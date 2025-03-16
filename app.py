import streamlit as st
import os
import time
from datetime import datetime
import logging
from modules.audio_processor import AudioProcessor
from modules.transcriber import Transcriber
from modules.summarizer import Summarizer
from modules.utils import setup_logging, save_results, clean_memory, get_timestamp
from config import SUMMARY_CHUNK_SIZE, SUMMARY_MODEL_PRIMARY, SUMMARY_MODEL_FALLBACK, RESULT_DIR, APP_NAME, SUMMARY_TIMEOUT, VERSION, DATA_DIR
import os

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title(f"{APP_NAME} v{VERSION}")
st.markdown("Bu uygulama, ses dosyalarını transkribe eder ve içeriği özetler.")

with st.sidebar:
    st.header("Ayarlar")
    st.markdown("Ses dosyanızı yükleyin ve işlem başlatın.")
    
    uploaded_file = st.file_uploader("Ses dosyası seçin", type=["m4a", "mp3", "wav"])
    
    if uploaded_file:
        start_process = st.button("İşlemi Başlat", type="primary")
    
    st.header("Son İşlemler")
    if os.path.exists(RESULT_DIR):
        files = [f for f in os.listdir(RESULT_DIR) if f.startswith("transcription_") or f.startswith("summary_")]
        dates = set([f.split("_", 1)[1].rsplit(".", 1)[0] for f in files])
        dates = sorted(list(dates), reverse=True)[:5]
        
        for date in dates:
            st.markdown(f"**{date.replace('_', ' ')}**")

if 'process_complete' not in st.session_state:
    st.session_state.process_complete = False

if 'transcription_result' not in st.session_state:
    st.session_state.transcription_result = ""

if 'summary_result' not in st.session_state:
    st.session_state.summary_result = ""

if 'transcription_file' not in st.session_state:
    st.session_state.transcription_file = ""

if 'summary_file' not in st.session_state:
    st.session_state.summary_file = ""

if uploaded_file and start_process:
    with st.spinner("Ses dosyası işleniyor..."):
        try:
            timestamp = get_timestamp()
            temp_path = os.path.join(DATA_DIR, f"upload_{timestamp}{os.path.splitext(uploaded_file.name)[1]}")
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            progress_bar = st.progress(0)
            status_text = st.empty()
                
            status_text.text("Ses dosyası dönüştürülüyor...")
            progress_bar.progress(10)
            audio_processor = AudioProcessor()
            wav_file = audio_processor.convert_to_wav(temp_path)
            
            status_text.text("Ses dosyası parçalara bölünüyor...")
            progress_bar.progress(20)
            segment_files = audio_processor.split_audio(wav_file)
            
            status_text.text("Transkripsiyon yapılıyor...")
            transcriber = Transcriber()
            
            total_segments = len(segment_files)
            for i, (segment_file, _) in enumerate(segment_files):
                sub_progress = 20 + (i / total_segments * 30)
                progress_bar.progress(int(sub_progress))
                status_text.text(f"Transkripsiyon: Segment {i+1}/{total_segments} işleniyor...")
            
            transcription = transcriber.transcribe_segments(segment_files)
            transcriber.cleanup()
            
            if not transcription or transcription.strip() == "":
                st.error("Transkripsiyon işlemi başarısız oldu. Ses dosyasını kontrol edin veya başka bir dosya deneyin.")
                st.stop()
            
            segment_paths = [path for path, _ in segment_files]
            audio_processor.cleanup_temp_files(segment_paths + [wav_file])
            
            status_text.text("Metin özetleniyor (bu işlem 10 dakikaya kadar sürebilir)...")
            progress_bar.progress(60)

            try:
                summarizer = Summarizer()
                
                status_text.text("Kapsamlı özet oluşturuluyor...")
                progress_bar.progress(70)
                
                summary = summarizer.create_summary_with_key_concepts(
                    text=transcription,
                    timeout=SUMMARY_TIMEOUT
                )
                
                if summary and len(summary) > 200:
                    status_text.text("Özet başarıyla oluşturuldu!")
                else:
                    status_text.text("Özet oluşturuldu ancak beklenenden kısa")
                
                progress_bar.progress(85)
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Özet oluşturma hatası: {error_msg}", exc_info=True)
                summary = "Özet oluşturma sırasında bir hata oluştu: " + error_msg
                
                quick_summary = summarizer.create_quick_summary(
                    text=transcription[:4000],
                    timeout=90
                )
                
                status_text.text("Kapsamlı özet oluşturuluyor... (2/3)")
                progress_bar.progress(75)
                
                try:
                    comprehensive_summary = summarizer.create_comprehensive_summary(
                        text=transcription,
                        quick_summary=quick_summary,
                        timeout=300
                    )
                    
                    if comprehensive_summary and len(comprehensive_summary) > 300:
                        summary = comprehensive_summary
                        status_text.text("Kapsamlı özet tamamlandı!")
                    else:
                        summary = quick_summary
                        status_text.text("Basit özet tamamlandı (kapsamlı özet oluşturulamadı)")
                except Exception as e:
                    logger.error(f"Kapsamlı özet hatası: {e}")
                    summary = quick_summary
                    status_text.text("Basit özet kullanılıyor (kapsamlı özet başarısız)")
                
                progress_bar.progress(85)
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Özet oluşturma hatası: {error_msg}", exc_info=True)
                
                try:
                    status_text.text("Acil durum özeti oluşturuluyor...")
                    summary = "Özet oluşturma sırasında bir hata oluştu. İşlenen metin:\n\n" + transcription[:500] + "..."
                except:
                    summary = "Özet oluşturulamadı. Teknik bir sorun oluştu."
            
            original_filename = os.path.splitext(os.path.basename(uploaded_file.name))[0]
            status_text.text("Sonuçlar kaydediliyor...")
            progress_bar.progress(90)
            transcription_file, summary_file = save_results(
                transcription, 
                summary, 
                original_filename
            )
            progress_bar.progress(100)
            status_text.text("İşlem tamamlandı!")
            time.sleep(1)
            
            st.session_state.transcription_result = transcription
            st.session_state.summary_result = summary
            st.session_state.transcription_file = transcription_file
            st.session_state.summary_file = summary_file
            st.session_state.process_complete = True
            
            clean_memory()
            
        except Exception as e:
            st.error(f"İşlem sırasında hata oluştu: {e}")
            logger.error(f"İşlem hatası: {e}", exc_info=True)
    
    st.rerun()

if st.session_state.process_complete:
    tabs = st.tabs(["Özet", "Transkripsiyon", "Dosyalar"])
    
    with tabs[0]:
        st.header("Özet")
        st.write(st.session_state.summary_result)
        
        if st.download_button(
            label="Özeti İndir",
            data=st.session_state.summary_result,
            file_name=f"summary_{get_timestamp()}.txt",
            mime="text/plain"
        ):
            st.success("Özet başarıyla indirildi!")
    
    with tabs[1]:
        st.header("Transkripsiyon")
        st.write(st.session_state.transcription_result)
        
        if st.download_button(
            label="Transkripsiyonu İndir",
            data=st.session_state.transcription_result,
            file_name=f"transcription_{get_timestamp()}.txt",
            mime="text/plain"
        ):
            st.success("Transkripsiyon başarıyla indirildi!")
    
    with tabs[2]:
        st.header("Kaydedilen Dosyalar")
        st.write(f"**Transkripsiyon:** {st.session_state.transcription_file}")
        st.write(f"**Özet:** {st.session_state.summary_file}")
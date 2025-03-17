import streamlit as st
import os
import time
from datetime import datetime
import logging
from modules.audio_processor import AudioProcessor
from modules.transcriber import Transcriber
from modules.summarizer import Summarizer
from modules.utils import setup_logging, save_results, clean_memory, get_timestamp
from modules.language import LANGUAGES, get_text
from config import SUMMARY_CHUNK_SIZE, SUMMARY_MODEL_PRIMARY, SUMMARY_MODEL_FALLBACK, RESULT_DIR, APP_NAME, VERSION, DATA_DIR
import os

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

setup_logging()
logger = logging.getLogger(__name__)

if 'language' not in st.session_state:
    st.session_state.language = "tr"

def get_lang_text(key):
    return get_text(st.session_state.language, key)

st.set_page_config(
    page_title="S2T2S",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #00ADB5; 
        font-size: 2.5rem;
        margin-bottom: 0;
    }

    .sub-header {
        text-align: center;
        color: #EEEEEE; 
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    .stButton>button {
        height: 3rem;
        width: 100%;
        font-weight: bold;
        background-color: #00ADB5; 
        color: #EEEEEE; 
        border: none;
    }

    .stButton>button[data-baseweb="button"].primary {
        background-color: #00ADB5; 
    }

    .stButton>button[data-baseweb="button"].secondary {
        background-color: #393E46; 
    }

    .info-box,
    .success-box,
    .error-box {
        background-color: #222831; 
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        color: #EEEEEE; 
    }

    .icon-text {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #00ADB5; 
    }

    .section-divider {
        margin: 2rem 0;
        border-bottom: 1px solid #00ADB5; 
    }

    .file-info {
        font-size: 0.9rem;
        color: #EEEEEE; 
        margin-top: 0.5rem;
    }

</style>
""", unsafe_allow_html=True)

st.markdown(f'<h1 class="main-header">{get_lang_text("app_title")}</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">{get_lang_text("app_subtitle")} v{VERSION}</p>', unsafe_allow_html=True)

if 'process_running' not in st.session_state:
    st.session_state.process_running = False
if 'process_complete' not in st.session_state:
    st.session_state.process_complete = False
if 'stop_requested' not in st.session_state:
    st.session_state.stop_requested = False
if 'transcription_result' not in st.session_state:
    st.session_state.transcription_result = ""
if 'summary_result' not in st.session_state:
    st.session_state.summary_result = ""
if 'transcription_file' not in st.session_state:
    st.session_state.transcription_file = ""
if 'summary_file' not in st.session_state:
    st.session_state.summary_file = ""

def stop_processing():
    st.session_state.stop_requested = True
    st.session_state.process_running = False
    logger.info("İşlemi durdurma isteği alındı")

with st.sidebar:
    st.markdown("<div style='text-align: center;'><img src='https://img.icons8.com/?size=100&id=1RueIplXPGd2&format=png&color=000000' width='100'></div>", unsafe_allow_html=True)
    
    lang_options = {
        "tr": "Türkçe", 
        "en": "English"
    }
    
    selected_lang = st.selectbox(
        get_lang_text("select_language"),
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(st.session_state.language)
    )
    
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()
    
    st.header(get_lang_text("control_panel"))
    
    with st.expander(f"📋 {get_lang_text('instructions_title')}", expanded=True):
        for instruction in get_lang_text("instructions"):
            st.markdown(instruction)
    
    uploaded_file = st.file_uploader(get_lang_text("select_audio"), type=["m4a", "mp3", "wav"])
    
    if uploaded_file:
        file_details = f"""
        <div class="file-info">
            <strong>{get_lang_text("file_name")}:</strong> {uploaded_file.name}<br>
            <strong>{get_lang_text("size")}:</strong> {uploaded_file.size/1024:.1f} KB
        </div>
        """
        st.markdown(file_details, unsafe_allow_html=True)
    
    # Özet seçenekleri bölümünü ekle
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    st.subheader(get_lang_text("summary_options"))
    
    summary_mode = st.radio(
        get_lang_text("select_summary_mode"),
        options=["basic", "enhanced"],
        format_func=lambda x: get_lang_text(f"{x}_mode"),
        index=0,
        help=get_lang_text("summary_mode_help")
    )
    
    # Gelişmiş mod seçilirse bilgi mesajı göster
    if summary_mode == "enhanced":
        st.info(get_lang_text("enhanced_mode_info"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        if uploaded_file and not st.session_state.process_running:
            start_button = st.button(get_lang_text("start_button"), type="primary", key="start_button", 
                              disabled=st.session_state.process_running)
            if start_button:
                st.session_state.process_running = True
                st.session_state.stop_requested = False
                st.session_state.process_complete = False
    
    with col2:
        if st.session_state.process_running:
            stop_button = st.button(get_lang_text("stop_button"), on_click=stop_processing, key="stop_button", 
                             type="secondary")
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    st.subheader(get_lang_text("recent_processes"))
    if os.path.exists(RESULT_DIR):
        files = [f for f in os.listdir(RESULT_DIR) if f.startswith("transcription_") or f.startswith("summary_")]
        dates = set([f.split("_", 1)[1].rsplit(".", 1)[0] for f in files])
        dates = sorted(list(dates), reverse=True)[:5]
        
        if dates:
            for date in dates:
                with st.expander(f"📄 {date.replace('_', '/')}"):
                    trans_file = os.path.join(RESULT_DIR, f"transcription_{date}.txt")
                    summ_file = os.path.join(RESULT_DIR, f"summary_{date}.txt")
                    
                    if os.path.exists(trans_file):
                        st.download_button(
                            label=get_lang_text("download_transcription"),
                            data=open(trans_file, "r", encoding="utf-8").read(),
                            file_name=f"transcription_{date}.txt",
                            mime="text/plain",
                            key=f"dl_trans_{date}"
                        )
                    
                    if os.path.exists(summ_file):
                        st.download_button(
                            label=get_lang_text("download_summary"),
                            data=open(summ_file, "r", encoding="utf-8").read(),
                            file_name=f"summary_{date}.txt",
                            mime="text/plain",
                            key=f"dl_summ_{date}"
                        )
        else:
            st.info(get_lang_text("no_processes"))

if uploaded_file and st.session_state.process_running and not st.session_state.process_complete:
    with st.status(get_lang_text("processing"), expanded=True) as status:
        try:
            timestamp = get_timestamp()
            temp_path = os.path.join(DATA_DIR, f"upload_{timestamp}{os.path.splitext(uploaded_file.name)[1]}")
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            if st.session_state.stop_requested:
                raise Exception(get_lang_text("process_stopped"))
                
            status_text.markdown(f"**{get_lang_text('audio_converting')}**")
            progress_bar.progress(10)
            audio_processor = AudioProcessor()
            wav_file = audio_processor.convert_to_wav(temp_path)
            
            if st.session_state.stop_requested:
                raise Exception(get_lang_text("process_stopped"))
                
            status_text.markdown(f"**{get_lang_text('audio_splitting')}**")
            progress_bar.progress(20)
            segment_files = audio_processor.split_audio(wav_file)
            
            if st.session_state.stop_requested:
                raise Exception(get_lang_text("process_stopped"))
                
            status_text.markdown(f"**{get_lang_text('transcribing')}**")
            transcriber = Transcriber()
            
            total_segments = len(segment_files)
            for i, (segment_file, _) in enumerate(segment_files):
                if st.session_state.stop_requested:
                    raise Exception(get_lang_text("process_stopped"))
                    
                sub_progress = 20 + (i / total_segments * 30)
                progress_bar.progress(int(sub_progress))
                status_text.markdown(f"**{get_lang_text('transcribing_segment').format(i+1, total_segments)}**")
            
            transcription = transcriber.transcribe_segments(segment_files)
            transcriber.cleanup()
            
            if not transcription or transcription.strip() == "":
                st.error(get_lang_text("transcription_error"))
                status.update(label=get_lang_text("process_failed"), state="error")
                st.session_state.process_running = False
                st.stop()
            
            segment_paths = [path for path, _ in segment_files]
            audio_processor.cleanup_temp_files(segment_paths + [wav_file])
            
            if st.session_state.stop_requested:
                raise Exception(get_lang_text("process_stopped"))
                
            progress_bar.progress(60)

            try:
                summarizer = Summarizer()
                
                if st.session_state.stop_requested:
                    raise Exception(get_lang_text("process_stopped"))
                
                
                if summary_mode == "enhanced":
                    status_text.markdown(f"**{get_lang_text('enhanced_summarizing')}**")
                else:
                    status_text.markdown(f"**{get_lang_text('basic_summarizing')}**")
                
                summary = summarizer.summarize_text(
                    transcription=transcription,
                    mode=summary_mode,
                )
                
                if summary and len(summary) > 200:
                    status_text.markdown(f"**{get_lang_text('summary_success')}**")
                else:
                    status_text.markdown(f"**{get_lang_text('summary_short')}**")
                
                progress_bar.progress(85)
                
            except Exception as e:
                if st.session_state.stop_requested:
                    raise Exception(get_lang_text("process_stopped"))
                    
                error_msg = str(e)
                logger.error(f"Özet oluşturma hatası: {error_msg}", exc_info=True)
                
                status_text.markdown(f"**{get_lang_text('fallback_model')}**")
                
                try:
                    quick_summary = summarizer.create_quick_summary(
                        text=transcription[:4000],
                        timeout=90
                    )
                    
                    status_text.markdown(f"**{get_lang_text('summarizing_model').format(SUMMARY_MODEL_FALLBACK)}**")
                    progress_bar.progress(75)
                    
                    comprehensive_summary = summarizer.create_comprehensive_summary(
                        text=transcription,
                        quick_summary=quick_summary,
                        timeout=300
                    )
                    
                    if comprehensive_summary and len(comprehensive_summary) > 300:
                        summary = comprehensive_summary
                        status_text.markdown(f"**{get_lang_text('comprehensive_summary')}**")
                    else:
                        summary = quick_summary
                        status_text.markdown(f"**{get_lang_text('simple_summary')}**")
                except Exception as e:
                    logger.error(f"Kapsamlı özet hatası: {e}")
                    summary = f"{get_lang_text('summary_error')} " + str(e)
                    status_text.markdown(f"**{get_lang_text('summary_error')}**")
                
                progress_bar.progress(85)
            
            if st.session_state.stop_requested:
                raise Exception(get_lang_text("process_stopped"))
                
            original_filename = os.path.splitext(os.path.basename(uploaded_file.name))[0]
            status_text.markdown(f"**{get_lang_text('saving_results')}**")
            progress_bar.progress(90)
            
            transcription_file, summary_file = save_results(
                transcription, 
                summary, 
                original_filename
            )
            
            progress_bar.progress(100)
            status_text.markdown(f"**{get_lang_text('process_completed')}**")
            status.update(label=get_lang_text("process_completed"), state="complete")
            time.sleep(1)
            
            st.session_state.transcription_result = transcription
            st.session_state.summary_result = summary
            st.session_state.transcription_file = transcription_file
            st.session_state.summary_file = summary_file
            st.session_state.process_complete = True
            st.session_state.process_running = False
            
            clean_memory()
            
        except Exception as e:
            if get_lang_text("process_stopped") in str(e):
                st.warning(get_lang_text("process_stopped"))
                status.update(label=get_lang_text("process_stopped"), state="error")
            else:
                st.error(get_lang_text("process_error").format(e))
                status.update(label=get_lang_text("process_failed"), state="error")
                logger.error(f"İşlem hatası: {e}", exc_info=True)
            
            st.session_state.process_running = False
    
    st.rerun()

if st.session_state.process_complete:
    st.success(get_lang_text("process_completed_message"), icon="✅")
    
    tabs = st.tabs([
        get_lang_text("summary_tab"), 
        get_lang_text("transcription_tab"), 
        get_lang_text("files_tab")
    ])
    
    with tabs[0]:
        st.header(get_lang_text("summary_header"))
        st.markdown(f"""
        <div class="info-box">
        {get_lang_text("summary_info")}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.write(st.session_state.summary_result)
        st.markdown("---")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.download_button(
                label=get_lang_text("download_summary_button"),
                data=st.session_state.summary_result,
                file_name=f"summary_{get_timestamp()}.txt",
                mime="text/plain"
            ):
                st.success(get_lang_text("summary_downloaded"))
    
    with tabs[1]:
        st.header(get_lang_text("transcription_header"))
        st.markdown(f"""
        <div class="info-box">
        {get_lang_text("transcription_info")}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.write(st.session_state.transcription_result)
        st.markdown("---")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.download_button(
                label=get_lang_text("download_transcription_button"),
                data=st.session_state.transcription_result,
                file_name=f"transcription_{get_timestamp()}.txt",
                mime="text/plain"
            ):
                st.success(get_lang_text("transcription_downloaded"))
    
    with tabs[2]:
        st.header(get_lang_text("saved_files_header"))
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="success-box">
            <strong>{get_lang_text("transcription_file")}:</strong><br>
            {os.path.basename(st.session_state.transcription_file)}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="success-box">
            <strong>{get_lang_text("summary_file")}:</strong><br>
            {os.path.basename(st.session_state.summary_file)}
            </div>
            """, unsafe_allow_html=True)
            
        st.info(get_lang_text("files_stored_info").format(RESULT_DIR))
from pydub import AudioSegment
import os
from typing import List, Tuple
import logging
from config import TEMP_DIR, SEGMENT_DURATION_MS

logger = logging.getLogger(__name__)

class AudioProcessor:
    @staticmethod
    def convert_to_wav(input_file: str) -> str:
        try:
            base_filename = os.path.splitext(os.path.basename(input_file))[0]
            output_wav_file = os.path.join(TEMP_DIR, f"{base_filename}.wav")
            
            audio = AudioSegment.from_file(input_file)
            audio.export(output_wav_file, format="wav")
            logger.info(f"Dosya dönüştürüldü: {output_wav_file}")
            
            return output_wav_file
        except Exception as e:
            logger.error(f"Ses dönüştürme hatası: {e}")
            raise

    @staticmethod
    def split_audio(wav_file: str) -> List[Tuple[str, int]]:
        try:
            audio = AudioSegment.from_wav(wav_file)
            segments = [audio[i:i+SEGMENT_DURATION_MS] for i in range(0, len(audio), SEGMENT_DURATION_MS)]
            
            segment_files = []
            for idx, segment in enumerate(segments):
                segment_path = os.path.join(TEMP_DIR, f"segment_{idx}.wav")
                segment.export(segment_path, format="wav")
                segment_files.append((segment_path, idx))
            
            logger.info(f"Ses dosyası {len(segments)} parçaya bölündü")
            return segment_files
        except Exception as e:
            logger.error(f"Ses bölme hatası: {e}")
            raise

    @staticmethod
    def cleanup_temp_files(file_list: List[str]) -> None:
        for file in file_list:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception as e:
                logger.warning(f"{file} silinirken hata: {e}")

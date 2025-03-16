import torch
from transformers import pipeline
import logging
from typing import List, Tuple
import os
from config import WHISPER_MODEL

logger = logging.getLogger(__name__)

class Transcriber:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Cihaz: {self.device}")
        
        if self.device == "cuda":
            torch.backends.cudnn.benchmark = True
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"Toplam GPU belleği: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
            
        self.model = None
        
    def load_model(self) -> None:
        """Whisper modelini yükler."""
        try:
            logger.info(f"Whisper modeli yükleniyor: {WHISPER_MODEL}")
            self.model = pipeline(
                "automatic-speech-recognition", 
                model=WHISPER_MODEL, 
                device=self.device,
                torch_dtype=torch.float16
            )
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}")
            raise
            
    def transcribe_segments(self, segment_files: List[Tuple[str, int]]) -> str:
        """Ses segmentlerini transkribe eder ve birleştirir."""
        if not self.model:
            self.load_model()
            
        full_transcription = ""
        
        for segment_path, idx in segment_files:
            logger.info(f"Segment işleniyor {idx+1}/{len(segment_files)}...")
            
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            try:
                transcription = self.model(
                    inputs=segment_path, 
                    return_timestamps=True,
                    batch_size=16,
                    chunk_length_s=30
                )["text"]
                
                full_transcription += transcription + " "
                logger.info(f"Segment {idx+1} transkripsiyon tamamlandı. Uzunluk: {len(transcription)} karakter")
            except Exception as e:
                logger.error(f"Segment {idx+1} transkripsiyon hatası: {e}")
                continue
        
        if not full_transcription.strip():
            logger.error("Transkripsiyon boş! Ses dosyası işlenemedi veya içerik algılanamadı.")
            return "Transkripsiyon işlemi başarısız oldu. Lütfen ses dosyasını kontrol edin."
        
        return full_transcription
    
    def cleanup(self) -> None:
        """Model belleğini temizler."""
        del self.model
        self.model = None
        
        if self.device == "cuda":
            torch.cuda.empty_cache()
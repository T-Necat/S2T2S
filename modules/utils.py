import os
from datetime import datetime
import logging
import gc
import re
import subprocess
import time
from typing import Tuple
from config import RESULT_DIR

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(RESULT_DIR, f"log_{datetime.now().strftime('%Y%m%d')}.txt"))
        ]
    )
    logging.getLogger("transformers").setLevel(logging.ERROR)
    logging.getLogger("torch").setLevel(logging.ERROR)

def get_timestamp() -> str:
    """Dosya isimlendirmesi için zaman damgası oluşturur."""
    return datetime.now().strftime("%H_%M_%d_%m_%Y")

def save_results(transcription: str, summary: str, file_base_name: str = None) -> Tuple[str, str]:
    """
    Args:
        transcription: Kaydedilecek transkripsiyon metni
        summary: Kaydedilecek özet metni
        file_base_name: Orijinal dosya adı (opsiyonel)
        
    Returns:
        Kaydedilen dosya yolları (transkripsiyon, özet)
    """
    timestamp = get_timestamp()
    
    if file_base_name:
        clean_name = re.sub(r'[^\w\-_]', '_', file_base_name)
        base_name = f"{clean_name}_{timestamp}"
    else:
        base_name = timestamp
    
    transcription_file = os.path.join(RESULT_DIR, f"transcription_{base_name}.txt")
    summary_file = os.path.join(RESULT_DIR, f"summary_{base_name}.txt")
    
    with open(transcription_file, "w", encoding="utf-8") as f:
        f.write(transcription)
    
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary)
    
    logger.info(f"Transkripsiyon kaydedildi: {transcription_file}")
    logger.info(f"Özet kaydedildi: {summary_file}")
    
    return transcription_file, summary_file


def kill_stalled_processes(process_name="ollama"):
    try:
        if os.name == 'nt':
            os.system(f'taskkill /f /im {process_name}.exe')
        else:
            os.system(f'pkill -f {process_name}')
        logger.info(f"Olası askıda kalmış {process_name} süreçleri temizlendi")
    except Exception as e:
        logger.warning(f"Süreç temizleme başarısız: {e}")

def ensure_ollama_running():
    try:
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True, 
            timeout=5,
            check=False
        )
        
        if result.returncode != 0:
            logger.warning("Ollama servisi çalışmıyor olabilir!")
            return False
        return True
    except Exception as e:
        logger.error(f"Ollama durum kontrolü başarısız: {e}")
        return False

def monitor_process_with_timeout(func, args=None, kwargs=None, timeout=180):
    import threading
    
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    
    result = [None]
    exception = [None]
    is_finished = [False]
    
    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
        finally:
            is_finished[0] = True
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    
    start_time = time.time()
    while not is_finished[0] and (time.time() - start_time) < timeout:
        time.sleep(0.5)  
        
        elapsed = time.time() - start_time
        progress_percent = min(95, 60 + (elapsed / timeout * 35))
        
        yield {
            "elapsed": elapsed,
            "progress": progress_percent,
            "status": "running"
        }
    
    if not is_finished[0]:
        return {
            "status": "timeout",
            "elapsed": timeout,
            "result": None,
            "exception": TimeoutError(f"İşlem {timeout} saniye içinde tamamlanmadı")
        }
    
    if exception[0]:
        return {
            "status": "error",
            "elapsed": time.time() - start_time,
            "result": None, 
            "exception": exception[0]
        }
    
    return {
        "status": "success",
        "elapsed": time.time() - start_time,
        "result": result[0],
        "exception": None
    }

def clean_memory():
    gc.collect()
    logger.info("Bellek temizlendi")

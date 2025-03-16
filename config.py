import os
import locale
import sys

APP_NAME = "Sound-Text Conversion and Summary System"
VERSION = "1.3"

SUMMARY_TIMEOUT = 600  
SUMMARY_FALLBACK_TIMEOUT = 180 

SYSTEM_ENCODING = locale.getpreferredencoding() 
CONSOLE_ENCODING = sys.stdout.encoding 

SUBPROCESS_ENCODING = "utf-8"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_DIR = os.path.join(DATA_DIR, "temp")
RESULT_DIR = os.path.join(DATA_DIR, "results")

WHISPER_MODEL = "openai/whisper-large-v3-turbo"
SUMMARY_MODEL_PRIMARY = "deepseek-r1:32b"
SUMMARY_MODEL_FALLBACK = "llama3:8b"  

MAX_INPUT_TOKENS = 4000  
MAX_META_SUMMARY_TOKENS = 8000  

SEGMENT_DURATION_MS = 300 * 1000  
SUMMARY_CHUNK_SIZE = 3000

DEVICE_MAP = "auto"

for directory in [DATA_DIR, TEMP_DIR, RESULT_DIR]:
    os.makedirs(directory, exist_ok=True)
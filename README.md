# Sound-Text Conversion and Summary System
🐍 Python | 🤖 Whisper | 🦙 Ollama | 🎵 Audio Processing

This project is a Python application that converts sound files to text and then summarizes the text. It creates intelligent summaries from audio files using OpenAI Whisper and Ollama.

## 🚀 Features
- Converting M4A format audio files to WAV format
- Automatically dividing large audio files into segments
- Fast transcription with GPU support
- High-accuracy speech recognition with Whisper large-v3-turbo model
- Text summarization with Ollama
- Automatic result file creation

## 📋 Requirements
- Python 3.8+
- FFmpeg
- CUDA compatible GPU (optional)
- Ollama

The project includes a `requirements.txt` file with all necessary Python dependencies. You can install them using pip.

## 🛠️ Installation
1. Clone the project:
```bash
git clone [repo-url]
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg:
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt-get install ffmpeg`
- Windows: [FFmpeg website](https://ffmpeg.org/download.html)

4. Install and start Ollama:
```bash
# For Ollama installation: https://ollama.ai/
ollama pull deepseek-r1:32b
```

## 📝 Usage
1. Place your audio file in the `/source` folder
2. Run the script:
```bash
python main.py
```
3. Results will be created in the `/source/resoult_text` folder:
- `transcription_[timestamp].txt`: Full transcription
- `summary_[timestamp].txt`: Summarized text

## 🗂️ Project Structure
```
my_school_project/
│
├── main.py 
├── requirements.txt
├── source/ 
│ ├── input_audio.m4a 
│ └── resoult_text/ 
│ ├── transcription_*.txt
│ └── summary_*.txt
└── README.md
```

## ⚠️ Notes
- GPU will be automatically detected and used when available
- You can change the Ollama model according to your computer power or model preference
- Large audio files are automatically divided into 5-minute segments
- Contains automatic cleaning mechanisms for memory management
- When running on Windows, you may need to set the `KMP_DUPLICATE_LIB_OK=TRUE` environment variable

## 🔍 Troubleshooting
- Try reducing segment size for GPU memory errors
- Check installation for FFmpeg errors
- Make sure the service is running for Ollama connection errors

# Sound-Text Conversion and Summary System

🐍 Python | 🤖 Whisper | 🦙 Ollama | 🎵 Audio Processing

![Version](https://img.shields.io/badge/version-1.2.0-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

The Sound-Text Conversion and Summary System is a comprehensive solution that converts audio recordings to text and summarizes the content using artificial intelligence. Easily upload audio files in various formats, obtain accurate and detailed transcriptions, and quickly grasp the essential points of the content through AI-powered intelligent summarization.

## 📋 Features

- **Multi-Format Support**: Process audio files in M4A, MP3, and WAV formats
- **High-Accuracy Transcription**: Advanced speech recognition using the OpenAI Whisper large-v3-turbo model
- **Intelligent Summarization System**: Two-tier summarization (deepseek-r1:32b and llama3:8b)
- **Automatic Language Detection**: Detects the language of the transcription for appropriate summarization (currently supports English and Turkish only)
- **Concept Extraction**: Automatically extracts important terms and concepts from the text
- **User-Friendly Interface**: Intuitive web interface designed with Streamlit
- **Progress Tracking**: Real-time process status and progress indicators
- **Result Management**: Automatic saving of all transcriptions and summaries
- **Long Audio File Support**: Automatic segmentation of large audio files

## 📋 Requirements

- Python 3.8 or higher
- FFmpeg
- CUDA compatible GPU (optional, but recommended)
- Ollama

The project comes with a `requirements.txt` file containing all necessary Python dependencies. You can install them using pip.

## 🛠️ Installation

1. Clone the project:
```bash
git clone [repo-url]
cd audio-transcription-summary
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg:
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt-get install ffmpeg`
- Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH

4. Install Ollama and load required models:
```bash
# For Ollama installation: https://ollama.ai/
ollama pull deepseek-r1:32b
ollama pull llama3:8b
```

## 📝 Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. In the web interface that automatically opens in your browser:
   - Upload your audio file (M4A, MP3, or WAV) from the left menu
   - Click the "Start Process" button
   - Monitor progress using the progress bar during processing
   - View results in the "Summary," "Transcription," and "Files" tabs when completed

3. Export results:
   - Save results as text files using the "Download" button in each tab
   - All results are also automatically saved to the `data/results` folder

## 🗂️ Project Structure

```
audio_transcription_app/
│
├── app.py                  # Main Streamlit application
├── config.py               # Configuration settings
├── requirements.txt        # Dependencies
│
├── modules/
│   ├── audio_processor.py  # Audio conversion and segmentation
│   ├── transcriber.py      # Speech-to-text conversion (Whisper)
│   ├── summarizer.py       # Text summarization (Ollama)
│   └── utils.py            # Helper functions
│
└── data/                   # Storage for processed files
    ├── temp/               # Temporary files
    └── results/            # Result files
```

## ⚠️ Important Notes

- GPU will be automatically detected and used when available
- You can change the Ollama model according to your computer power or model preference
- Large audio files are automatically divided into 5-minute segments
- Contains automatic cleaning mechanisms for memory management
- When running on Windows, you may need to set the `KMP_DUPLICATE_LIB_OK=TRUE` environment variable
- Language detection currently only supports English and Turkish

## 🔍 Troubleshooting

- Try reducing segment size for GPU memory errors (lower the `SEGMENT_DURATION_MS` value in the `config.py` file)
- Check installation for FFmpeg errors
- Ensure the Ollama service is running for connection errors (verify with the `ollama list` command)
- If you receive insufficient summaries, increase the `SUMMARY_TIMEOUT` value in the `config.py` file

## 🔄 Update Notes (v1.2.0)

- Transition from command-line interface to Streamlit web interface
- Added automatic language detection feature (English and Turkish)
- Implemented two-tier summarization system (primary and fallback models)
- Improved memory management and error handling mechanisms
- Added real-time progress tracking during processing
- Added automatic extraction of important concepts
- Provided option to download results directly from the application

## 🔒 System Requirements

- **Minimum**: 8GB RAM, 4-core CPU, 10GB disk space
- **Recommended**: 16GB RAM, 8-core CPU, CUDA compatible GPU (4GB+ VRAM), 20GB disk space

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

We welcome your contributions. Please feel free to fork and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

---

Last Updated: March 2025
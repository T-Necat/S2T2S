# Sound-Text Conversion and Summary System

🐍 Python | 🤖 Whisper | 🦙 Ollama | 🎵 Audio Processing | 🐳 Docker

![Version](https://img.shields.io/badge/version-1.4.2-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

The Sound-Text Conversion and Summary System (S2T2S) is a comprehensive solution that converts audio recordings to text and summarizes the content using artificial intelligence. Easily upload audio files in various formats, obtain accurate and detailed transcriptions, and quickly grasp the essential points of the content through AI-powered intelligent summarization.

![S2T2S DEMO ](S2T2S_DEMO.gif)

## 📋 Features

- **Multi-Format Support**: Process audio files in M4A, MP3, and WAV formats
- **High-Accuracy Transcription**: Advanced speech recognition using the OpenAI Whisper large-v3-turbo model
- **Enhanced Summarization System**: Two-tier summarization with basic and enhanced modes
- **Multiple Language Support**: Automatic language detection for English and Turkish with appropriate summarization
- **Concept Extraction & Analysis**: Automatically extracts important terms and concepts with relationship analysis
- **Domain-Specific Analysis**: Detects content domain and provides specialized insights
- **Interactive Progress Tracking**: Real-time process status with detailed progress indicators
- **Comprehensive Result Management**: Automatic saving and organization of all results
- **Enhanced User Interface**: Streamlined Streamlit interface with improved accessibility
- **Model Flexibility**: Use any Ollama-compatible model for summarization by adjusting configuration settings
- **Docker Integration**: Easy deployment using pre-built Docker images

## Enhanced Summarization System

S2T2S offers two summarization modes to meet different needs:

- **Basic Mode**: Provides quick, concise summaries of audio content suitable for general use with minimal computational requirements.
- **Enhanced Mode**: Delivers comprehensive, high-quality analysis with concept extraction, relationship mapping, and domain-specific insights using a sophisticated multi-model pipeline.

## 🐳 Docker Integration

The system is available as a Docker image with optimized smaller models for easier deployment:

```bash
# Pull the image
docker pull topraknecat/s2t2s_v1

# Run the container
docker run -p 8501:8501 topraknecat/s2t2s_v1

# With persistent data storage
docker run -p 8501:8501 -v $(pwd)/data:/app/data topraknecat/s2t2s_v1

# With GPU support
docker run --gpus all -p 8501:8501 topraknecat/s2t2s_v1
```

Access the application in your browser at `http://localhost:8501`.

## 📋 Requirements

- Python 3.8 or higher
- FFmpeg
- CUDA compatible GPU (optional, but recommended)
- Ollama

The project comes with a `requirements.txt` file containing all necessary Python dependencies. You can install them using pip.

## 🛠️ Installation

1. Clone the project:
```bash
git clone https://github.com/yourusername/S2T2S.git
cd S2T2S
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

Note: While the default configuration uses deepseek-r1:32b and llama3:8b, you can modify the `config.py` file to use any model available in Ollama. This flexibility allows you to leverage different models based on your specific needs or hardware capabilities.

## 📝 Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. In the web interface that opens in your browser:
   - Select your preferred language (English or Turkish)
   - Upload your audio file (M4A, MP3, or WAV) from the left menu
   - Choose between basic or enhanced summary mode
   - Click the "Start Process" button
   - Monitor progress with detailed status updates
   - View results in the "Summary," "Transcription," and "Files" tabs when completed

3. Export results:
   - Save results as text files using the "Download" button in each tab
   - All results are also automatically saved to the `data/results` folder

## 🗂️ Project Structure

```
S2T2S/
│
├── app.py                         # Main Streamlit application
├── config.py                      # Configuration settings
├── requirements.txt               # Dependencies
│
├── modules/
│   ├── audio_processor.py         # Audio conversion and segmentation
│   ├── transcriber.py             # Speech-to-text conversion (Whisper)
│   ├── summarizer.py              # Text summarization (Ollama)
│   ├── language.py                # Multi-language support
│   └── utils.py                   # Helper functions
│
└── data/                          # Storage for processed files
    ├── temp/                      # Temporary files
    └── results/                   # Result files
```

## ⚠️ Important Notes

- GPU will be automatically detected and used when available
- You can select between basic and enhanced summary modes based on your needs
- Large audio files are automatically divided into 5-minute segments
- The system contains automatic cleaning mechanisms for memory management
- When running on Windows, you may need to set the `KMP_DUPLICATE_LIB_OK=TRUE` environment variable
- Language detection currently supports English and Turkish
- You can use any Ollama-compatible model by modifying the model names in `config.py`
- The Docker image is optimized to work with smaller models for better performance on standard hardware

## 🔍 Troubleshooting

- For GPU memory errors, try reducing segment size in `config.py` (lower the `SEGMENT_DURATION_MS` value)
- If you encounter FFmpeg errors, verify your installation
- For connection errors, ensure the Ollama service is running (verify with `ollama list`)
- If summaries are insufficient, you can increase timeout values in `config.py`
- If enhanced summaries fail, the system will automatically fall back to basic mode
- If you want to use different models, ensure they are first downloaded with `ollama pull [model-name]`
- For Docker-related issues, ensure you have the latest Docker version installed

## 🔄 Update Notes (v1.4.2)

- **Docker Support**: Added Docker image for easy deployment and usage
- **New Summarization Modes**: Added options for basic and enhanced summarization
- **Improved Summary Quality**: Enhanced summarization now includes:
  - Section-by-section enhancement with relevant content analysis
  - Domain detection and specialized content analysis
  - Concept relationship mapping and definition
  - Quality evaluation and automatic improvement of weak sections
- **Enhanced Language Support**: Improved language detection and consistency checks
  - Better handling of mixed-language content
  - Improved Turkish language support with specialized processing
- **Optimized Performance**: More efficient processing with fallback mechanisms
  - Better error handling with graceful degradation
  - Improved timeout management for summarization processes
- **User Interface Enhancements**: 
  - Added summary mode selection in UI
  - More detailed progress updates during processing
  - Better organization of results
- **Model Flexibility**: Added ability to easily configure and use any Ollama-compatible model

## 🔒 System Requirements

- **Minimum**: 8GB RAM, 4-core CPU, 10GB disk space
- **Recommended**: 16GB RAM, 8-core CPU, CUDA compatible GPU (4GB+ VRAM), 20GB disk space
- **Enhanced Summary Mode**: 16GB+ RAM, dedicated GPU with 8GB+ VRAM recommended
- **Docker Usage**: Docker Engine 19.03+, 4GB RAM minimum, 5GB free disk space

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

We welcome your contributions. Please feel free to fork and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

---

Last Updated: March 2025

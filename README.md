# Sound-Text Conversion and Summary System

🐍 Python | 🤖 Whisper | 🦙 Ollama | 🎵 Audio Processing

![Version](https://img.shields.io/badge/version-1.4.0-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

The Sound-Text Conversion and Summary System (S2T2S) is a comprehensive solution that converts audio recordings to text and summarizes the content using artificial intelligence. Easily upload audio files in various formats, obtain accurate and detailed transcriptions, and quickly grasp the essential points of the content through AI-powered intelligent summarization.

[S2T2S DEMO ](https://github.com/T-Necat/S2T2S/blob/main/S2T2S_DEMO.gif)

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

## Enhanced Summarization System

The enhanced summarization mode represents a significant advancement over basic summarization, delivering comprehensive, high-quality summaries through a sophisticated multi-stage process:

1. **Multi-Model Pipeline Processing**: 
   - Primary model (deepseek-r1:32b) creates an initial detailed summary
   - Secondary model (llama3:8b) performs specialized enhancement tasks
   - Iterative refinement with both models for optimal quality

2. **Advanced Content Analysis**:
   - Automatic key concept extraction and terminology identification
   - Relationship mapping between concepts with detailed definitions
   - Domain recognition and specialized content treatment
   - Quality evaluation with targeted improvements for weak sections

3. **Practical Advantages**:
   - Transforms hours of audio content into concise, structured summaries in minutes
   - Preserves technical accuracy while improving readability
   - Maintains contextual relationships between concepts
   - Produces summaries with professional organization and academic quality

The enhanced mode is particularly valuable for educational content, technical discussions, and professional presentations where comprehensive understanding of complex relationships between concepts is essential. This sophisticated system effectively transforms what would typically be hours of reading and analysis into a streamlined, efficient process that delivers the essential content in a fraction of the time.

While the basic mode offers quick summaries suitable for general content, the enhanced mode provides a level of depth and analysis that approaches expert-level understanding, making it ideal for professional and academic applications where thorough comprehension is critical.

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

## 🔍 Troubleshooting

- For GPU memory errors, try reducing segment size in `config.py` (lower the `SEGMENT_DURATION_MS` value)
- If you encounter FFmpeg errors, verify your installation
- For connection errors, ensure the Ollama service is running (verify with `ollama list`)
- If summaries are insufficient, you can increase timeout values in `config.py`
- If enhanced summaries fail, the system will automatically fall back to basic mode
- If you want to use different models, ensure they are first downloaded with `ollama pull [model-name]`

## 🔄 Update Notes (v1.4.0)

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

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

We welcome your contributions. Please feel free to fork and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

---

Last Updated: March 2025


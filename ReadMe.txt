<div align="center">

# Karbouji Crystal 2026  
**Open-source Levantine Arabic Text-to-Speech & Speech-to-Text Engine**

</div>

Karbouji is an open-source voice processing toolkit focused on high-quality **Levantine Arabic** (Shami dialect) synthesis and recognition, built on top of modern TTS and ASR models.

### Key Features

- High-quality **Text-to-Speech** (TTS) for Levantine Arabic using Facebook MMS-TTS (ara)  
- Optional English TTS support (MMS-TTS eng)  
- Automatic language detection (Arabic ↔ English)  
- Intelligent chunking & concatenation for long texts  
- Voice speed adjustment with natural female/male variants optimized for Levantine pronunciation  
- **Noise reduction & enhancement** using DeepFilterNet3  
- **Speech-to-Text** (STT) with Whisper small – good performance on Levantine dialect  
- Clean, modern desktop GUI (Tkinter) with bilingual (Arabic/English) interface  
- Real-time playback with instant stop functionality  
- Export synthesized speech as WAV files  
- Comprehensive logging & session reports  
- Optional advanced source separation via Demucs (vocals/drums/bass/etc.)

### Current Status (January 2026)

| Feature                          | Status              | Notes                              |
|----------------------------------|---------------------|------------------------------------|
| Levantine Arabic TTS             | ✅ Ready            | Primary model – highest quality    |
| English TTS                      | ✅ Optional         | Requires model download            |
| Whisper STT (Levantine support)  | ✅ With installation| openai-whisper required            |
| DeepFilterNet noise reduction    | ✅                  | Great studio-like cleanup          |
| GUI (bilingual)                  | ✅                  | Dark theme, responsive layout      |
| Demucs source separation         | 🟡 Optional         | Needs separate installation        |

### Quick Start

```bash
# boot Starter
bootStarter.py

# Recommended – run the GUI
python Voice_processor.GUI.py
test_coqui.py

# Basic backend test
python Voice_processor.py

# Reporter
logger.py

Requirementsbash

Python 3.9–3.11
pip install torch torchaudio transformers soundfile sounddevice numpy scipy pillow
# Optional / recommended:
pip install openai-whisper          # for speech recognition
pip install demucs                  # for advanced source separation
pip install df                      # for DeepFilterNet enhancement

Models (download manually and place in models/ folder):facebook/mms-tts-ara
facebook/mms-tts-eng (optional)

Project GoalsProvide the best possible open-source Levantine Arabic voice synthesis currently available
Support researchers, content creators, accessibility applications, and dialect preservation efforts
Maintain clean code structure for future improvements (fine-tuning, more dialects, real-time usage)

LicenseMIT LicenseContributingContributions are welcome!
Please open an issue first to discuss what you would like to change.Made with passion for Arabic language technology
© 2025–2026 Rashed Dadouch


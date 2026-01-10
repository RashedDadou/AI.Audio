Karbouji Al-Shamiya Crystal 2026
# AI.Audio engine #

============================
A fully local (offline-first) audio engine specializing in Levantine Arabic (Lebanese/Syrian/Palestinian/Jordanian dialects).

It aims to provide the best possible quality text-to-speech (TTS) conversion in the Levantine dialect using open-source models.

Current Key Features (January 2026):

• High-quality text-to-speech conversion in the Levantine dialect using facebook/mms-tts-ara
• Optional English support (facebook/mms-tts-eng)
• Automatic language detection (Arabic ↔ English)
• Audio cleaning and enhancement using DeepFilterNet3 (very powerful noise removal)
• Speech recognition (STT) using Whisper small with relatively good performance on the Levantine dialect
• Advanced audio source separation (vocals/drums/bass/...) using Demucs (htdemucs)
• Bilingual (Arabic/English) graphical interface with a modern dark theme
• Instant playback with instant pause and no distortion
• Processing of long texts with intelligent segmentation and seamless merging
• Comprehensive recording of processes with end-of-session reports

Philosophy:

─────────
The project aims to be an open-source, fully local Arabic audio tool,
without relying on cloud services or subscriptions, with a special focus on the quality of the Levantine dialect,
which is often neglected in large commercial models.

Main Dependencies:

───────────────────────
torch · torchaudio · transformers · soundfile · sounddevice · numpy · scipy
openai-whisper (optional) · demucs (optional) · df (DeepFilterNet3)

Developer: Rashed Daadoush
Period: 2025–2026
License: MIT

Important Note:
─────────────
The project is still in active development.

The current quality relies heavily on the quality of the base models (especially MMS-TTS), and there is no dedicated fine-tuning yet.

"Everything we dream of in natural Arabic sound... we're trying to achieve step by step."

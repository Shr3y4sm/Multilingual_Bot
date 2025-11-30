# Animated-AI-translator

This project is an advanced AI-driven chatbot designed to bridge language barriers through real-time multilingual communication. It supports both voice and text input/output, providing instant translations across multiple languages. The bot uses Natural Language Processing (NLP), Neural Machine Translation (NMT), and Text-to-Speech (TTS) technologies to ensure fluid and human-like conversation.

What makes this bot unique is its integration of animated avatars that visually respond to user inputs with realistic lip-syncing and expressions, offering a more engaging and immersive experience. Ideal for education, customer support, or global collaboration, the bot promotes inclusivity and accessibility by allowing users to communicate in their native language, regardless of the medium.

## ✨ Key Features

🌍 **Real-time Language Translation using NMT**

- Supports 16+ languages including English, Hindi, Kannada, Tamil, Telugu, and more
- Automatic language detection
- Neural Machine Translation for accurate translations

🎤 **Voice Input and Output for hands-free communication**

- Speech-to-Text recognition using Google Speech Recognition
- Text-to-Speech synthesis with natural voice responses
- Real-time voice processing

🧠 **AI-Powered Chatbot with NLP-based conversation handling**

- Powered by Google Gemini AI
- Context-aware conversations
- Intent detection (greeting, question, translation, conversation)
- Multi-turn dialogue support

🗣️ **Text-to-Speech Synthesis for natural voice responses**

- Natural voice generation in multiple languages
- Synchronized with animated avatar

🎭 **Animated Avatar Interaction with lip-sync capabilities**

- Visual avatar representation
- Synchronized with speech output
- Enhanced user engagement

💬 **Multi-Lingual Support for global users**

- 16+ languages supported
- Easy language switching
- Language-specific responses

📜 **Chat History Logging for reference**

- Complete conversation history
- Session management
- Analytics and insights

📊 **Analytics Dashboard**

- Intent distribution analysis
- Language usage statistics
- Session tracking

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- Microphone (for voice input)
- Google Gemini API Key

### Setup Steps

1. **Clone the repository**

```bash
git clone <repository-url>
cd Animated-AI-translator
```

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

1. **Set up Google Gemini API Key**

   **Option 1: Using .env File (Recommended)**
   - Create a file named `.env` in the project root
   - Add your API key:
   
   ```env
   GEMINI_API_KEY=your-api-key-here
   ```
   - The application will automatically load it

   **Option 2: Environment Variable**
   
   ```bash
   # Windows
   set GEMINI_API_KEY=your-api-key-here
   
   # Linux/Mac
   export GEMINI_API_KEY=your-api-key-here
   ```

   **Option 3: Streamlit Secrets** (create `.streamlit/secrets.toml`)
   
   ```toml
   GEMINI_API_KEY = "your-api-key-here"
   ```

   Get your API key from: [Google MakerSuite](https://makersuite.google.com/app/apikey)

1. **Add Avatar Video (Optional)**
   - Place your animated avatar video file as `girl.gif.mp4` in the project root
   - Or update `ASSISTANT_VIDEO_PATH` in `main.py` with your video path

1. **Run the application**

```bash
streamlit run main.py
```

## 📖 Usage

### AI Chatbot Mode

1. Select your preferred language from the sidebar
2. Choose input method (Text or Voice)
3. Type or speak your message
4. AI will respond with context-aware answers
5. Use "Speak Response" to hear the AI's response

### Translation Mode

1. Navigate to the "Translation" tab
2. Enter text or use voice input
3. Select source and target languages
4. Click "Translate & Speak" to get translation and audio

### Analytics

- View conversation statistics
- Analyze intent distribution
- Track language usage patterns

## 🛠️ Technologies Used

- **Frontend**: Streamlit
- **AI/ML**: Google Gemini AI, NLP
- **Translation**: Google Translator API (Deep Translator)
- **Speech Recognition**: Google Speech Recognition API
- **Text-to-Speech**: Google Text-to-Speech (gTTS)
- **Language Support**: 16+ languages

## 🛰️ Offline / Low-Bandwidth Mode (Experimental)

Offline mode lets the app operate with minimal or no internet connectivity for Speech-to-Text (STT), Text-to-Speech (TTS), and basic Translation.

### Components

- **STT**: Vosk (local speech recognition models)
- **TTS**: pyttsx3 (system voices; English best, other languages depend on OS voices)
- **Translation**: Argos Translate (installable language packs)

### Install Optional Dependencies

```powershell
pip install vosk pyttsx3 argostranslate==1.9.0
```

### Download & Place Vosk Model

1. Get a small model (e.g. English): <https://alphacephei.com/vosk/models>
2. Extract into: `models/vosk/en/` so the path contains files like `conf`, `am`, etc.
3. (Optional) Set a custom path:
```powershell
$Env:VOSK_MODEL_PATH = "models/vosk/en"
```

### Install Argos Translate Language Packs
1. Download `.argosmodel` files (e.g. English–Hindi) from: https://github.com/argosopentech/argos-translate
2. Install each pack:
```powershell
python -m argostranslate.package install .\en_hi.argosmodel
python -m argostranslate.package install .\en_es.argosmodel
```
3. Verify installed packs by running the app and enabling offline mode.

### Enable Offline Mode in the App
1. Start the app:
```powershell
streamlit run main.py
```
2. Open sidebar → check: **Enable Offline Mode (Experimental)**.
3. Capability summary shows which parts initialized (`vosk`, `pyttsx3`, `argos`). Missing items display setup guidance.

### Testing Checklist
| Feature | Action | Expected |
|---------|--------|----------|
| Offline STT | Select input method "🎤 Offline STT", speak | Transcribed text appears or warning if model missing |
| Fallback STT | Disable offline or remove model | Cloud Google STT used instead |
| Offline TTS | Send message → response speaks | Uses system voice (less natural than gTTS) |
| Fallback TTS | Disable offline mode | gTTS mp3 generated as before |
| Offline Translation | Use "Translate & Speak" with offline enabled | Translation succeeds via Argos if pack installed |
| Fallback Translation | Remove Argos pack | Falls back to GoogleTranslator API |

### Simulate Low Bandwidth
- Disconnect network or block outbound temporarily; offline components continue to work (Gemini responses will fail—demo fallback by prompting cached or simplified responses if needed).
- For a fully offline demo, avoid using Chatbot tab or replace with a local FAQ answer set.

### Tips & Limitations
- Argos translation quality is lower than neural cloud services; highlight educational access benefit.
- pyttsx3 voice availability varies by OS; for richer voices keep gTTS as hybrid.
- Vosk supports multiple languages—add more models in parallel folders and extend detection logic.
- Heuristic auto language detection in offline translation falls back to English vs Hindi; refine later.

### Roadmap Upgrades (Future)
- Whisper.cpp integration for higher-quality offline STT.
- Coqui TTS for multilingual neural voices offline.
- Better language auto-detect (character script + frequency models).
- Local intent classification to replace Gemini in offline classrooms.


## 📁 Project Structure

```
Animated-AI-translator/
├── main.py                 # Main application file
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── chat_history.json      # Chat conversation history
├── translations.txt       # Translation history
└── girl.gif.mp4          # Animated avatar video (optional)
```

## 🔧 Configuration

### Supported Languages
- English (en)
- Hindi (hi)
- Kannada (kn)
- Tamil (ta)
- Telugu (te)
- Marathi (mr)
- Bengali (bn)
- Gujarati (gu)
- Punjabi (pa)
- Urdu (ur)
- Spanish (es)
- French (fr)
- German (de)
- Japanese (ja)
- Chinese (zh)
- Arabic (ar)

### Customization
- Modify `SUPPORTED_LANGUAGES` in `main.py` to add more languages
- Update `ASSISTANT_VIDEO_PATH` for custom avatar
- Adjust intent detection patterns in `detect_intent()` function

## 🎯 Features for Presentation

### For AICTE Productization Fellowship YUKTI Innovation Challenge 2025

1. **AI-Powered Chatbot**
   - Context-aware conversations
   - Intent detection and classification
   - Multi-language support

2. **Neural Machine Translation**
   - Real-time translation
   - 16+ language pairs
   - Automatic language detection

3. **Natural Language Processing**
   - Intent recognition
   - Context management
   - Conversation flow

4. **Voice Interface**
   - Speech-to-Text
   - Text-to-Speech
   - Hands-free operation

5. **Analytics Dashboard**
   - Usage statistics
   - Intent analysis
   - Language distribution

## 📝 Notes

- Ensure stable internet connection for API calls
- Microphone access required for voice input
- Google Gemini API has rate limits (free tier available)
- Avatar video is optional but enhances user experience

## 🤝 Contributing

This project is developed for AICTE Productization Fellowship YUKTI Innovation Challenge 2025.

## 📄 License

This project is developed for academic and research purposes.

## 👥 Authors

Developed for AICTE Productization Fellowship YUKTI Innovation Challenge 2025 - Institution's Innovation Council (IIC), AICTE 2nd Stage Evaluation.

## 🙏 Acknowledgments

- Google Gemini AI for conversational AI capabilities
- Google Translator API for translation services
- Streamlit for the web framework
- Open source community for various libraries

---

**Status**: ✅ Production Ready for Presentation

**Version**: 2.0.0

**Last Updated**: 2025

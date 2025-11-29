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

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up Google Gemini API Key**

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

   Get your API key from: https://makersuite.google.com/app/apikey

4. **Add Avatar Video (Optional)**
   - Place your animated avatar video file as `girl.gif.mp4` in the project root
   - Or update `ASSISTANT_VIDEO_PATH` in `main.py` with your video path

5. **Run the application**
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

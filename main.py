import streamlit as st
import os
import json
import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
from datetime import datetime
import google.generativeai as genai
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
TRANSLATION_FILE = "translations.txt"
CHAT_HISTORY_FILE = "chat_history.json"
ASSISTANT_VIDEO_PATH = "girl.gif.mp4"

# Supported languages with full names
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "ur": "Urdu",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
    "zh": "Chinese",
    "ar": "Arabic"
}

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
if 'conversation_context' not in st.session_state:
    st.session_state.conversation_context = []

def initialize_gemini():
    """Initialize Google Gemini AI"""
    # Try to get API key from .env file first, then environment variable, then Streamlit secrets
    api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except:
            pass
    
    if api_key and api_key != "":
        try:
            genai.configure(api_key=api_key)
            # Using Gemini 2.5 models - 1.5 models are deprecated
            # Try Gemini 2.5 Flash first (fastest, best for real-time chat)
            try:
                return genai.GenerativeModel('gemini-2.5-flash')
            except:
                # Fallback to Gemini 2.5 Pro if Flash is not available
                try:
                    return genai.GenerativeModel('gemini-2.5-pro')
                except:
                    # Last fallback to Gemini 2.0 Flash if 2.5 models not available
                    try:
                        return genai.GenerativeModel('gemini-2.0-flash-exp')
                    except Exception as e:
                        st.error(f"Error initializing Gemini 2.5 models: {e}")
                        return None
        except Exception as e:
            st.error(f"Error initializing Gemini: {e}")
            return None
    return None

def detect_intent(text):
    """Detect user intent from text"""
    text_lower = text.lower()
    
    # Greeting patterns
    if any(word in text_lower for word in ['hi', 'hello', 'hey', 'namaste', 'good morning', 'good afternoon', 'good evening']):
        return "greeting"
    
    # Question patterns
    if any(word in text_lower for word in ['what', 'when', 'where', 'why', 'how', 'who', 'which', '?']):
        return "question"
    
    # Translation request
    if any(word in text_lower for word in ['translate', 'translation', 'meaning', 'what does']):
        return "translation"
    
    # Conversation
    if any(word in text_lower for word in ['tell', 'explain', 'describe', 'talk about']):
        return "conversation"
    
    return "general"

def get_ai_response(user_message, model, language="en"):
    """Get AI response using Gemini"""
    if not model:
        return "AI Response Error: Please configure GEMINI_API_KEY in environment variables or Streamlit secrets."
    
    try:
        # Build context from conversation history
        context = "\n".join([f"User: {msg['user']}\nAssistant: {msg['bot']}" 
                            for msg in st.session_state.conversation_context[-5:]])
        
        # Create prompt with context
        prompt = f"""You are a helpful multilingual AI assistant. 
        Respond naturally and conversationally in {SUPPORTED_LANGUAGES.get(language, 'English')}.
        Keep responses concise and friendly.
        
        Previous conversation:
        {context}
        
        User: {user_message}
        Assistant:"""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Response Error: {str(e)}"

def save_chat_entry(user_message, bot_response, language, intent):
    """Save chat entry to history"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": st.session_state.session_id,
        "user_message": user_message,
        "bot_response": bot_response,
        "language": language,
        "intent": intent
    }
    
    st.session_state.chat_history.append(entry)
    st.session_state.conversation_context.append({
        "user": user_message,
        "bot": bot_response
    })
    
    # Save to file
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []
    
    history.append(entry)
    
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_chat_history():
    """Load chat history from file"""
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_translation(original, translated, src_lang, tgt_lang):
    """Save translations to a file"""
    with open(TRANSLATION_FILE, "a", encoding="utf-8") as file:
        file.write(f"{src_lang} -> {tgt_lang} | {original} => {translated}\n")

def load_translation_history():
    """Load translation history with newest entries on top"""
    if os.path.exists(TRANSLATION_FILE):
        with open(TRANSLATION_FILE, "r", encoding="utf-8") as file:
            history = file.readlines()
            return history[::-1]  # Reverse list to show newest entries first
    return []

def speech_to_text():
    """Convert speech to text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Speak now...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            st.error("❌ Could not understand the speech.")
        except sr.RequestError:
            st.error("❌ Network error. Check your connection.")
        except sr.WaitTimeoutError:
            st.error("❌ No speech detected. Try again.")
    return None

def text_to_speech(text, language):
    """Convert text to speech and play AI Assistant Video"""
    try:
        tts = gTTS(text, lang=language)
        audio_file = "output.mp3"
        tts.save(audio_file)

        # Show AI Assistant Video while speaking
        col1, col2 = st.columns([3, 1])
        with col2:
            if os.path.exists(ASSISTANT_VIDEO_PATH):
                st.video(ASSISTANT_VIDEO_PATH)
            else:
                st.info("🎭 Avatar video not found. Please add girl.gif.mp4")

        # Play Audio
        st.audio(audio_file, format="audio/mp3")
    except Exception as e:
        st.error(f"TTS Error: {e}")

def translate_text(text, target_lang):
    """Translate text using Google Translator"""
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        save_translation(text, translated, "auto-detected", target_lang)
        return translated
    except Exception as e:
        st.error(f"❌ Translation Error: {e}")
        return None

# Streamlit UI
st.set_page_config(
    page_title="AI Translator with Talking Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Gemini
gemini_model = initialize_gemini()

# Main Title
st.title("🌍 AI Speech & Text Translator with Talking Assistant")
st.markdown("**Advanced AI-driven chatbot with real-time multilingual communication, NLP, and animated avatar**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Language Selection
    selected_language = st.selectbox(
        "🌐 Select Language:",
        options=list(SUPPORTED_LANGUAGES.keys()),
        format_func=lambda x: f"{SUPPORTED_LANGUAGES[x]} ({x})",
        index=0
    )
    
    st.divider()
    
    # Chat History
    st.header("📜 Chat History")
    if st.button("🔄 Refresh History"):
        st.session_state.chat_history = load_chat_history()
    
    if st.session_state.chat_history:
        st.write(f"**Total Messages:** {len(st.session_state.chat_history)}")
        if st.button("🗑️ Clear Current Session"):
            st.session_state.chat_history = []
            st.session_state.conversation_context = []
            st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.rerun()
    
    st.divider()
    
    # Translation History
    st.header("🔠 Translation History")
    if st.button("📜 Show Translation History"):
        history = load_translation_history()
        if history:
            st.write("\n".join(history[:10]))
        else:
            st.write("No translation history available.")
    
    st.divider()

# Main Content Area
tab1, tab2, tab3 = st.tabs(["💬 AI Chatbot", "🔠 Translation", "📊 Analytics"])

# Tab 1: AI Chatbot
with tab1:
    st.header("🤖 AI-Powered Chatbot with NLP")
    st.markdown("**Chat with AI in multiple languages with conversation context and intent detection**")
    
    # Chat Interface
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        if st.session_state.chat_history:
            for entry in st.session_state.chat_history[-10:]:  # Show last 10 messages
                with st.chat_message("user"):
                    st.write(entry['user_message'])
                    st.caption(f"Intent: {entry['intent']} | Language: {entry['language']}")
                
                with st.chat_message("assistant"):
                    st.write(entry['bot_response'])
                    st.caption(f"Session: {entry['session_id']}")
    
    # Input method
    input_method = st.radio(
        "Choose input method:",
        ["📝 Type Text", "🎤 Speak"],
        horizontal=True,
        key="chatbot_input_method"
    )
    
    user_input = None
    
    if input_method == "📝 Type Text":
        user_input = st.text_input("Type your message:", key="chat_input")
    else:
        if st.button("🎤 Start Speaking"):
            recognized_text = speech_to_text()
            if recognized_text:
                user_input = recognized_text
                st.session_state['recognized_text'] = recognized_text
    
    if 'recognized_text' in st.session_state and input_method == "🎤 Speak":
        user_input = st.text_input("Recognized Speech:", value=st.session_state['recognized_text'], key="recognized_input")
    
    # Process user input
    if user_input and st.button("💬 Send Message", type="primary"):
        # Detect intent
        intent = detect_intent(user_input)
        
        # Get AI response
        with st.spinner("🤔 AI is thinking..."):
            bot_response = get_ai_response(user_input, gemini_model, selected_language)
        
        # Save to history
        save_chat_entry(user_input, bot_response, selected_language, intent)
        
        # Display response
        with st.chat_message("user"):
            st.write(user_input)
            st.caption(f"Intent: {intent}")
        
        with st.chat_message("assistant"):
            st.write(bot_response)
            
            # Text to Speech option
            if st.button("🔊 Speak Response", key="tts_chat"):
                text_to_speech(bot_response, selected_language)
        
        st.rerun()

# Tab 2: Translation
with tab2:
    st.header("🔠 Real-time Language Translation")
    st.markdown("**Translate text or speech into multiple languages with NMT**")
    
    input_method = st.radio(
        "Choose input method:",
        ["📝 Type Text", "🎤 Speak"],
        horizontal=True,
        key="translation_input_method"
    )
    
    text = None
    if input_method == "📝 Type Text":
        text = st.text_area("Enter text to translate:", height=100)
    else:
        if st.button("🎤 Start Speaking"):
            recognized_text = speech_to_text()
            if recognized_text:
                st.session_state['recognized_text_trans'] = recognized_text
        
        if 'recognized_text_trans' in st.session_state:
            text = st.text_area("Recognized Speech:", value=st.session_state['recognized_text_trans'], height=100)
    
    if text:
        col1, col2 = st.columns(2)
        
        with col1:
            source_lang = st.selectbox(
                "Source Language:",
                options=["auto"] + list(SUPPORTED_LANGUAGES.keys()),
                format_func=lambda x: "Auto-detect" if x == "auto" else f"{SUPPORTED_LANGUAGES.get(x, x)} ({x})"
            )
        
        with col2:
            target_lang = st.selectbox(
                "Target Language:",
                options=list(SUPPORTED_LANGUAGES.keys()),
                format_func=lambda x: f"{SUPPORTED_LANGUAGES[x]} ({x})",
                index=1 if "hi" in SUPPORTED_LANGUAGES else 0
            )
        
        if st.button("🔄 Translate & Speak", type="primary"):
            with st.spinner("Translating..."):
                translated_text = translate_text(text, target_lang)
            
            if translated_text:
                st.success(f"✅ **Translated Text ({SUPPORTED_LANGUAGES[target_lang]}):**")
                st.info(translated_text)
                text_to_speech(translated_text, target_lang)

# Tab 3: Analytics
with tab3:
    st.header("📊 Analytics & Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_chats = len(st.session_state.chat_history)
        st.metric("Total Chat Messages", total_chats)
    
    with col2:
        total_sessions = len(set([entry['session_id'] for entry in st.session_state.chat_history])) if st.session_state.chat_history else 0
        st.metric("Active Sessions", total_sessions)
    
    with col3:
        languages_used = len(set([entry['language'] for entry in st.session_state.chat_history])) if st.session_state.chat_history else 0
        st.metric("Languages Used", languages_used)
    
    st.divider()
    
    # Intent Distribution
    if st.session_state.chat_history:
        st.subheader("📈 Intent Distribution")
        intent_counts = {}
        for entry in st.session_state.chat_history:
            intent = entry.get('intent', 'unknown')
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        st.bar_chart(intent_counts)
        
        st.divider()
        
        # Language Usage
        st.subheader("🌐 Language Usage")
        lang_counts = {}
        for entry in st.session_state.chat_history:
            lang = entry.get('language', 'unknown')
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
        
        st.bar_chart(lang_counts)
    else:
        st.info("No chat history available. Start chatting to see analytics!")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🚀 <b>Animated AI Translator</b> | Powered by Google Gemini AI, NLP, and Neural Machine Translation</p>
    <p>Developed for AICTE Productization Fellowship YUKTI Innovation Challenge 2025</p>
</div>
""", unsafe_allow_html=True)

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

# Offline utilities (lazy import, guard if file not present)
try:
    from offline_utils import (
        initialize_offline_resources,
        offline_stt,
        offline_tts,
        offline_translate,
        is_offline_mode,
        capabilities_summary,
    )
    OFFLINE_UTILS_AVAILABLE = True
except ImportError:
    OFFLINE_UTILS_AVAILABLE = False

# Import lip sync utilities
try:
    from lip_sync_utils import create_lip_sync_video, get_expression_for_text, ExpressionAnimator
    LIP_SYNC_AVAILABLE = True
except ImportError:
    LIP_SYNC_AVAILABLE = False

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
if 'generated_videos' not in st.session_state:
    st.session_state.generated_videos = []  # Track generated video files
if 'current_video_id' not in st.session_state:
    st.session_state.current_video_id = None  # Current video identifier
if 'last_video_path' not in st.session_state:
    st.session_state.last_video_path = None  # Last displayed video path
if 'last_audio_path' not in st.session_state:
    st.session_state.last_audio_path = None  # Last audio path
if 'last_expression' not in st.session_state:
    st.session_state.last_expression = None  # Last detected expression
if 'clear_input' not in st.session_state:
    st.session_state.clear_input = False  # Flag to clear input on next render
if 'clear_input' not in st.session_state:
    st.session_state.clear_input = False  # Flag to clear input on next render

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
    # If offline mode toggled and offline utilities available, use offline STT first
    if OFFLINE_UTILS_AVAILABLE and is_offline_mode():
        text = offline_stt()
        if text:
            return text
        # Fall through to cloud STT if offline failed
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

def cleanup_old_videos(max_age_seconds=300):
    """Clean up old generated video files"""
    try:
        import time
        current_time = time.time()
        for video_file in st.session_state.generated_videos.copy():
            if os.path.exists(video_file):
                file_age = current_time - os.path.getmtime(video_file)
                if file_age > max_age_seconds:  # Delete files older than 5 minutes
                    try:
                        os.remove(video_file)
                        st.session_state.generated_videos.remove(video_file)
                    except:
                        pass
            else:
                # Remove from list if file doesn't exist
                st.session_state.generated_videos.remove(video_file)
    except:
        pass

def text_to_speech(text, language, enable_lip_sync=True, auto_generate=True, ai_model=None):
    """
    Convert text to speech and auto-generate AI Assistant Video with accurate lip sync and emotions
    
    Args:
        text: Text to convert to speech
        language: Language code for TTS
        enable_lip_sync: Enable lip sync generation
        auto_generate: Automatically generate video (no button needed)
        ai_model: Optional AI model for better emotion detection
    """
    try:
        # Clean up old videos first
        cleanup_old_videos()
        
        # Generate audio with absolute path (offline first if enabled)
        audio_file = os.path.abspath("output.mp3")
        offline_used = False
        if OFFLINE_UTILS_AVAILABLE and is_offline_mode():
            offline_path = offline_tts(text, language, output_file=audio_file)
            if offline_path and os.path.exists(offline_path):
                offline_used = True
        if not offline_used:
            tts = gTTS(text, lang=language)
            tts.save(audio_file)

        # Detect emotion with AI-enhanced analysis
        expression_video = ASSISTANT_VIDEO_PATH
        detected_expression = "neutral"
        
        if LIP_SYNC_AVAILABLE:
            from lip_sync_utils import ExpressionAnimator
            animator = ExpressionAnimator()
            # Use AI for better emotion detection if available
            detected_expression = animator.detect_expression(text, use_ai=(ai_model is not None), ai_model=ai_model)
            expression_video = animator.get_expression_video_path(detected_expression)
        
        # Auto-generate lip-synced video if enabled
        # Ensure we have a valid video file to start with
        if not os.path.exists(expression_video):
            expression_video = ASSISTANT_VIDEO_PATH
        
        # Always set video_file to a valid path if expression_video exists
        if os.path.exists(expression_video):
            video_file = os.path.abspath(expression_video)
        elif os.path.exists(ASSISTANT_VIDEO_PATH):
            video_file = os.path.abspath(ASSISTANT_VIDEO_PATH)
        else:
            video_file = None
        
        if enable_lip_sync and LIP_SYNC_AVAILABLE and video_file:
            try:
                # Check which API is configured (priority: D-ID > HeyGen > Synthesia > Elai)
                did_api_key = os.getenv("DID_API_KEY", "")
                heygen_api_key = os.getenv("HEYGEN_API_KEY", "")
                synthesia_api_key = os.getenv("SYNTHESIA_API_KEY", "")
                elai_api_key = os.getenv("ELAI_API_KEY", "")
                
                use_api = False
                api_provider = "heygen"
                api_key = None
                avatar_id = None
                
                if did_api_key:
                    use_api = True
                    api_provider = "d-id"
                    api_key = did_api_key
                    avatar_id = os.getenv("DID_AVATAR_ID", "")
                elif heygen_api_key:
                    use_api = True
                    api_provider = "heygen"
                    api_key = heygen_api_key
                    avatar_id = os.getenv("HEYGEN_AVATAR_ID", "")
                elif synthesia_api_key:
                    use_api = True
                    api_provider = "synthesia"
                    api_key = synthesia_api_key
                    avatar_id = os.getenv("SYNTHESIA_AVATAR_ID", "")
                elif elai_api_key:
                    use_api = True
                    api_provider = "elai"
                    api_key = elai_api_key
                    avatar_id = os.getenv("ELAI_AVATAR_ID", "")
                
                api_name = api_provider.upper() if use_api else "Local"
                with st.spinner(f"🎬 Generating {detected_expression} expression with lip sync..." + (f" (via {api_name} API)" if use_api else "")):
                    # Use absolute path for output
                    lip_sync_output = os.path.abspath(f"lip_sync_{st.session_state.session_id}_{datetime.now().strftime('%H%M%S')}.mp4")
                    result = create_lip_sync_video(
                        audio_file, 
                        video_file, 
                        lip_sync_output,
                        use_api=use_api,
                        api_provider=api_provider,
                        api_key=api_key,
                        avatar_id=avatar_id,
                        text_content=text  # Pass the text for D-ID API
                    )
                    if result and os.path.exists(result) and os.path.getsize(result) > 0:
                        video_file = os.path.abspath(result)
                        # Track generated video with absolute path
                        if video_file not in st.session_state.generated_videos:
                            st.session_state.generated_videos.append(video_file)
                        st.success(f"✅ Generated {detected_expression} expression with lip sync!" + (f" ({api_name})" if use_api else ""))
                    else:
                        # Keep original video if lip sync fails
                        st.info("ℹ️ Using original video")
            except Exception as e:
                st.warning(f"⚠️ Lip sync generation failed: {str(e)}. Using original video.")

        # Show AI Assistant Video while speaking
        # Determine which video to show - ensure we always have a video if available
        video_to_show = None
        
        # Priority: generated video > expression video > default avatar
        if video_file and os.path.exists(video_file):
            video_to_show = os.path.abspath(video_file)
        elif os.path.exists(expression_video):
            video_to_show = os.path.abspath(expression_video)
        elif os.path.exists(ASSISTANT_VIDEO_PATH):
            video_to_show = os.path.abspath(ASSISTANT_VIDEO_PATH)
        
        # Store in session state for persistence across reruns
        if video_to_show:
            st.session_state.last_video_path = video_to_show
            st.session_state.last_audio_path = audio_file
            st.session_state.last_expression = detected_expression
        
        # Display video and audio in columns
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Main content area - audio will be here too
            pass
        
        with col2:
            # Display video if available
            if video_to_show and os.path.exists(video_to_show):
                try:
                    # Use Streamlit's native video player
                    # Display video - ensure it's visible
                    st.video(video_to_show, autoplay=True)
                    
                    # Show detected expression
                    if LIP_SYNC_AVAILABLE:
                        emoji_map = {
                            "happy": "😊", "sad": "😢", "surprised": "😲", 
                            "thinking": "🤔", "confident": "💪", "neutral": "😐"
                        }
                        emoji = emoji_map.get(detected_expression, "😊")
                        st.caption(f"Expression: {detected_expression} {emoji}")
                    
                    # Play audio in the same column
                    st.audio(audio_file, format="audio/mp3", autoplay=True)
                except Exception as e:
                    st.error(f"Video error: {str(e)}")
                    st.audio(audio_file, format="audio/mp3", autoplay=True)
            else:
                # No video available - show debug info
                if not os.path.exists(ASSISTANT_VIDEO_PATH):
                    st.info("🎭 Avatar video not found. Please add `girl.gif.mp4` to project root.")
                else:
                    st.warning(f"⚠️ Video not accessible.")
                    with st.expander("🔍 Debug Info"):
                        st.write(f"video_file: {video_file}")
                        st.write(f"expression_video: {expression_video}")
                        st.write(f"ASSISTANT_VIDEO_PATH: {ASSISTANT_VIDEO_PATH}")
                        st.write(f"video_to_show: {video_to_show}")
                        st.write(f"File exists: {os.path.exists(ASSISTANT_VIDEO_PATH) if ASSISTANT_VIDEO_PATH else False}")
                st.audio(audio_file, format="audio/mp3", autoplay=True)
        
    except Exception as e:
        st.error(f"TTS Error: {e}")
        # Fallback: just play audio
        if os.path.exists(audio_file):
            st.audio(audio_file, format="audio/mp3")

def translate_text(text, target_lang):
    """Translate text using Google Translator"""
    try:
        # Offline first if enabled
        if OFFLINE_UTILS_AVAILABLE and is_offline_mode():
            offline_result = offline_translate(text, src_lang='auto', tgt_lang=target_lang)
            if offline_result:
                save_translation(text, offline_result, "auto-detected-offline", target_lang)
                return offline_result
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

    # Offline Mode Toggle
    st.subheader("🛰️ Offline / Low-Bandwidth Mode")
    offline_mode_enabled = st.checkbox(
        "Enable Offline Mode (Experimental)",
        value=False,
        help="Use local STT, TTS, and translation where possible (Vosk, pyttsx3, Argos). Falls back to online services if components missing."
    )
    st.session_state["offline_mode_enabled"] = offline_mode_enabled
    if offline_mode_enabled:
        if OFFLINE_UTILS_AVAILABLE:
            caps = initialize_offline_resources()
            missing = [k for k,v in caps.items() if not v]
            if missing:
                st.warning("Offline components missing: " + ", ".join(missing))
                with st.expander("Offline Setup Instructions"):
                    st.markdown("""
**Install optional packages:**
```
pip install vosk pyttsx3 argostranslate==1.9.0
```
**Vosk model:** Download and place in `models/vosk/en/` (e.g. `vosk-model-small-en-us-0.15`).
**Argos language packs:** Download `.argosmodel` files and install:
```
python -m argostranslate.package install <file.argosmodel>
```
""")
            else:
                st.success("All offline components initialized.")
            st.caption("Capabilities: " + capabilities_summary())
        else:
            st.error("offline_utils.py not found or failed to import.")
    
    st.divider()
    
    # Lip Sync Settings
    st.subheader("🎭 Animation Settings")
    enable_lip_sync = st.checkbox(
        "Enable Lip Sync & Expressions",
        value=True,
        help="Generate lip-synced animations with expressive reactions based on text sentiment"
    )
    
    if LIP_SYNC_AVAILABLE:
        st.success("✅ Lip sync features available")
    else:
        st.warning("⚠️ Install moviepy and mediapipe for lip sync: pip install moviepy mediapipe")
    
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
    
    # Display last video if available (persists after rerun)
    if 'last_video_path' in st.session_state and st.session_state.last_video_path:
        if os.path.exists(st.session_state.last_video_path):
            col1, col2 = st.columns([3, 1])
            with col2:
                try:
                    st.video(st.session_state.last_video_path, autoplay=False)
                    
                    if 'last_expression' in st.session_state and st.session_state.last_expression:
                        emoji_map = {
                            "happy": "😊", "sad": "😢", "surprised": "😲", 
                            "thinking": "🤔", "confident": "💪", "neutral": "😐"
                        }
                        emoji = emoji_map.get(st.session_state.last_expression, "😊")
                        st.caption(f"Expression: {st.session_state.last_expression} {emoji}")
                    
                    if 'last_audio_path' in st.session_state and st.session_state.last_audio_path:
                        if os.path.exists(st.session_state.last_audio_path):
                            st.audio(st.session_state.last_audio_path, format="audio/mp3", autoplay=False)
                except Exception as e:
                    st.error(f"Video display error: {str(e)}")
    
    # Input method
    input_options = ["📝 Type Text", "🎤 Speak"]
    if OFFLINE_UTILS_AVAILABLE and is_offline_mode():
        input_options.append("🎤 Offline STT")
    input_method = st.radio(
        "Choose input method:",
        input_options,
        horizontal=True,
        key="chatbot_input_method"
    )
    
    # Use form to handle input clearing automatically
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = None
        
        if input_method == "📝 Type Text":
            user_input = st.text_input("Type your message:", key="chat_input_form")
        elif input_method == "🎤 Speak":
            if st.form_submit_button("🎤 Start Speaking"):
                recognized_text = speech_to_text()
                if recognized_text:
                    st.session_state['recognized_text'] = recognized_text
        elif input_method == "🎤 Offline STT":
            if st.form_submit_button("🔌 Start Offline STT"):
                recognized_text = offline_stt() if (OFFLINE_UTILS_AVAILABLE and is_offline_mode()) else None
                if recognized_text:
                    st.session_state['recognized_text'] = recognized_text
        
        if 'recognized_text' in st.session_state and input_method == "🎤 Speak":
            user_input = st.text_input("Recognized Speech:", value=st.session_state['recognized_text'], key="recognized_input_form")
        
        # Process user input
        submitted = st.form_submit_button("💬 Send Message", type="primary")
        
        if submitted and user_input and user_input.strip():
            # Store the input temporarily
            current_input = user_input.strip()
            
            # Clear recognized text after processing
            if 'recognized_text' in st.session_state:
                del st.session_state['recognized_text']
            
            # Detect intent
            intent = detect_intent(current_input)
            
            # Get AI response
            with st.spinner("🤔 AI is thinking..."):
                bot_response = get_ai_response(current_input, gemini_model, selected_language)
            
            # Save to history
            save_chat_entry(current_input, bot_response, selected_language, intent)
            
            # Display response in chat
            with st.chat_message("user"):
                st.write(current_input)
                st.caption(f"Intent: {intent}")
            
            with st.chat_message("assistant"):
                st.write(bot_response)
                
                # Auto-generate video with emotion and lip sync
                if enable_lip_sync and LIP_SYNC_AVAILABLE:
                    # Automatically generate and display video
                    text_to_speech(bot_response, selected_language, 
                                 enable_lip_sync=enable_lip_sync, 
                                 auto_generate=True, 
                                 ai_model=gemini_model)
                else:
                    # Manual button if lip sync disabled
                    if st.button("🔊 Speak Response", key=f"tts_chat_{len(st.session_state.chat_history)}"):
                        text_to_speech(bot_response, selected_language, enable_lip_sync=False)
            
            # Rerun to refresh UI - form will auto-clear inputs
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
                # Auto-generate with emotion detection
                text_to_speech(translated_text, target_lang, 
                             enable_lip_sync=enable_lip_sync,
                             auto_generate=True,
                             ai_model=gemini_model)

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
    <p>🚀 <b>Animated AI Translator</b> | Powered by NLP and Neural Machine Translation</p>
    <p>Developed for AICTE Productization Fellowship YUKTI Innovation Challenge 2025</p>
</div>
""", unsafe_allow_html=True)

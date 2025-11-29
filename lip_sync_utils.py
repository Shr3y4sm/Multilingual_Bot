"""
Lip Sync and Animation Utilities
Provides multiple approaches for avatar lip sync and expressive animations
"""

import os
import subprocess
import cv2
import numpy as np
from typing import Optional, Tuple
import json
import requests
import time

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


class LipSyncGenerator:
    """Generate lip-synced videos from audio and avatar images/videos"""
    
    def __init__(self):
        self.mediapipe_face = None
        self.face_mesh = None
        if MEDIAPIPE_AVAILABLE:
            try:
                self.mp_face_mesh = mp.solutions.face_mesh
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5
                )
            except Exception as e:
                # Handle MediaPipe initialization errors gracefully
                print(f"MediaPipe initialization warning: {e}")
                self.face_mesh = None
    
    def generate_lip_sync_video(self, audio_path: str, avatar_path: str, output_path: str) -> bool:
        """
        Generate a lip-synced video using Wav2Lip or alternative methods
        
        Args:
            audio_path: Path to the audio file
            avatar_path: Path to the avatar image/video
            output_path: Output path for the lip-synced video
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Method 1: Try Wav2Lip (if available)
        if self._check_wav2lip_available():
            return self._generate_with_wav2lip(audio_path, avatar_path, output_path)
        
        # Method 2: Use MoviePy to merge video and audio (basic lip sync)
        elif MOVIEPY_AVAILABLE:
            return self._generate_with_mediapipe(audio_path, avatar_path, output_path)
        
        # Method 3: Simple video-audio merge (fallback)
        else:
            return self._generate_simple_merge(audio_path, avatar_path, output_path)
    
    def _check_wav2lip_available(self) -> bool:
        """Check if Wav2Lip is available"""
        try:
            # Check if wav2lip model files exist or if it's installed
            return os.path.exists("wav2lip") or os.path.exists("Wav2Lip")
        except:
            return False
    
    def _generate_with_wav2lip(self, audio_path: str, avatar_path: str, output_path: str) -> bool:
        """Generate lip sync using Wav2Lip"""
        try:
            # Wav2Lip command format
            cmd = [
                "python", "inference.py",
                "--checkpoint_path", "checkpoints/wav2lip_gan.pth",
                "--face", avatar_path,
                "--audio", audio_path,
                "--outfile", output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Wav2Lip error: {e}")
            return False
    
    def _generate_with_mediapipe(self, audio_path: str, avatar_path: str, output_path: str) -> bool:
        """Generate video-audio merge using MoviePy (basic synchronization)"""
        try:
            if not MOVIEPY_AVAILABLE:
                return False
            
            # Check if files exist
            if not os.path.exists(audio_path):
                print(f"Audio file not found: {audio_path}")
                return False
            if not os.path.exists(avatar_path):
                print(f"Avatar file not found: {avatar_path}")
                return False
            
            # Load avatar video/image
            if avatar_path.endswith(('.mp4', '.avi', '.mov')):
                avatar_clip = VideoFileClip(avatar_path)
            else:
                # If it's an image, create a video from it
                from moviepy.editor import ImageClip
                # Get audio duration first to set image duration
                temp_audio = AudioFileClip(audio_path)
                audio_duration = temp_audio.duration
                temp_audio.close()
                avatar_clip = ImageClip(avatar_path, duration=audio_duration)
            
            # Load audio
            audio_clip = AudioFileClip(audio_path)
            
            # Set video duration to match audio (loop if video is shorter)
            if avatar_clip.duration < audio_clip.duration:
                avatar_clip = avatar_clip.loop(duration=audio_clip.duration)
            else:
                avatar_clip = avatar_clip.set_duration(audio_clip.duration)
            
            # Create video WITHOUT audio track - audio will play separately via st.audio
            # Just use the video clip without adding audio
            final_clip = avatar_clip
            
            # Write output with error handling (no audio)
            try:
                final_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio=False,  # No audio in video file
                    fps=24,
                    verbose=False,
                    logger=None  # Suppress moviepy logs
                )
            except Exception as write_error:
                print(f"Video write error: {write_error}")
                raise
            
            # Cleanup
            avatar_clip.close()
            audio_clip.close()
            final_clip.close()
            
            return True
        except Exception as e:
            print(f"Video-audio merge error: {e}")
            return False
    
    def _generate_simple_merge(self, audio_path: str, avatar_path: str, output_path: str) -> bool:
        """Simple fallback: merge video/image with audio"""
        try:
            if not MOVIEPY_AVAILABLE:
                return False
            
            # Check if files exist
            if not os.path.exists(audio_path):
                print(f"Audio file not found: {audio_path}")
                return False
            if not os.path.exists(avatar_path):
                print(f"Avatar file not found: {avatar_path}")
                return False
            
            # Load audio first to get duration
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            
            # Load avatar
            if avatar_path.endswith(('.mp4', '.avi', '.mov')):
                video_clip = VideoFileClip(avatar_path)
            else:
                from moviepy.editor import ImageClip
                # ImageClip needs duration parameter
                video_clip = ImageClip(avatar_path, duration=audio_duration)
            
            # Set duration - loop if video is shorter than audio
            if video_clip.duration < audio_duration:
                video_clip = video_clip.loop(duration=audio_duration)
            else:
                video_clip = video_clip.set_duration(audio_duration)
            
            # Create video WITHOUT audio track - audio plays separately
            # Just use video clip without adding audio
            final_clip = video_clip
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio=False,  # No audio in video file
                verbose=False,
                logger=None
            )
            
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            
            return True
        except Exception as e:
            print(f"Simple merge error: {e}")
            return False


class ExpressionAnimator:
    """Generate expressive animations based on text sentiment and intent"""
    
    # Enhanced expression mappings with more keywords and emotional cues
    EXPRESSIONS = {
        "happy": ["smile", "joy", "excited", "great", "wonderful", "amazing", "excellent", 
                 "fantastic", "delighted", "pleased", "happy", "glad", "wonderful", 
                 "brilliant", "perfect", "awesome", "love", "enjoy", "celebrate"],
        "sad": ["sad", "sorry", "unfortunately", "regret", "disappointed", "sorrow", 
               "apologize", "apology", "unfortunately", "sadly", "regretful", "upset"],
        "surprised": ["wow", "really", "incredible", "unbelievable", "amazing", "surprised",
                     "astonishing", "remarkable", "impressive", "unexpected", "shocking"],
        "thinking": ["let me think", "hmm", "consider", "analyze", "thinking", "ponder",
                   "reflect", "contemplate", "examine", "evaluate", "assess"],
        "confident": ["certain", "sure", "definitely", "absolutely", "confident", "clear",
                     "obvious", "evident", "guaranteed", "assured"],
        "neutral": []  # Default
    }
    
    # Emotional intensity indicators
    INTENSITY_WORDS = {
        "very": 2, "extremely": 3, "really": 2, "quite": 1.5, "so": 1.5,
        "incredibly": 3, "absolutely": 2, "totally": 2
    }
    
    def detect_expression(self, text: str, use_ai: bool = False, ai_model=None) -> str:
        """
        Detect expression from text with enhanced analysis
        
        Args:
            text: Text to analyze
            use_ai: Use AI model for better emotion detection
            ai_model: Optional AI model for emotion analysis
            
        Returns:
            str: Detected expression
        """
        if use_ai and ai_model:
            return self._detect_with_ai(text, ai_model)
        
        text_lower = text.lower()
        
        # Score each expression
        expression_scores = {}
        for expression, keywords in self.EXPRESSIONS.items():
            if expression == "neutral":
                continue
            score = 0
            for keyword in keywords:
                count = text_lower.count(keyword)
                # Check for intensity modifiers
                for intensity_word, multiplier in self.INTENSITY_WORDS.items():
                    if f"{intensity_word} {keyword}" in text_lower:
                        count *= multiplier
                score += count
            if score > 0:
                expression_scores[expression] = score
        
        # Return expression with highest score, or neutral
        if expression_scores:
            return max(expression_scores, key=expression_scores.get)
        
        return "neutral"
    
    def _detect_with_ai(self, text: str, ai_model) -> str:
        """Use AI model to detect emotion more accurately"""
        try:
            prompt = f"""Analyze the emotional tone of this text and respond with ONLY one word from this list: happy, sad, surprised, thinking, confident, neutral.

Text: "{text}"

Respond with only the emotion word:"""
            
            response = ai_model.generate_content(prompt)
            emotion = response.text.strip().lower()
            
            # Validate response
            valid_emotions = ["happy", "sad", "surprised", "thinking", "confident", "neutral"]
            if emotion in valid_emotions:
                return emotion
            
            # Fallback to keyword detection
            return self.detect_expression(text, use_ai=False)
        except:
            # Fallback to keyword detection
            return self.detect_expression(text, use_ai=False)
    
    def get_expression_video_path(self, expression: str, base_path: str = "girl.gif.mp4") -> str:
        """Get path to expression-specific video"""
        # If you have multiple videos for different expressions
        expression_map = {
            "happy": "avatar_happy.mp4",
            "sad": "avatar_sad.mp4",
            "surprised": "avatar_surprised.mp4",
            "thinking": "avatar_thinking.mp4",
            "neutral": base_path
        }
        
        expression_file = expression_map.get(expression, base_path)
        
        if os.path.exists(expression_file):
            return expression_file
        
        return base_path  # Fallback to default


def create_lip_sync_video(audio_file: str, avatar_file: str, output_file: str = "lip_sync_output.mp4", 
                         use_api: bool = False, api_provider: str = "heygen", 
                         api_key: str = None, avatar_id: str = None) -> str:
    """
    Main function to create lip-synced video
    
    Args:
        audio_file: Path to audio file
        avatar_file: Path to avatar image/video
        output_file: Output file path
        use_api: Whether to use API for generation
        api_provider: API provider ("heygen", "d-id", "synthesia", "elai")
        api_key: API key for the provider
        avatar_id: Avatar ID for the provider
        
    Returns:
        str: Path to output file or None if failed
    """
    # Try API first if enabled
    if use_api and api_key:
        try:
            from video_api_alternatives import VideoGenerationAPIs
            
            if api_provider == "d-id":
                result = VideoGenerationAPIs.generate_with_did(audio_file, output_file, api_key, avatar_id)
            elif api_provider == "synthesia":
                result = VideoGenerationAPIs.generate_with_synthesia(audio_file, output_file, api_key, avatar_id)
            elif api_provider == "elai":
                result = VideoGenerationAPIs.generate_with_elai(audio_file, output_file, api_key, avatar_id)
            else:  # Default to HeyGen
                result = VideoGenerationAPIs.generate_with_heygen(audio_file, output_file, api_key, avatar_id)
            
            if result:
                return result
        except ImportError:
            # Fallback to local HeyGen implementation
            result = generate_with_heygen_api(audio_file, output_file, api_key, avatar_id)
            if result:
                return result
    
    # Fallback to local generation
    generator = LipSyncGenerator()
    
    if generator.generate_lip_sync_video(audio_file, avatar_file, output_file):
        return output_file
    
    return None


def generate_with_heygen_api(audio_file: str, output_file: str, api_key: str, avatar_id: str = None) -> Optional[str]:
    """
    Generate video using HeyGen API
    
    Args:
        audio_file: Path to audio file
        output_file: Output file path
        api_key: HeyGen API key
        avatar_id: HeyGen avatar ID (optional, uses default if not provided)
        
    Returns:
        str: Path to output file or None if failed
    """
    try:
        # HeyGen API endpoint
        api_url = "https://api.heygen.com/v1/video.generate"
        
        # Read audio file
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
        
        # Prepare request
        headers = {
            "X-API-KEY": api_key
        }
        
        # Prepare form data
        files = {
            "audio": ("audio.mp3", audio_data, "audio/mpeg")
        }
        
        data = {}
        if avatar_id:
            data["avatar_id"] = avatar_id
        
        # Make API request
        response = requests.post(api_url, headers=headers, files=files, data=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            video_url = result.get("data", {}).get("video_url")
            
            if video_url:
                # Download the generated video
                video_response = requests.get(video_url, timeout=120)
                if video_response.status_code == 200:
                    with open(output_file, 'wb') as f:
                        f.write(video_response.content)
                    return output_file
        else:
            print(f"HeyGen API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"HeyGen API generation failed: {str(e)}")
        return None


def get_expression_for_text(text: str, ai_model=None) -> str:
    """
    Get appropriate expression video for text with enhanced emotion detection
    
    Args:
        text: Text to analyze
        ai_model: Optional AI model for better emotion detection
        
    Returns:
        str: Path to expression video
    """
    animator = ExpressionAnimator()
    use_ai = ai_model is not None
    expression = animator.detect_expression(text, use_ai=use_ai, ai_model=ai_model)
    return animator.get_expression_video_path(expression)


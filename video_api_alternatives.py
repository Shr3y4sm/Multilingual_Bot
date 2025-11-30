"""
Free Video Generation API Alternatives
Provides implementations for various free text-to-video APIs with audio
"""

import os
import requests
import time
from typing import Optional
import json

class VideoGenerationAPIs:
    """Collection of free video generation API implementations"""
    
    @staticmethod
    def generate_with_did(audio_file: str, output_file: str, api_key: str, avatar_id: str = None, text_content: str = None) -> Optional[str]:
        """
        Generate video using D-ID API (Free tier: 20 credits/month)
        https://www.d-id.com/
        
        Args:
            audio_file: Path to audio file (for reference, D-ID uses text input)
            output_file: Output file path
            api_key: D-ID API key
            avatar_id: D-ID avatar ID (optional)
            text_content: Text content to speak (required for D-ID)
            
        Returns:
            str: Path to output file or None if failed
        """
        try:
            # D-ID requires text input, not audio file
            if not text_content:
                print("D-ID API requires text content")
                return None
            
            # D-ID API endpoint
            api_url = "https://api.d-id.com/talks"
            
            # Prepare request headers
            headers = {
                "Authorization": f"Basic {api_key}",
                "Content-Type": "application/json"
            }
            
            # Create talk request with text-to-speech
            payload = {
                "source_url": avatar_id or "https://d-id-public-bucket.s3.amazonaws.com/alice.jpg",
                "script": {
                    "type": "text",
                    "input": text_content,
                    "provider": {
                        "type": "microsoft",
                        "voice_id": "en-US-JennyNeural"
                    }
                },
                "config": {
                    "fluent": True,
                    "pad_audio": 0.0
                }
            }
            
            # Make API request
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 201:
                result = response.json()
                talk_id = result.get("id")
                
                # Poll for completion
                status_url = f"https://api.d-id.com/talks/{talk_id}"
                for _ in range(60):  # Wait up to 5 minutes
                    time.sleep(5)
                    status_response = requests.get(status_url, headers=headers)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get("status")
                        
                        if status == "done":
                            video_url = status_data.get("result_url")
                            if video_url:
                                # Download video
                                video_response = requests.get(video_url, timeout=120)
                                if video_response.status_code == 200:
                                    with open(output_file, 'wb') as f:
                                        f.write(video_response.content)
                                    return output_file
                        elif status == "error":
                            error_msg = status_data.get("error", {}).get("description", "Unknown error")
                            print(f"D-ID API error: {error_msg}")
                            return None
            else:
                print(f"D-ID API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"D-ID API generation failed: {str(e)}")
            return None
    
    @staticmethod
    def generate_with_synthesia(audio_file: str, output_file: str, api_key: str, avatar_id: str = None) -> Optional[str]:
        """
        Generate video using Synthesia API (Free tier: Limited)
        https://www.synthesia.io/
        
        Note: Synthesia primarily uses text input, not audio files directly
        """
        try:
            # Synthesia API endpoint
            api_url = "https://api.synthesia.io/v2/videos"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Synthesia uses text input, so you'd need to extract text from audio
            # This is a simplified example - actual implementation may vary
            payload = {
                "test": True,
                "input": [
                    {
                        "scriptText": "Your text here",  # Extract from audio or use TTS text
                        "avatar": avatar_id or "anna_costume1_cameraA",
                        "background": "off_white"
                    }
                ]
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                video_id = result.get("id")
                
                # Poll for completion
                status_url = f"https://api.synthesia.io/v2/videos/{video_id}"
                for _ in range(60):
                    time.sleep(5)
                    status_response = requests.get(status_url, headers=headers)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("status") == "complete":
                            video_url = status_data.get("download_url")
                            if video_url:
                                video_response = requests.get(video_url, timeout=120)
                                if video_response.status_code == 200:
                                    with open(output_file, 'wb') as f:
                                        f.write(video_response.content)
                                    return output_file
            else:
                print(f"Synthesia API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Synthesia API generation failed: {str(e)}")
            return None
    
    @staticmethod
    def generate_with_elai(audio_file: str, output_file: str, api_key: str, avatar_id: str = None) -> Optional[str]:
        """
        Generate video using Elai.io API (Free tier: 1 minute video)
        https://elai.io/
        """
        try:
            api_url = "https://api.elai.io/api/v1/videos"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Read audio file and convert to base64 or upload separately
            # Elai typically uses text input with TTS
            payload = {
                "template_id": avatar_id or "default",
                "script": "Your text here"  # Extract from audio
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                video_id = result.get("id")
                
                # Poll for completion
                status_url = f"https://api.elai.io/api/v1/videos/{video_id}"
                for _ in range(60):
                    time.sleep(5)
                    status_response = requests.get(status_url, headers=headers)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("status") == "completed":
                            video_url = status_data.get("download_url")
                            if video_url:
                                video_response = requests.get(video_url, timeout=120)
                                if video_response.status_code == 200:
                                    with open(output_file, 'wb') as f:
                                        f.write(video_response.content)
                                    return output_file
            else:
                print(f"Elai API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Elai API generation failed: {str(e)}")
            return None
    
    @staticmethod
    def generate_with_heygen(audio_file: str, output_file: str, api_key: str, avatar_id: str = None) -> Optional[str]:
        """
        Generate video using HeyGen API (Free tier available)
        https://www.heygen.com/
        """
        try:
            api_url = "https://api.heygen.com/v1/video.generate"
            
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            
            headers = {
                "X-API-KEY": api_key
            }
            
            files = {
                "audio": ("audio.mp3", audio_data, "audio/mpeg")
            }
            
            data = {}
            if avatar_id:
                data["avatar_id"] = avatar_id
            
            response = requests.post(api_url, headers=headers, files=files, data=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                video_url = result.get("data", {}).get("video_url")
                
                if video_url:
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


# Free tier comparison
FREE_TIER_INFO = {
    "d-id": {
        "name": "D-ID",
        "free_credits": "20 credits/month",
        "website": "https://www.d-id.com/",
        "api_docs": "https://docs.d-id.com/",
        "best_for": "Avatar lip sync with audio"
    },
    "heygen": {
        "name": "HeyGen",
        "free_credits": "Free tier available",
        "website": "https://www.heygen.com/",
        "api_docs": "https://docs.heygen.com/",
        "best_for": "Professional avatars with lip sync"
    },
    "synthesia": {
        "name": "Synthesia",
        "free_credits": "Limited free tier",
        "website": "https://www.synthesia.io/",
        "api_docs": "https://docs.synthesia.io/",
        "best_for": "Enterprise-grade video generation"
    },
    "elai": {
        "name": "Elai.io",
        "free_credits": "1 minute video free",
        "website": "https://elai.io/",
        "api_docs": "https://docs.elai.io/",
        "best_for": "Quick video generation"
    }
}


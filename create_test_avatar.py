"""
Quick script to create a simple test avatar video
This creates a basic animated placeholder for testing
"""

try:
    import numpy as np
    from moviepy.editor import ImageClip, CompositeVideoClip, TextClip
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    def create_simple_avatar(output_path="girl.gif.mp4", duration=5):
        """Create a simple animated avatar for testing"""
        
        # Create a simple colored circle as avatar
        width, height = 400, 400
        frames = []
        
        for i in range(30):  # 30 frames for smooth animation
            # Create image with gradient background
            img = Image.new('RGB', (width, height), color='lightblue')
            draw = ImageDraw.Draw(img)
            
            # Draw a simple face
            # Head (circle)
            head_size = 150
            head_x = width // 2
            head_y = height // 2 - 30
            draw.ellipse([head_x - head_size//2, head_y - head_size//2, 
                         head_x + head_size//2, head_y + head_size//2], 
                        fill='peachpuff', outline='black', width=2)
            
            # Eyes (animated blink)
            eye_y = head_y - 20
            if i % 20 < 2:  # Blink every 20 frames
                # Closed eyes
                draw.ellipse([head_x - 40, eye_y, head_x - 20, eye_y + 5], fill='black')
                draw.ellipse([head_x + 20, eye_y, head_x + 40, eye_y + 5], fill='black')
            else:
                # Open eyes
                draw.ellipse([head_x - 40, eye_y - 10, head_x - 20, eye_y + 10], fill='black')
                draw.ellipse([head_x + 20, eye_y - 10, head_x + 40, eye_y + 10], fill='black')
            
            # Mouth (simple smile, animated)
            mouth_y = head_y + 30
            smile_offset = int(5 * np.sin(i * 0.2))  # Animated smile
            draw.arc([head_x - 30, mouth_y - 15 + smile_offset, 
                     head_x + 30, mouth_y + 15 + smile_offset], 
                    start=0, end=180, fill='black', width=3)
            
            # Save frame
            frame_path = f"temp_frame_{i:03d}.png"
            img.save(frame_path)
            frames.append(frame_path)
        
        # Create video from frames
        clips = [ImageClip(frame).set_duration(duration/30) for frame in frames]
        video = CompositeVideoClip(clips).set_duration(duration)
        video.write_videofile(output_path, fps=6, codec='libx264', audio=False)
        
        # Cleanup temp files
        for frame in frames:
            if os.path.exists(frame):
                os.remove(frame)
        
        print(f"✅ Created test avatar: {output_path}")
        return output_path
    
    if __name__ == "__main__":
        print("Creating test avatar video...")
        create_simple_avatar()
        print("\nPlace this file in your project root as 'girl.gif.mp4'")
        print("Or rename it: girl.gif.mp4")
        
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Install required packages:")
    print("pip install moviepy pillow numpy")
except Exception as e:
    print(f"❌ Error creating avatar: {e}")


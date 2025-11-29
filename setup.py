"""
Setup script for Animated AI Translator
Run this to check if all dependencies are installed correctly
"""

import sys
import subprocess

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} is installed")
        return True
    except ImportError:
        print(f"❌ {package_name} is NOT installed")
        return False

def install_package(package_name):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package_name}")
        return False

def main():
    print("=" * 50)
    print("Animated AI Translator - Setup Check")
    print("=" * 50)
    print()
    
    required_packages = {
        "streamlit": "streamlit",
        "speechrecognition": "speech_recognition",
        "deep-translator": "deep_translator",
        "gtts": "gtts",
        "google-generativeai": "google.generativeai",
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        if not check_package(package_name, import_name):
            missing_packages.append(package_name)
    
    print()
    
    if missing_packages:
        print("=" * 50)
        print("Missing packages detected!")
        print("=" * 50)
        response = input(f"\nInstall missing packages? (y/n): ")
        
        if response.lower() == 'y':
            print("\nInstalling packages...")
            for package in missing_packages:
                install_package(package)
            print("\n✅ Setup complete!")
        else:
            print("\nPlease install missing packages manually:")
            print(f"pip install {' '.join(missing_packages)}")
    else:
        print("=" * 50)
        print("✅ All required packages are installed!")
        print("=" * 50)
    
    print("\nNext steps:")
    print("1. Set GEMINI_API_KEY environment variable")
    print("2. Run: streamlit run main.py")
    print()

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Automated Setup Script for Calling Agent System
Run this on new PC to install everything automatically
"""

import os
import sys
import subprocess
import platform
import urllib.request
import zipfile

def run_command(cmd, shell=True):
    """Run command and return success status"""
    try:
        result = subprocess.run(cmd, shell=shell, check=True, capture_output=True, text=True)
        print(f"✓ {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {cmd}")
        print(f"  Error: {e.stderr}")
        return False

def main():
    print("=" * 60)
    print("CALLING AGENT - AUTOMATED SETUP")
    print("=" * 60)
    
    # Get current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pc_agent_dir = os.path.join(script_dir, "pc_agent")
    
    # Detect OS
    os_type = platform.system()
    print(f"\n[1/6] Detected OS: {os_type}")
    
    # Check Python version
    print("\n[2/6] Checking Python version...")
    py_version = sys.version_info
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 8):
        print(f"✗ Python 3.8+ required. Current: {py_version.major}.{py_version.minor}")
        sys.exit(1)
    print(f"✓ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # Install Python packages
    print("\n[3/6] Installing Python packages...")
    packages = [
        "openai",
        "sounddevice",
        "soundfile",
        "numpy",
        "openpyxl",
        "edge-tts",
        "pyaudio",
        "speechrecognition",
        "adb-shell",
        "python-dotenv"
    ]
    
    for pkg in packages:
        print(f"  Installing {pkg}...")
        run_command(f"{sys.executable} -m pip install {pkg}")
    
    # Install ADB
    print("\n[4/6] Installing ADB (Android Debug Bridge)...")
    if os_type == "Linux":
        run_command("sudo apt update && sudo apt install -y adb")
    elif os_type == "Darwin":  # macOS
        if run_command("which brew", shell=True):
            run_command("brew install android-platform-tools")
        else:
            print("  ⚠ Homebrew not found. Install ADB manually from:")
            print("    https://developer.android.com/studio/releases/platform-tools")
    elif os_type == "Windows":
        adb_dir = os.path.join(script_dir, "platform-tools")
        adb_exe = os.path.join(adb_dir, "adb.exe")
        
        if os.path.exists(adb_exe):
            print(f"  ✓ ADB already installed at {adb_dir}")
        else:
            print("  Downloading ADB Platform Tools for Windows...")
            url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
            zip_path = os.path.join(script_dir, "platform-tools.zip")
            
            try:
                urllib.request.urlretrieve(url, zip_path)
                print("  ✓ Downloaded")
                
                print("  Extracting...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(script_dir)
                print(f"  ✓ Extracted to {adb_dir}")
                
                os.remove(zip_path)
                
                # Add to PATH for current session
                os.environ["PATH"] = adb_dir + os.pathsep + os.environ["PATH"]
                print("  ✓ ADB added to PATH (current session)")
                print(f"  ⚠ Add to Windows PATH permanently: {adb_dir}")
            except Exception as e:
                print(f"  ✗ Failed to download/extract ADB: {e}")
                print("    Download manually from: https://developer.android.com/studio/releases/platform-tools")
    
    # Setup credentials
    print("\n[5/6] Setting up credentials...")
    env_file = os.path.join(pc_agent_dir, ".env")
    
    if os.path.exists(env_file):
        print(f"  ✓ Credentials file already exists: {env_file}")
        with open(env_file, 'r') as f:
            print(f"  Current content:\n{f.read()}")
    else:
        print(f"  Creating credentials file: {env_file}")
        print("\n  Enter your OpenAI API Key:")
        api_key = input("  > ").strip()
        
        with open(env_file, 'w') as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
        print(f"  ✓ Credentials saved to {env_file}")
    
    # Verify ADB connection
    print("\n[6/6] Verifying ADB connection...")
    print("  Make sure:")
    print("    1. USB debugging enabled on Android phone")
    print("    2. Phone connected via USB")
    print("    3. Accept 'Allow USB debugging' prompt on phone")
    input("\n  Press ENTER when ready...")
    
    if run_command("adb devices"):
        print("  ✓ ADB working")
    else:
        print("  ⚠ ADB not found or not working")
    
    # Final instructions
    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print(f"\nTo run the agent:")
    print(f"  cd {pc_agent_dir}")
    print(f"  python main.py")
    print("\nTo install Android app:")
    print(f"  adb install app/build/outputs/apk/debug/app-debug.apk")
    print("=" * 60)

if __name__ == "__main__":
    main()

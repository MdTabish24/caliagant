"""
Build script to create standalone .exe for Calling Agent
Run: python build_exe.py
"""

import os
import sys
import subprocess

def main():
    print("=" * 60)
    print("Building Calling Agent .exe")
    print("=" * 60)
    
    # Install PyInstaller if not present
    print("\n[1/3] Installing PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Get paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gui_script = os.path.join(script_dir, "gui_app.py")
    
    # Build command
    print("\n[2/3] Building executable...")
    cmd = [
        "pyinstaller",
        "--onefile",  # Single exe file
        "--windowed",  # No console window
        "--name=CallingAgent",
        "--icon=NONE",
        f"--add-data={script_dir};.",  # Include all files
        "--hidden-import=openpyxl",
        "--hidden-import=sounddevice",
        "--hidden-import=soundfile",
        "--hidden-import=edge_tts",
        "--hidden-import=speech_recognition",
        "--hidden-import=openai",
        gui_script
    ]
    
    subprocess.run(cmd, check=True)
    
    print("\n[3/3] Build complete!")
    print(f"\nExecutable created at: {os.path.join(script_dir, 'dist', 'CallingAgent.exe')}")
    print("\nTo distribute:")
    print("  1. Copy the entire 'pc_agent' folder")
    print("  2. Replace gui_app.py with CallingAgent.exe")
    print("  3. User just double-clicks CallingAgent.exe to run")
    print("=" * 60)

if __name__ == "__main__":
    main()

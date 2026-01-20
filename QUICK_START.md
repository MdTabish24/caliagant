# 🚀 Quick Start Guide - Calling Agent

## New PC Setup (One Command)

```bash
git clone https://github.com/MdTabish24/caliagant.git
cd caliagant/pc_agent
SETUP_COMPLETE.bat
```

## What This Does:
1. ✅ Installs all Python dependencies
2. ✅ Builds the EXE file
3. ✅ Sets up folders
4. ✅ Copies ADB files

## After Setup:

### 1. Add OpenAI API Key
```bash
# Copy example file
copy api_key.txt.example api_key.txt

# Edit api_key.txt and add your key
notepad api_key.txt
```

### 2. Run the App
```bash
cd dist
CallingAgent.exe
```

## Usage:

### Audio Only Mode:
1. Select audio file (Browse button)
2. Choose "Audio Only" mode
3. Connect phone via USB (USB debugging ON)
4. Click "Start Agent"
5. Start calling from phone app

### AI Agent Mode:
1. Select audio file (Browse button)
2. Choose "AI Agent" mode
3. Connect phone via USB (USB debugging ON)
4. Click "Start Agent"
5. Start calling from phone app
6. AI will have conversation after audio plays

## Results:

Excel files will be saved in: `dist/results/`
- `results.xlsx` - Call results with conversation
- `audio_tracking.xlsx` - Audio listen time tracking (Red/Yellow/Green)

## Troubleshooting:

### Phone not detected?
- Enable USB Debugging in Developer Options
- Accept "Allow USB Debugging" popup on phone
- Try different USB cable/port

### Dependencies error?
```bash
pip install -r requirements.txt
```

### Rebuild EXE:
```bash
rebuild_exe.bat
```

## Requirements:
- Python 3.8+
- Windows 10/11
- Android phone with USB debugging
- OpenAI API key (for AI mode)

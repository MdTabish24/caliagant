# 🤖 AI Calling Agent - PC Side

## Ye Kya Karta Hai?
- Phone se numbers pe call karta hai
- User ki awaaz sunta hai (Speech-to-Text)
- Local LLM (Ollama) se reply generate karta hai
- PC speaker se bolta hai (jo phone mic se call me jaata hai)
- Result Excel me save karta hai

## 📋 Requirements

### PC pe:
- Windows 10/11
- Python 3.8+
- 8GB+ RAM (LLM ke liye)
- Speakers (loud!)

### Phone pe:
- Android 10+
- USB Debugging ON
- CallingAgent app installed

## 🚀 Setup (Ek Baar Karna Hai)

### Step 1: Python Dependencies
```bash
# Double-click karo:
install_dependencies.bat

# Ya manually:
pip install ollama pyttsx3 edge-tts openpyxl watchdog
```

### Step 2: Ollama Install
```bash
# Double-click karo:
install_ollama.bat

# Ya manually:
# 1. Download from https://ollama.ai
# 2. Install karo
# 3. Run:
ollama pull llama3.2
ollama serve
```

### Step 3: Phone Setup
1. USB cable se connect karo
2. Settings → Developer Options → USB Debugging ON
3. CallingAgent app install karo
4. App me permissions allow karo

### Step 4: Test Setup
```bash
python test_setup.py
```

## 📞 Kaise Use Karna Hai

### 1. Excel me Numbers Daalo
`numbers.xlsx` file me phone numbers daalo (first column)

### 2. Phone Connect Karo
USB se connect karo, USB Debugging ON

### 3. Agent Start Karo
```bash
# Double-click:
run_agent.bat

# Ya:
python main.py
```

### 4. Kya Hoga:
1. Phone pe call lagegi
2. User pick karega
3. Speakerphone ON hoga
4. User bolega → Phone text me convert karega
5. PC pe LLM response generate karega
6. PC speaker se bolega → Phone mic se call me jaayega
7. User sunke reply karega
8. Loop chalega...
9. Call end → Result Excel me save

## ⚙️ Configuration

`config.py` me settings change kar sakte ho:

```python
# LLM Model
LLM_MODEL = "llama3.2"  # ya "mistral", "phi3"

# Hindi voice
TTS_VOICE = "hi-IN-SwaraNeural"

# System prompt (LLM ko kya bolna hai)
SYSTEM_PROMPT = "..."
```

## 📁 Files

```
pc_agent/
├── main.py              # Main agent
├── adb_controller.py    # Phone communication
├── llm_engine.py        # Ollama LLM
├── tts_engine.py        # Text-to-Speech
├── excel_handler.py     # Excel read/write
├── config.py            # Settings
├── numbers.xlsx         # Input numbers
├── results.xlsx         # Output results
├── test_setup.py        # Setup tester
├── install_dependencies.bat
├── install_ollama.bat
└── run_agent.bat
```

## ❓ Troubleshooting

### Phone not connected
- USB cable check karo
- USB Debugging ON karo
- "Allow USB Debugging" popup pe OK karo

### Ollama not working
- `ollama serve` run karo
- `ollama pull llama3.2` run karo

### Audio not playing
- PC volume check karo
- Speakers ON karo

### Speech not recognized
- Phone mic permission check karo
- Speakerphone ON hona chahiye

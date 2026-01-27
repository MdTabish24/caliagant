# 📞 Calling Agent App

Auto-dialer Android app jo Excel se numbers read karke automatically call karta hai aur audio play karta hai.

## Features
- Excel file (.xlsx/.xls) se phone numbers read kare
- First column se automatically numbers extract kare
- Background me chale (Foreground Service)
- Call connect hone pe audio recording play kare
- Ek ke baad ek automatically call kare
- **WhatsApp Auto Message** - Call ke baad automatically WhatsApp message bheje
- **Media Support** - WhatsApp me image/file attach karke bheje
- AI conversation mode (optional)
- Excel reports with color coding

## 🚀 Quick Setup (New PC)

### Windows:
```bash
git clone https://github.com/TechStartUpTS/caliagant.git
cd caliagant
setup.bat
```

Ye automatically:
1. ✅ Python dependencies install karega
2. ✅ ADB download karega
3. ✅ API key setup karega
4. ✅ Portable EXE build karega

### Manual Setup:

1. **Clone repo:**
```bash
git clone https://github.com/TechStartUpTS/caliagant.git
cd caliagant/pc_agent
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Add API key:**
```bash
echo "your-openai-api-key" > api_key.txt
```

4. **Build EXE:**
```bash
build_portable.bat
```

5. **Run:**
```bash
cd dist
CallingAgent.exe
```

## Permissions Required
- CALL_PHONE - Calls karne ke liye
- READ_PHONE_STATE - Call state detect karne ke liye
- Storage - Excel file read karne ke liye
- Overlay - Background me kaam karne ke liye
- **WhatsApp installed** - Auto message feature ke liye

## Usage
1. App open karo
2. Permissions allow karo
3. Excel file select karo (first column = phone numbers)
4. **WhatsApp Auto Message (Optional):**
   - Toggle ON karo
   - Message type karo
   - Media file select karo (optional)
5. "START CALLING" dabao
6. App minimize hoke background me chalegi
7. **Call ke baad automatically WhatsApp open hoga** with pre-filled message

## Excel Format
| Phone Number | Name (optional) | Other columns... |
|--------------|-----------------|------------------|
| 9876543210   | John            | ...              |
| 8765432109   | Jane            | ...              |

First column HAMESHA phone number hona chahiye!

## 📊 Reports

Reports `pc_agent/reports/` me save hote hain:

### audio_tracking.xlsx
- 🔴 RED: <20% listened (NOT INTERESTED)
- 🟡 YELLOW: 20-60% listened (PARTIAL)
- 🟢 GREEN: >60% listened (INTERESTED)

### results.xlsx
- AI conversation analysis
- Interest level
- Summary

## Note
⚠️ Ye app sirf legitimate business purposes ke liye use karo. Spam calling illegal hai!

"""
AI Calling Agent - Configuration
Clean HTTP-based system with GPT-5 Nano
"""
import os
import random
import logging

# ===========================================
# Logging Setup
# ===========================================
LOG_LEVEL = logging.DEBUG  # DEBUG for detailed logs
LOG_FORMAT = "%(asctime)s | %(levelname)-5s | %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"

# Setup logging
logging.basicConfig(
    level=LOG_LEVEL, 
    format=LOG_FORMAT, 
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler("calling_agent.log", encoding="utf-8")  # File output
    ]
)
logger = logging.getLogger("CallingAgent")

# ===========================================
# HTTP Server Settings (Phone connects to PC)
# ===========================================
HTTP_HOST = "0.0.0.0"  # Listen on all interfaces
HTTP_PORT = 8765

# ===========================================
# OpenAI Settings - GPT-5 Nano (Cheapest)
# ===========================================
def get_api_key():
    """Get API key from env or file"""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    
    key_file = os.path.join(os.path.dirname(__file__), "api_key.txt")
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            return f.read().strip()
    
    return ""

OPENAI_API_KEY = get_api_key()
OPENAI_MODEL = "gpt-4.1-nano"  # CHEAPEST: $0.10/M input, $0.40/M output

# System prompt for natural Hindi conversation - 2-3 sentences max
SYSTEM_PROMPT = """Tu Universal Skill Development Centre ka telecaller hai. Natural Hindi me baat kar jaise ek normal insaan baat karta hai.

=== CENTRE INFO ===
NAME: Universal Skill Development Centre
ADDRESS: Gaibi Nagar Road, Kacheri Pada, Near Municipal School No. 62, Gaibi Nagar, Bhiwandi
TIMING: Monday to Saturday, 9 AM to 6 PM

=== COURSES ===
- MS Office
- Advance Excel  
- Tally Prime GST
- Graphic Designing
- Data Analytics
- English Speaking

=== OFFER ===
40% Discount - Sirf Rs 3000 me koi bhi course!

=== GARBLED SPEECH HANDLING ===
Phone audio distorted hoti hai, toh user ke words galat transcribe ho sakte hain:
- "गवस/गगवस/कोर्सेज/कौर्स" = COURSES
- "विजिट/विकसित/पाड़ूगा" = VISIT karna
- "प्राइज/प्राइस/प्राइज्या" = PRICE/FEES
- "टाइमिंग/टाइम" = TIMING
- "एड्रेस/पता" = ADDRESS
- "कब/कितना/कितने" = time/duration related

Agar user ka message courses, fees, timing, visit ya centre ke baare mein lag raha hai, toh SAMAJH KE relevant jawab de!

=== RESPONSE RULES ===
1. Sirf 1-2 SHORT sentence me jawab de (max 15 words)
2. Pure Hindi/Hinglish me bol, natural tone rakho
3. Course related questions ka seedha jawab do
4. Agar samajh nahi aaya but course related lag raha hai, toh courses list bata de
5. Sirf COMPLETELY unrelated questions pe bolo: "Maaf kijiye..."
6. User ko centre visit karne ke liye encourage karo

=== EXAMPLES ===
User: "कौन कौन से गवस मिलते हैं?" (garbled: courses)
AI: "Humare paas MS Office, Excel, Tally, Graphic Designing, Data Analytics aur English Speaking courses hain. Sirf 3000 me!"

User: "कभ तक विजिट करना पाड़ूगा" (garbled: kab visit kar sakta)
AI: "Aap Monday se Saturday, 9 se 6 baje tak aa sakte hain. Kab aayenge aap?"

User: "क्या प्राइज्या कूर्सका?" (garbled: price/fees)
AI: "Abhi 40% discount chal raha hai, sirf 3000 rupaye. Bahut accha offer hai."

User: Random irrelevant question
AI: "Maaf kijiye mujhe iske baare me pata nahi. Kya aap kisi course me interested hain?"

=== IMPORTANT ===
- Jaise normal telecaller baat karta hai waisa natural tone rakho
- PEHLE SAMAJHNE KI KOSHISH KARO ki user kya pooch raha hai
- Har jawab me try karo user ko centre visit ke liye convince karo
- Zyada lambi explanation mat do, short aur effective raho"""

# ===========================================
# TTS Settings - Hindi Male Voice
# ===========================================
TTS_VOICE = "hi-IN-MadhurNeural"  # Hindi Male voice
TTS_RATE = "+25%"  # Faster
TTS_PITCH = "+0Hz"

# ===========================================
# Audio Files
# ===========================================
OPENING_MP3 = os.path.join(os.path.dirname(__file__), "opening.mp3")

# ===========================================
# Call Settings
# ===========================================
SILENCE_TIMEOUT = 20  # Seconds - after opening.mp3 finishes
MAX_CALL_DURATION = 180  # 3 minutes max

SILENCE_MESSAGE = "Aapki awaaz nahi aa rahi. Kripya centre visit karein discount ke liye. Dhanyavaad!"

# ===========================================
# Opening Pitches (for TTS if no MP3)
# ===========================================
OPENING_PITCHES = [
    "Hello sir, Universal Skill Centre se bol raha hoon. Humare yahan 40 percent discount chal raha hai courses pe. Kya aap interested ho?",
    "Hello sir, aaj kal bina skill ke job milna mushkil hai. Humare centre me practical courses sirf 3000 me mil rahe hain. Kya aap visit karenge?",
]

def get_random_pitch():
    return random.choice(OPENING_PITCHES)

# ===========================================
# Excel Settings
# ===========================================
# Save in pc_agent/reports folder
import sys

def get_base_path():
    """Get base path - works for both script and exe"""
    if getattr(sys, 'frozen', False):
        # Running as exe
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(__file__)

RESULTS_DIR = os.path.join(get_base_path(), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
OUTPUT_EXCEL = os.path.join(RESULTS_DIR, "results.xlsx")

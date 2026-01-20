"""
AI Calling Agent - USB/ADB Based Detection

Flow:
1. Phone app se Excel select karo aur calling start karo
2. PC USB ke through call state detect karta hai (ADB)
3. RINGING -> PICKUP -> Audio play -> AI conversation
4. Call end -> Ready for next

Phone USB se connected hona chahiye with USB Debugging ON

Run: python main.py
"""
import time
import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from enum import Enum
from config import (
    logger, SILENCE_TIMEOUT, SILENCE_MESSAGE,
    MAX_CALL_DURATION, get_random_pitch
)
from tts_engine import TTSEngine
from excel_handler import ExcelHandler
from audio_tracker import AudioTracker


# ============================================================
# USB/ADB CALL DETECTOR
# ============================================================

class USBCallState(Enum):
    IDLE = "idle"
    DIALING = "dialing"      # Call dial ho rahi hai
    RINGING = "ringing"      # Samne wale ko ring ja rahi hai
    ACTIVE = "active"        # Samne wale ne pick kar liya


class ADBCallDetector:
    """USB/ADB based call detection - Phone USB se connected hona chahiye"""
    
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.current_state = USBCallState.IDLE
        self.current_number = ""
        self.ring_count = 0
        self.ring_start_time = None
        
        # Callbacks
        self.on_ringing = None
        self.on_pickup = None
        self.on_hangup = None
        
        self._lock = threading.Lock()
        self._last_state = None
        
        # Find ADB path
        self.adb_path = self._find_adb()
    
    def _find_adb(self):
        """Find ADB executable - check bundled first, then system"""
        import shutil
        import sys
        
        # Check bundled adb.exe (PyInstaller extracts to _MEIPASS)
        if getattr(sys, 'frozen', False):
            # Running as exe - check temp extraction folder
            bundle_dir = sys._MEIPASS
            bundled_adb = os.path.join(bundle_dir, "adb.exe")
            if os.path.exists(bundled_adb):
                logger.info(f"✅ Using bundled ADB: {bundled_adb}")
                return bundled_adb
            
            # Also check exe directory
            exe_dir = os.path.dirname(sys.executable)
            bundled_adb = os.path.join(exe_dir, "adb.exe")
            if os.path.exists(bundled_adb):
                logger.info(f"✅ Using bundled ADB: {bundled_adb}")
                return bundled_adb
        else:
            # Running as script - check script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            bundled_adb = os.path.join(script_dir, "adb.exe")
            if os.path.exists(bundled_adb):
                logger.info(f"✅ Using bundled ADB: {bundled_adb}")
                return bundled_adb
        
        # Check if adb is in PATH
        adb_in_path = shutil.which("adb")
        if adb_in_path:
            logger.info(f"✅ ADB found in PATH: {adb_in_path}")
            return "adb"
        
        # Common ADB locations on Windows
        possible_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
            os.path.expanduser(r"~\AppData\Local\Android\Sdk\platform-tools\adb.exe"),
            r"C:\Android\sdk\platform-tools\adb.exe",
            r"C:\Program Files\Android\Android Studio\platform-tools\adb.exe",
            r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ ADB found: {path}")
                return path
        
        logger.error("❌ ADB not found anywhere!")
        return None
    
    def check_adb(self):
        """Check if ADB is available and phone is connected"""
        if not self.adb_path:
            logger.error("❌ ADB not found!")
            return False
        
        try:
            result = subprocess.run(
                [self.adb_path, "devices"], 
                capture_output=True, 
                text=True, 
                timeout=10,  # Increased timeout
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:
                if '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    logger.info(f"✅ Phone connected: {device_id}")
                    return True
            logger.error("❌ No phone connected via USB")
            return False
        except FileNotFoundError:
            logger.error("❌ ADB not found!")
            return False
        except Exception as e:
            logger.error(f"❌ ADB error: {e}")
            return False
    
    def get_call_state(self):
        """Get current call state from phone via ADB"""
        if not self.adb_path:
            return USBCallState.IDLE
        
        try:
            result = subprocess.run(
                [self.adb_path, "shell", "dumpsys", "telephony.registry"],
                capture_output=True,
                text=True,
                timeout=5,  # Increased timeout
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            output = result.stdout
            
            # Parse states - get pairs of mCallState and mForegroundCallState
            lines = output.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('mCallState='):
                    try:
                        call_state = int(line.split('=')[1].strip())
                        
                        # If this SIM has active call (mCallState != 0), check its foreground state
                        if call_state != 0:
                            # Find corresponding mForegroundCallState
                            foreground_state = 0
                            for j in range(i+1, min(i+10, len(lines))):
                                if lines[j].strip().startswith('mForegroundCallState='):
                                    foreground_state = int(lines[j].strip().split('=')[1].strip())
                                    break
                            
                            # Determine state based on this active SIM
                            if call_state == 1:
                                return USBCallState.RINGING  # Incoming call ringing
                            elif call_state == 2:
                                if foreground_state == 4:
                                    return USBCallState.RINGING  # Outgoing - samne wale ko ring
                                elif foreground_state == 1:
                                    return USBCallState.ACTIVE  # Call picked up!
                                else:
                                    return USBCallState.DIALING
                    except:
                        pass
            
            return USBCallState.IDLE
            
        except Exception as e:
            logger.error(f"get_call_state error: {e}")
            return USBCallState.IDLE
    
    def get_call_number(self):
        """Get current call number from phone file"""
        if not self.adb_path:
            logger.warning("ADB path not found")
            return ""
        
        try:
            # Read from file that app saves
            result = subprocess.run(
                [self.adb_path, "shell", "cat", "/sdcard/Android/data/com.callingagent.app/files/current_number.txt"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            number = result.stdout.strip()
            logger.info(f"📱 Read from file: '{number}' (len={len(number)})")
            if number and len(number) > 5:  # Valid number
                logger.info(f"✅ Valid number found: {number}")
                return number
            else:
                logger.warning(f"❌ Invalid number from file: '{number}'")
        except Exception as e:
            logger.error(f"File read error: {e}")
        
        # Fallback: try telephony.registry (for incoming calls)
        try:
            result = subprocess.run(
                [self.adb_path, "shell", "dumpsys", "telephony.registry"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            output = result.stdout
            
            for line in output.split('\n'):
                if 'mCallIncomingNumber=' in line:
                    parts = line.split('mCallIncomingNumber=')
                    if len(parts) > 1:
                        number = parts[1].strip().split()[0] if parts[1].strip() else ""
                        if number and len(number) > 5:
                            logger.info(f"✅ Number from telephony: {number}")
                            return number
        except Exception as e:
            logger.error(f"Telephony read error: {e}")
        
        logger.warning("❌ No number found from any source")
        return ""
    
    def start_monitoring(self):
        """Start monitoring call state"""
        if self.running:
            return True
        
        if not self.check_adb():
            return False
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🎧 USB/ADB monitoring started")
        return True
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        check_count = 0
        
        while self.running:
            try:
                new_state = self.get_call_state()
                check_count += 1
                
                # Debug print every 10 checks
                if check_count % 10 == 0:
                    print(f"   [DEBUG] State: {new_state.value}", end='\r')
                
                with self._lock:
                    if new_state != self._last_state:
                        self._handle_state_change(new_state)
                        self._last_state = new_state
                
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(1)
    
    def _handle_state_change(self, new_state):
        """Handle state change"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if new_state == USBCallState.DIALING:
            if self.current_state == USBCallState.IDLE:
                print(f"📱 DIALING... | Time: {current_time}")
                logger.info("📱 Dialing...")
                self.current_state = new_state
        
        elif new_state == USBCallState.RINGING:
            if self.current_state in [USBCallState.IDLE, USBCallState.DIALING]:
                if self.ring_start_time is None:
                    self.ring_count = 0
                    self.ring_start_time = time.time()
                
                self.ring_count += 1
                ring_duration = time.time() - self.ring_start_time
                
                self.current_number = self.get_call_number()
                logger.info(f"📞 Got number during RINGING: '{self.current_number}'")
                
                print(f"📞 RINGING #{self.ring_count} | Time: {current_time} | Duration: {ring_duration:.1f}s")
                logger.info(f"📞 RINGING - samne wale ko ring ja rahi hai")
                
                if self.on_ringing:
                    self.on_ringing(self.current_number, self.ring_count)
                
                self.current_state = new_state
        
        elif new_state == USBCallState.ACTIVE:
            if self.current_state in [USBCallState.RINGING, USBCallState.DIALING, USBCallState.IDLE]:
                print(f"✅ CALL PICKED UP! | Time: {current_time}")
                logger.info("✅ SAMNE WALE NE PICK KAR LIYA!")
                
                # Try to get number again at pickup
                pickup_number = self.get_call_number()
                if pickup_number and pickup_number != "Unknown":
                    self.current_number = pickup_number
                    logger.info(f"📱 Updated number at PICKUP: '{self.current_number}'")
                else:
                    logger.warning(f"⚠️ No number at PICKUP, using: '{self.current_number}'")
                
                self.current_state = new_state
                
                if self.on_pickup:
                    self.on_pickup(self.current_number)
        
        elif new_state == USBCallState.IDLE:
            if self.current_state in [USBCallState.ACTIVE, USBCallState.RINGING, USBCallState.DIALING]:
                print(f"📴 CALL ENDED | Time: {current_time}")
                logger.info("📴 CALL ENDED")
                
                self.current_state = new_state
                
                if self.on_hangup:
                    self.on_hangup()
                
                self.ring_count = 0
                self.ring_start_time = None
                self.current_number = ""
            else:
                self.current_state = new_state
    
    def get_current_state(self):
        """Get current state"""
        with self._lock:
            return self.current_state
    
    def hang_up_call(self):
        """Send END_CALL broadcast to Android app via ADB"""
        if not self.adb_path:
            logger.error("❌ ADB not found - cannot send command")
            return False
        
        try:
            # Send broadcast to app - app will end call and trigger next
            cmd = [
                self.adb_path, "shell", "am", "broadcast",
                "-a", "com.callingagent.END_CALL",
                "-n", "com.callingagent.app/.receiver.PCCommandReceiver"
            ]
            
            logger.info("� Sending END_CALL broadcast to app...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and "Broadcast completed" in result.stdout:
                logger.info("✅ END_CALL broadcast sent successfully!")
                logger.info("📱 App will end call and dial next number")
                return True
            else:
                logger.warning(f"Broadcast result: {result.stdout} {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            return False


# ============================================================
# GLOBAL SETTINGS
# ============================================================

OPENING_AUDIO = ""
AI_MODE = False


def select_audio_file():
    """GUI to select opening audio file"""
    global OPENING_AUDIO
    
    root = tk.Tk()
    root.title("AI Calling Agent - USB Mode")
    root.geometry("500x300")
    root.configure(bg="#1a1a2e")
    root.resizable(False, False)
    
    selected_file = tk.StringVar(value="No file selected")
    
    def browse_file():
        file_path = filedialog.askopenfilename(
            title="Select Opening Audio",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.m4a"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            selected_file.set(os.path.basename(file_path))
            global OPENING_AUDIO
            OPENING_AUDIO = file_path
    
    def confirm():
        if not OPENING_AUDIO:
            messagebox.showwarning("Warning", "Please select an audio file!")
            return
        root.destroy()
    
    # Title
    tk.Label(
        root, text="🤖 AI Calling Agent", 
        font=("Arial", 20, "bold"), 
        fg="#00ff88", bg="#1a1a2e"
    ).pack(pady=15)
    
    tk.Label(
        root, text="USB Mode - Phone se Excel select karke call karo", 
        font=("Arial", 10), 
        fg="#888888", bg="#1a1a2e"
    ).pack()
    
    tk.Label(
        root, text="PC sirf call detect karega aur audio play karega", 
        font=("Arial", 10), 
        fg="#888888", bg="#1a1a2e"
    ).pack()
    
    # Audio selection
    tk.Label(
        root, text="🔊 Opening Audio File", 
        font=("Arial", 12), 
        fg="white", bg="#1a1a2e"
    ).pack(pady=(25, 5))
    
    frame = tk.Frame(root, bg="#1a1a2e")
    frame.pack(pady=5)
    
    tk.Label(
        frame, textvariable=selected_file, 
        font=("Arial", 10), 
        fg="#aaaaaa", bg="#16213e",
        width=35, height=2
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        frame, text="📁 Browse", 
        command=browse_file,
        font=("Arial", 10),
        bg="#0f3460", fg="white",
        width=10
    ).pack(side=tk.LEFT, padx=5)
    
    # Confirm button
    tk.Button(
        root, text="✅ CONFIRM & START", 
        command=confirm,
        font=("Arial", 12, "bold"),
        bg="#00ff88", fg="black",
        width=20, height=2
    ).pack(pady=30)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_width()) // 2
    y = (root.winfo_screenheight() - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()
    
    return OPENING_AUDIO


def ask_ai_mode():
    """Console prompt for AI mode"""
    global AI_MODE
    
    print("\n" + "=" * 50)
    print("🤖 AI TALKING MODE")
    print("=" * 50)
    print("\nY = AI baat karega, analyze karega, Excel report banega")
    print("N = Sirf audio play, call cut, next call (No AI)")
    print()
    
    while True:
        choice = input("AI Talking? (Y/N): ").strip().upper()
        if choice in ['Y', 'N']:
            AI_MODE = (choice == 'Y')
            break
        print("❌ Please enter Y or N")
    
    if AI_MODE:
        print("\n✅ AI MODE: ON - AI baat karega")
    else:
        print("\n✅ AI MODE: OFF - Sirf audio play hoga")
    
    return AI_MODE


# ============================================================
# MAIN CALLING AGENT
# ============================================================

class CallingAgent:
    def __init__(self, opening_audio, ai_mode, show_banner=True):
        if show_banner:
            self._print_banner()
        
        self.opening_audio = opening_audio
        self.ai_mode = ai_mode
        
        logger.info("Initializing components...")
        
        # USB/ADB Call Detector
        self.usb_detector = ADBCallDetector()
        self.usb_detector.on_ringing = self._on_ringing
        self.usb_detector.on_pickup = self._on_pickup
        self.usb_detector.on_hangup = self._on_hangup
        
        self.tts = TTSEngine()
        self.excel = ExcelHandler()
        self.audio_tracker = AudioTracker()
        
        # Only load listener if AI mode
        self.listener = None
        if self.ai_mode:
            from speech_listener import SpeechListener
            self.listener = SpeechListener()
        
        # Only load LLM if AI mode is ON
        self.llm = None
        if self.ai_mode:
            try:
                from llm_engine import LLMEngine
                self.llm = LLMEngine()
                logger.info("🤖 AI Mode: ON")
            except Exception as e:
                logger.error(f"LLM init failed: {e}")
                logger.warning("⚠️ Running without AI - just audio playback")
                self.ai_mode = False
        else:
            logger.info("📢 AI Mode: OFF - Audio only")
        
        self.current_number = ""
        self.call_start_time = 0
        self.last_speech_time = 0
        self.in_call = False
        self.audio_length = 0
        self.audio_start_time = 0
        
        # Threading events
        self._pickup_event = threading.Event()
        self._hangup_event = threading.Event()
        self._call_lock = threading.Lock()  # Prevent duplicate call handling
        
        logger.info(f"� Opening Audio: {os.path.basename(opening_audio)}")
    
    def _print_banner(self):
        print("""
╔═══════════════════════════════════════════════════════════╗
║     🤖 AI CALLING AGENT - USB/ADB Mode                    ║
║     Phone app se Excel select karo, PC audio play karega  ║
╚═══════════════════════════════════════════════════════════╝
        """)
    
    def _on_ringing(self, number, ring_count):
        """Called when phone is ringing"""
        if number and number != "Unknown":
            self.current_number = number
        # Don't start timer yet - wait for pickup
    
    def _on_pickup(self, number):
        """Called when call is picked up"""
        # Update number if we got it now
        if number and number != "Unknown":
            self.current_number = number
        self._pickup_event.set()
    
    def _on_hangup(self):
        """Called when call ends"""
        self._hangup_event.set()
        # Stop audio safely
        try:
            self.tts.stop()
        except:
            pass
    
    def start(self):
        """Start the agent"""
        if not self.usb_detector.start_monitoring():
            logger.error("❌ Failed to start USB monitoring")
            print("\n⚠️ Make sure:")
            print("   1. Phone USB se connected hai")
            print("   2. USB Debugging ON hai (Developer Options me)")
            print("   3. Phone pe 'Allow USB Debugging' popup accept karo")
            print("\n   ADB path check karo:")
            print(f"   {self.usb_detector.adb_path or 'NOT FOUND'}")
            return
        
        if self.ai_mode and self.listener:
            self.listener.calibrate()
        
        logger.info("=" * 50)
        logger.info("✅ READY - USB monitoring active")
        logger.info("📱 Phone app se Excel select karo aur calling start karo")
        logger.info(f"🤖 AI Mode: {'ON' if self.ai_mode else 'OFF'}")
        logger.info("=" * 50)
        
        print("\n" + "=" * 50)
        print("📱 PHONE APP SE CALLING START KARO")
        print("   PC automatically call detect karega")
        print("=" * 50 + "\n")
        
        self._main_loop()
    
    def _main_loop(self):
        """Main loop - wait for calls from phone app"""
        while True:
            try:
                # Reset events
                self._pickup_event.clear()
                self._hangup_event.clear()
                
                # Wait for pickup
                if self._pickup_event.wait(timeout=0.5):
                    self._handle_call()
                
            except KeyboardInterrupt:
                logger.info("\n⛔ Stopped by user")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(1)
        
        self.usb_detector.stop_monitoring()
    
    def _handle_call(self):
        """Handle active call"""
        # Prevent duplicate call handling
        if not self._call_lock.acquire(blocking=False):
            logger.warning("⚠️ Call already being handled - skipping duplicate")
            return
        
        try:
            self.in_call = True
            self.call_start_time = time.time()
            self.last_speech_time = time.time()
            self._hangup_event.clear()
            
            # Start audio timer RIGHT NOW at pickup
            self.audio_start_time = time.time()
            
            if self.llm:
                self.llm.reset_conversation()
            
            logger.info(f"📞 Call active: {self.current_number}")
            
            time.sleep(0.5)
            
            if self.ai_mode:
                self._handle_call_ai()
            else:
                self._handle_call_audio_only()
            
            self._end_call()
        finally:
            self._call_lock.release()
    
    def _handle_call_ai(self):
        """AI MODE: Play audio then conversation"""
        logger.info("🤖 MODE: AI Active")
        
        if os.path.exists(self.opening_audio):
            logger.info(f"� Playing: {os.path.basename(self.opening_audio)}")
            self._play_audio_with_hangup_check(self.opening_audio)
            
            if self._hangup_event.is_set():
                logger.info("📴 Call ended during audio")
                return
            
            logger.info("✅ Audio finished")
        else:
            pitch = get_random_pitch()
            self.tts.speak(pitch)
            if self.llm:
                self.llm.conversation_history.append({"role": "assistant", "content": pitch})
        
        self.last_speech_time = time.time()
        
        if not self._hangup_event.is_set():
            self._conversation_loop()
    
    def _handle_call_audio_only(self):
        """AUDIO ONLY MODE: Just play audio, then call ends"""
        logger.info("📢 MODE: Audio Only")
        
        if os.path.exists(self.opening_audio):
            # Get audio length
            self.audio_length = self.tts.get_audio_duration(self.opening_audio)
            logger.info(f"🔊 Playing: {os.path.basename(self.opening_audio)} ({self.audio_length:.1f}s)")
            
            # Start timer RIGHT BEFORE audio play
            audio_play_start = time.time()
            
            self._play_audio_with_hangup_check(self.opening_audio)
            
            # Calculate ACTUAL listened time (from audio start to hangup/end)
            listened_time = time.time() - audio_play_start
            
            # Cap at audio length (can't listen more than audio duration)
            if listened_time > self.audio_length:
                listened_time = self.audio_length
            
            if self._hangup_event.is_set():
                logger.info(f"📴 Call ended during audio (listened: {listened_time:.1f}s / {self.audio_length:.1f}s)")
            else:
                logger.info("✅ Audio finished - call will end now")
            
            # Use current_number or fallback to "Unknown"
            phone = self.current_number if self.current_number else "Unknown"
            
            # Log to Excel
            self.audio_tracker.log_call(phone, self.audio_length, listened_time)
        else:
            logger.error("❌ Audio file not found!")
            return
    
    def _play_audio_with_hangup_check(self, audio_file):
        """Play audio file with hangup check"""
        # Prevent duplicate playback
        if self.tts._playing:
            logger.warning("⚠️ Audio already playing - skipping")
            return
        
        play_thread = threading.Thread(
            target=self.tts.play_file, 
            args=(audio_file,),
            daemon=True
        )
        play_thread.start()
        
        while play_thread.is_alive():
            if self._hangup_event.is_set():
                self.tts.stop()
                break
            time.sleep(0.1)
        
        play_thread.join(timeout=1)
    
    def _conversation_loop(self):
        """AI conversation loop"""
        if not self.llm or not self.listener:
            return
        
        logger.info("🎤 Listening...")
        self.listener.start_continuous()
        self.listener.clear_queue()
        
        # Track irrelevant questions
        irrelevant_count = 0
        MAX_IRRELEVANT = 4  # End call after 4 irrelevant questions
        
        while self.in_call and not self._hangup_event.is_set():
            if self._hangup_event.is_set():
                break
            
            if time.time() - self.call_start_time > MAX_CALL_DURATION:
                logger.info("⏰ Max duration")
                self.tts.speak("Bahut accha laga. Bye!")
                break
            
            user_text = self.listener.get_text()
            
            if user_text:
                self.last_speech_time = time.time()
                
                logger.info("=" * 50)
                logger.info(f"👤 USER: \"{user_text}\"")
                logger.info("=" * 50)
                
                if self._is_end_signal(user_text):
                    self.listener.pause()  # Pause instead of stop to avoid context error
                    self.tts.speak("Theek hai, dhanyavaad! Bye!")
                    break
                
                if self._hangup_event.is_set():
                    break
                
                logger.info("🤔 AI...")
                
                # STOP listener completely before AI speaks
                self.listener.stop_continuous()
                time.sleep(0.2)
                
                # Get full response
                full_response = self.llm.generate_response(user_text)
                
                logger.info("-" * 50)
                logger.info(f"🤖 AI: \"{full_response}\"")
                logger.info("-" * 50)
                
                # Split by sentence and speak each separately (prevents skipping)
                if not self._hangup_event.is_set():
                    import re
                    sentences = re.split(r'[.!?।]\s*', full_response)
                    for sentence in sentences:
                        if sentence.strip() and not self._hangup_event.is_set():
                            self.tts.speak(sentence.strip())
                            time.sleep(0.1)  # Minimal gap
                    time.sleep(0.2)
                
                # Check if response indicates irrelevant question
                if "maaf" in full_response.lower() or "pata nahi" in full_response.lower():
                    irrelevant_count += 1
                    logger.info(f"⚠️ Irrelevant question #{irrelevant_count}/{MAX_IRRELEVANT}")
                    
                    if irrelevant_count >= MAX_IRRELEVANT:
                        logger.info("❌ Too many irrelevant questions - ending call")
                        if not self._hangup_event.is_set():
                            self.listener.pause()
                            # Already spoken via streaming
                            time.sleep(0.5)
                            self.tts.speak("Theek hai, aapka dhanyavaad. Agar course me interest ho to call kijiye. Bye!")
                        break
                
                if not self._hangup_event.is_set():
                    # Restart listener
                    self.listener.start_continuous()
                    self.listener.clear_queue()
                    self.last_speech_time = time.time()
                else:
                    break
            else:
                if time.time() - self.last_speech_time >= SILENCE_TIMEOUT:
                    logger.info(f"⏳ {SILENCE_TIMEOUT}s silence")
                    if not self._hangup_event.is_set():
                        self.tts.speak(SILENCE_MESSAGE)
                    break
            
            time.sleep(0.15)
        
        self.listener.stop_continuous()
    
    def _is_end_signal(self, text):
        end_words = ["bye", "nahi", "no", "bas", "cut", "band", "rakhiye", "busy"]
        return any(w in text.lower() for w in end_words)
    
    def _end_call(self):
        if not self.in_call:
            return
        
        self.in_call = False
        duration = int(time.time() - self.call_start_time)
        
        logger.info(f"📊 Duration: {duration}s")
        
        if self.ai_mode and self.llm and self.llm.conversation_history:
            logger.info("🔍 Analyzing...")
            analysis = self.llm.analyze_conversation()
            conversation = self.llm.get_conversation_text()
            logger.info(f"   Result: {analysis['result']}")
            self.excel.save_result(self.current_number, duration, analysis, conversation)
        else:
            self.excel.save_result(self.current_number, duration, {
                "interest": "AUDIO_ONLY" if not self.ai_mode else "NO_CONVERSATION",
                "result": "PLAYED" if not self.ai_mode else "NO_RESPONSE",
                "summary": "Audio played" if not self.ai_mode else "No conversation"
            }, "")
        
        # End call and trigger next (for both AI and Audio-only modes)
        logger.info("📴 Ending call and triggering next...")
        self.usb_detector.hang_up_call()
        
        logger.info("=" * 50)
        logger.info("👂 Ready for next call...")
        logger.info("=" * 50)


# ============================================================
# MAIN
# ============================================================

def main():
    try:
        print("\n🔌 USB Mode Setup")
        print("⚠️  Phone USB se connected hona chahiye with USB Debugging ON")
        print()
        
        audio_file = select_audio_file()
        
        if not audio_file:
            print("❌ No audio selected. Exiting.")
            return
        
        print(f"✅ Audio: {os.path.basename(audio_file)}")
        
        ai_mode = ask_ai_mode()
        
        agent = CallingAgent(audio_file, ai_mode)
        agent.start()
        
    except KeyboardInterrupt:
        logger.info("\n⛔ Stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

"""
Speech Listener - Mic se user ki awaaz sunta hai
Uses OpenAI Whisper for best quality
"""
import speech_recognition as sr
import threading
import queue
import tempfile
import os
import wave
import io
import time
from datetime import datetime
from config import logger, OPENAI_API_KEY

# Try to import OpenAI for Whisper
try:
    from openai import OpenAI
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("OpenAI not installed - using Google Speech Recognition")


class SpeechListener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_listening = False
        self.text_queue = queue.Queue()
        self.listen_thread = None
        
        # OpenAI Whisper - BEST quality
        if WHISPER_AVAILABLE and OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
                logger.info("🎤 Using OpenAI Whisper (best quality)")
            except Exception as e:
                self.openai_client = None
                logger.error(f"Whisper init failed: {e}")
        else:
            self.openai_client = None
            logger.info("🎤 Using FREE Google Speech Recognition")
        
        # Settings - OPTIMIZED for phone call audio
        self.recognizer.energy_threshold = 150  # Lower to catch softer audio
        self.recognizer.dynamic_energy_threshold = True  # Auto-adjust
        self.recognizer.dynamic_energy_adjustment_damping = 0.15  # Faster adjustment
        self.recognizer.dynamic_energy_ratio = 1.2  # More sensitive
        self.recognizer.pause_threshold = 0.5
        self.recognizer.phrase_threshold = 0.1
        self.recognizer.non_speaking_duration = 0.3
        
        # Temp directory for audio files
        self.temp_dir = tempfile.gettempdir()
        
        self._setup_microphone()
    
    def _setup_microphone(self):
        """Setup default microphone"""
        try:
            self.microphone = sr.Microphone()
            logger.info("🎤 Microphone ready")
        except Exception as e:
            logger.error(f"Microphone error: {e}")
    
    def calibrate(self):
        """Calibrate for ambient noise"""
        logger.info("🔧 Calibrating microphone (3 seconds)...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=3)
            logger.info(f"✅ Calibrated | Threshold: {self.recognizer.energy_threshold:.0f}")
        except Exception as e:
            logger.error(f"Calibration error: {e}")
    
    def _transcribe_with_whisper(self, audio_data):
        """Transcribe audio using OpenAI Whisper - best quality"""
        if not self.openai_client:
            return None
        
        try:
            # Convert audio to WAV file
            wav_data = audio_data.get_wav_data()
            temp_file = os.path.join(self.temp_dir, f"speech_{datetime.now().strftime('%H%M%S')}.wav")
            
            with open(temp_file, "wb") as f:
                f.write(wav_data)
            
            # Enhanced prompt
            enhanced_prompt = """course, timing, fees, address, visit, interested, 
            Excel, Tally, centre, discount, office, graphic, designing, analytics, english, speaking,
            kab, kitna, kaise, kahan, konsa, haan, nahi, theek, rupaye, hello, kaun"""
            
            # OpenAI Whisper
            text = None
            try:
                with open(temp_file, "rb") as audio_file:
                    response = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="hi",
                        response_format="text",
                        temperature=0,
                        prompt=enhanced_prompt
                    )
                
                text = response.strip() if isinstance(response, str) else str(response).strip()
            except Exception as e:
                logger.error(f"Whisper error: {e}")
                return None
            
            # Cleanup
            try:
                os.remove(temp_file)
            except:
                pass
            
            # Filter out hallucinations and garbage
            if text:
                # Skip if too short (likely garbage)
                if len(text) < 3:
                    logger.debug(f"Skipping too short: '{text}'")
                    return None
                
                # Skip "प्रेंग" type hallucinations (repeated garbage)
                words = text.split()
                if len(words) > 3:
                    # Check if same word repeated (hallucination)
                    unique_words = set(words)
                    if len(unique_words) <= 2:  # Only 1-2 unique words repeated
                        logger.debug(f"Skipping repetition hallucination: '{text}'")
                        return None
                
                # Skip Malayalam/Tamil/Telugu scripts
                if any(ord(c) >= 0x0D00 for c in text):
                    logger.debug(f"Skipping non-Hindi script: '{text}'")
                    return None
                
                # Skip common hallucination patterns
                hallucination_patterns = [
                    "प्रेंग", "रिंग", "ding", "beep",
                    "thank you", "subscribe",
                    "silence", "music"
                ]
                text_lower = text.lower()
                for pattern in hallucination_patterns:
                    if pattern in text_lower:
                        logger.debug(f"Skipping hallucination: '{text}'")
                        return None
                
                logger.info(f"🎤 [WHISPER] User: \"{text}\"")
                return text
            
            return None
            
        except Exception as e:
            logger.error(f"Whisper error: {e}")
            return None
    
    def _transcribe_with_google(self, audio_data):
        """Fallback to Google Speech Recognition"""
        try:
            # Try Hindi first
            text = self.recognizer.recognize_google(audio_data, language="hi-IN")
            if text:
                logger.info(f"🎤 [GOOGLE-HI] User: \"{text}\"")
                return text
        except:
            pass
        
        try:
            # Try English-India
            text = self.recognizer.recognize_google(audio_data, language="en-IN")
            if text:
                logger.info(f"🎤 [GOOGLE-EN] User: \"{text}\"")
                return text
        except:
            pass
        
        return None
    
    def listen_once(self, timeout=10):
        """Listen for one phrase and return text"""
        try:
            with self.microphone as source:
                logger.debug("Listening...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
            
            logger.debug("Processing audio...")
            
            # Try Whisper first (better for noisy/distorted audio)
            if self.openai_client:
                text = self._transcribe_with_whisper(audio)
                if text:
                    return text
            
            # Fallback to Google
            text = self._transcribe_with_google(audio)
            if text:
                return text
            
            logger.debug("No speech recognized")
            return None
            
        except sr.WaitTimeoutError:
            logger.debug("Listen timeout - no speech")
            return None
        except Exception as e:
            logger.error(f"Listen error: {e}")
            return None
    
    def start_continuous(self):
        """Start continuous listening in background"""
        if self.is_listening:
            return
        
        self.is_listening = True
        self._paused = False  # New: pause flag
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        logger.info("🎤 Continuous listening started")
    
    def stop_continuous(self):
        """Stop continuous listening"""
        self.is_listening = False
        # Wait a bit for thread to finish current listen
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=0.5)
        logger.info("🎤 Listening stopped")
    
    def pause(self):
        """Pause listening temporarily (without stopping thread)"""
        self._paused = True
    
    def resume(self):
        """Resume listening"""
        self._paused = False
    
    def _listen_loop(self):
        """Background listening loop"""
        while self.is_listening:
            if getattr(self, '_paused', False):
                time.sleep(0.1)
                continue
            
            try:
                with self.microphone as source:
                    logger.debug("Listening...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                
                logger.debug("Processing audio...")
                
                # Try Whisper first
                if self.openai_client:
                    text = self._transcribe_with_whisper(audio)
                    if text:
                        self.text_queue.put(text)
                        continue
                
                # Fallback to Google
                text = self._transcribe_with_google(audio)
                if text:
                    self.text_queue.put(text)
            
            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                if "context manager" not in str(e):
                    logger.error(f"Listen error: {e}")
                time.sleep(0.1)
    
    def get_text(self):
        """Get latest recognized text (non-blocking)"""
        try:
            return self.text_queue.get_nowait()
        except queue.Empty:
            return None
    
    def clear_queue(self):
        """Clear any pending text"""
        while not self.text_queue.empty():
            try:
                self.text_queue.get_nowait()
            except:
                break


if __name__ == "__main__":
    print("=" * 50)
    print("🎤 SPEECH LISTENER TEST")
    print("=" * 50)
    
    listener = SpeechListener()
    
    if listener.openai_client:
        print("✅ Using OpenAI Whisper (best for noisy audio)")
    else:
        print("⚠️ Using Google Speech (Whisper not available)")
    
    listener.calibrate()
    
    print("\n🎤 Say something (Hindi/English)...")
    text = listener.listen_once()
    
    if text:
        print(f"\n✅ Recognized: {text}")
    else:
        print("\n❌ Nothing recognized")

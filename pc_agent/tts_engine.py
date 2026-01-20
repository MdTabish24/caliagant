"""
TTS Engine - Text to Speech
Uses Edge TTS (FREE, Indian Hindi voice) - NO OpenAI TTS

COST: FREE! 
"""
import os
import subprocess
import tempfile
import asyncio
from config import logger

# Edge TTS - FREE with Indian Hindi voices
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts not installed! pip install edge-tts")

# gTTS fallback (also FREE)
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


class TTSEngine:
    def __init__(self):
        self.temp_file = os.path.join(tempfile.gettempdir(), "tts_output.mp3")
        self._current_process = None
        self._stop_flag = False
        self._playing = False  # Track if already playing
        
        if EDGE_TTS_AVAILABLE:
            logger.info("🔊 TTS ready | Using: Edge TTS (hi-IN-MadhurNeural - FREE Indian voice)")
        elif GTTS_AVAILABLE:
            logger.info("🔊 TTS ready | Using: gTTS (fallback)")
        else:
            logger.error("❌ No TTS engine available!")
    
    def stop(self):
        """Stop currently playing audio"""
        self._stop_flag = True
        self._playing = False
        
        if self._current_process:
            try:
                self._current_process.terminate()
                self._current_process.wait(timeout=1)
            except:
                try:
                    self._current_process.kill()
                except:
                    pass
            self._current_process = None
        
        # Kill any ffplay processes (hidden window)
        try:
            subprocess.run(["taskkill", "/F", "/IM", "ffplay.exe"], 
                          capture_output=True, 
                          creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
        
        # Kill PowerShell MediaPlayer processes (hidden window)
        try:
            subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command", 
                          "Get-Process | Where-Object {$_.MainWindowTitle -like '*MediaPlayer*'} | Stop-Process -Force"],
                          capture_output=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
        
        logger.debug("🔇 Audio stopped")
    
    def _speak_edge_tts(self, text):
        """Use Edge TTS - FREE with Indian Hindi male voice (LEGACY - use async version)"""
        try:
            async def generate():
                communicate = edge_tts.Communicate(
                    text=text,
                    voice="hi-IN-MadhurNeural",
                    rate="+25%",
                    pitch="-2Hz"
                )
                await communicate.save(self.temp_file)
            
            asyncio.run(generate())
            return True
        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
            return False
    
    def _speak_gtts(self, text):
        """Use gTTS - FREE but robotic"""
        if not GTTS_AVAILABLE:
            return False
        try:
            tts = gTTS(text=text, lang='hi', slow=False)
            tts.save(self.temp_file)
            return True
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return False
    
    def speak(self, text):
        """Speak text through PC speaker - ASYNC for instant playback"""
        self._stop_flag = False
        
        if not text or len(text.strip()) == 0:
            logger.debug("No text to speak")
            return
        
        try:
            logger.debug(f"TTS: {text[:50]}...")
            
            success = False
            
            # Try Edge TTS first (FREE, Indian voice) - ASYNC!
            if EDGE_TTS_AVAILABLE:
                success = self._speak_edge_tts_async(text)
            
            # Fallback to gTTS
            if not success and GTTS_AVAILABLE:
                logger.debug("Trying gTTS fallback...")
                success = self._speak_gtts(text)
            
            if not success:
                logger.error("All TTS engines failed!")
                
        except Exception as e:
            logger.error(f"TTS Error: {e}")
    
    def _speak_edge_tts_async(self, text):
        """Use Edge TTS with ASYNC for instant playback"""
        try:
            async def generate_and_play():
                communicate = edge_tts.Communicate(
                    text=text,
                    voice="hi-IN-MadhurNeural",
                    rate="+25%",
                    pitch="-2Hz"
                )
                
                # Save to temp file
                await communicate.save(self.temp_file)
            
            # Run async
            asyncio.run(generate_and_play())
            
            if not self._stop_flag and os.path.exists(self.temp_file):
                self._play_audio()
            return True
            
        except Exception as e:
            logger.error(f"Edge TTS async error: {e}")
            return False
    
    def _play_audio(self):
        """Play audio file"""
        if self._stop_flag:
            return
        
        # Try ffplay first (best)
        try:
            self._current_process = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", self.temp_file],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self._current_process.wait(timeout=60)
            self._current_process = None
            return
        except:
            pass
        
        # Fallback: PowerShell
        try:
            abs_path = os.path.abspath(self.temp_file).replace("\\", "/")
            ps_script = f'''
            Add-Type -AssemblyName PresentationCore
            $p = New-Object System.Windows.Media.MediaPlayer
            $p.Open([System.Uri]"{abs_path}")
            $p.Volume = 1.0
            Start-Sleep -Milliseconds 500
            $p.Play()
            while ($p.NaturalDuration.HasTimeSpan -eq $false) {{ Start-Sleep -Milliseconds 100 }}
            Start-Sleep -Seconds ($p.NaturalDuration.TimeSpan.TotalSeconds + 0.5)
            $p.Close()
            '''
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=60)
        except Exception as e:
            logger.error(f"Audio play failed: {e}")
    
    def play_file(self, file_path):
        """Play an existing audio file (like opening.mp3)"""
        if self._playing:
            logger.warning("⚠️ Already playing - skipping duplicate")
            return False
        
        self._stop_flag = False
        self._playing = True
        
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found: {file_path}")
            self._playing = False
            return False
        
        logger.info(f"🔊 Playing: {os.path.basename(file_path)}")
        
        # Try ffplay first (best, no popup)
        try:
            self._current_process = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path],
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW  # Hide window
            )
            
            # Wait for process to finish or stop flag
            while self._current_process.poll() is None:
                if self._stop_flag:
                    self._current_process.terminate()
                    break
                import time
                time.sleep(0.1)
            
            self._current_process = None
            self._playing = False
            return True
        except FileNotFoundError:
            # ffplay not found, try PowerShell
            pass
        except Exception as e:
            logger.error(f"ffplay error: {e}")
        
        # Fallback: PowerShell (hidden window)
        try:
            abs_path = os.path.abspath(file_path).replace("\\", "/")
            ps_script = f'''
            Add-Type -AssemblyName PresentationCore
            $p = New-Object System.Windows.Media.MediaPlayer
            $p.Open([System.Uri]"{abs_path}")
            $p.Volume = 1.0
            Start-Sleep -Milliseconds 500
            $p.Play()
            while ($p.NaturalDuration.HasTimeSpan -eq $false) {{ Start-Sleep -Milliseconds 100 }}
            Start-Sleep -Seconds ($p.NaturalDuration.TimeSpan.TotalSeconds + 0.5)
            $p.Close()
            '''
            
            self._current_process = subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW  # Hide window
            )
            
            # Wait for process to finish or stop flag
            while self._current_process.poll() is None:
                if self._stop_flag:
                    self._current_process.terminate()
                    break
                import time
                time.sleep(0.1)
            
            self._current_process = None
            self._playing = False
            return True
        except Exception as e:
            logger.error(f"Play file failed: {e}")
            self._playing = False
            return False
    
    def get_audio_duration(self, file_path):
        """Get duration of audio file in seconds"""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", 
                 "-of", "default=noprint_wrappers=1:nokey=1", file_path],
                capture_output=True, text=True, timeout=10
            )
            return float(result.stdout.strip())
        except:
            return 30  # Default 30 seconds


if __name__ == "__main__":
    print("Testing TTS Engine (Edge TTS only)...")
    tts = TTSEngine()
    tts.speak("Hello sir, kaise hain aap? Centre visit karne ka plan hai kya?")
    print("Done!")

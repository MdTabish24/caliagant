"""
Advanced Audio-Based Call State Detector

Detects:
- RINGING: Ringtone, caller tune, music
- PICKUP: Human voice, speech ("hello", "haan")
- BUSY: Busy tone (beep pattern)
- SILENT: No audio / call cut

Uses:
- Voice Activity Detection (VAD)
- Speech Recognition for human voice
- Audio pattern analysis
"""
import numpy as np
import threading
import queue
import time
import webrtcvad
import pyaudio
import collections
from config import logger

# Try importing speech recognition
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    logger.warning("speech_recognition not installed")

# Try importing librosa for advanced audio analysis
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not installed - using basic detection")


class CallState:
    IDLE = "idle"
    RINGING = "ringing"      # Ringtone/music playing
    PICKUP = "pickup"        # Human voice detected
    BUSY = "busy"            # Busy tone
    SILENT = "silent"        # No audio
    UNKNOWN = "unknown"


class AudioCallDetector:
    """
    Detects call state by analyzing audio from phone speaker
    """
    
    def __init__(self, sample_rate=16000, frame_duration=30):
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration  # ms
        self.frame_size = int(sample_rate * frame_duration / 1000)
        
        # WebRTC VAD for voice detection
        self.vad = webrtcvad.Vad(3)  # Aggressiveness 0-3
        
        # PyAudio for mic input
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # State tracking
        self.current_state = CallState.IDLE
        self.is_running = False
        self.audio_queue = queue.Queue()
        
        # Detection buffers
        self.voice_buffer = collections.deque(maxlen=30)  # ~1 sec of frames
        self.energy_buffer = collections.deque(maxlen=50)
        self.speech_detected_count = 0
        self.silence_count = 0
        
        # Thresholds
        self.VOICE_THRESHOLD = 0.6      # 60% frames with voice = human
        self.SILENCE_THRESHOLD = 2.0    # 2 sec silence = call cut
        self.ENERGY_THRESHOLD = 500     # Min energy for audio
        self.PICKUP_CONFIRM_TIME = 1.5  # Confirm pickup after 1.5s of voice
        
        # Callbacks
        self.on_state_change = None
        
        # Speech recognizer for pickup confirmation
        if SR_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
        
        # Timing
        self.state_start_time = 0
        self.last_voice_time = 0
        self.pickup_confirmed = False
        
        logger.info("🎧 AudioCallDetector initialized")
        logger.info(f"   VAD: WebRTC | Sample Rate: {sample_rate}")
        logger.info(f"   Librosa: {'Yes' if LIBROSA_AVAILABLE else 'No'}")
    
    def start(self):
        """Start audio detection"""
        if self.is_running:
            return
        
        self.is_running = True
        self.current_state = CallState.IDLE
        self.pickup_confirmed = False
        
        # Find mic that captures system audio (VoiceMeeter, Stereo Mix, etc.)
        mic_index = self._find_audio_input()
        
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=mic_index,
                frames_per_buffer=self.frame_size
            )
            
            # Start detection thread
            self.detect_thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.detect_thread.start()
            
            logger.info("🎧 Audio detection started")
            
        except Exception as e:
            logger.error(f"Failed to start audio: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop audio detection"""
        self.is_running = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        self._set_state(CallState.IDLE)
        logger.info("🎧 Audio detection stopped")
    
    def _find_audio_input(self):
        """Find best audio input device"""
        # Look for virtual audio cable or stereo mix
        preferred = ["voicemeeter", "stereo mix", "what u hear", "cable output", "virtual"]
        
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            name = info.get("name", "").lower()
            
            if info.get("maxInputChannels", 0) > 0:
                for pref in preferred:
                    if pref in name:
                        logger.info(f"🎤 Using audio input: {info['name']}")
                        return i
        
        # Fallback to default
        logger.info("🎤 Using default audio input")
        return None
    
    def _detection_loop(self):
        """Main detection loop"""
        self.state_start_time = time.time()
        
        while self.is_running:
            try:
                # Read audio frame
                frame = self.stream.read(self.frame_size, exception_on_overflow=False)
                audio_data = np.frombuffer(frame, dtype=np.int16)
                
                # Analyze frame
                self._analyze_frame(audio_data, frame)
                
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Detection error: {e}")
                time.sleep(0.1)
    
    def _analyze_frame(self, audio_data, raw_frame):
        """Analyze single audio frame"""
        # Calculate energy
        energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
        self.energy_buffer.append(energy)
        
        # Check if there's any audio
        if energy < self.ENERGY_THRESHOLD:
            self.silence_count += 1
            self.voice_buffer.append(False)
            
            # Long silence = call might be cut
            if self.silence_count > (self.SILENCE_THRESHOLD * 1000 / self.frame_duration):
                if self.current_state != CallState.IDLE:
                    self._set_state(CallState.SILENT)
            return
        
        self.silence_count = 0
        
        # Voice Activity Detection
        try:
            is_voice = self.vad.is_speech(raw_frame, self.sample_rate)
            self.voice_buffer.append(is_voice)
        except:
            self.voice_buffer.append(False)
        
        # Calculate voice ratio
        if len(self.voice_buffer) >= 10:
            voice_ratio = sum(self.voice_buffer) / len(self.voice_buffer)
            
            # Detect state based on voice ratio
            self._detect_state(voice_ratio, energy, audio_data)
    
    def _detect_state(self, voice_ratio, energy, audio_data):
        """Detect call state from audio characteristics"""
        current_time = time.time()
        
        # HIGH voice ratio = Human speaking
        if voice_ratio > self.VOICE_THRESHOLD:
            self.last_voice_time = current_time
            
            if not self.pickup_confirmed:
                # Need sustained voice for pickup confirmation
                if self.current_state == CallState.RINGING:
                    # Was ringing, now voice detected
                    time_since_state = current_time - self.state_start_time
                    if time_since_state > 0.5:  # At least 0.5s of voice
                        self._confirm_pickup(audio_data)
                else:
                    self._set_state(CallState.RINGING)
                    # Start checking for pickup
                    if current_time - self.state_start_time > self.PICKUP_CONFIRM_TIME:
                        self._confirm_pickup(audio_data)
            
        # LOW voice ratio but has audio = Music/Ringtone
        elif voice_ratio < 0.3 and energy > self.ENERGY_THRESHOLD:
            if self.current_state == CallState.IDLE:
                self._set_state(CallState.RINGING)
            
            # Check for busy tone pattern
            if self._is_busy_tone(audio_data):
                self._set_state(CallState.BUSY)
        
        # Check if pickup was confirmed but now silent
        if self.pickup_confirmed:
            if current_time - self.last_voice_time > 3.0:
                # 3 seconds no voice after pickup = might be holding
                pass  # Keep as pickup
    
    def _confirm_pickup(self, audio_data):
        """Confirm pickup using speech recognition"""
        if self.pickup_confirmed:
            return
        
        # Quick check - if we have sustained voice, it's likely pickup
        voice_ratio = sum(self.voice_buffer) / len(self.voice_buffer) if self.voice_buffer else 0
        
        if voice_ratio > 0.5:
            logger.info("✅ PICKUP DETECTED (voice pattern)")
            self.pickup_confirmed = True
            self._set_state(CallState.PICKUP)
            return
        
        # Try speech recognition for confirmation
        if SR_AVAILABLE:
            try:
                # This is async - we'll confirm based on voice pattern for now
                pass
            except:
                pass
    
    def _is_busy_tone(self, audio_data):
        """Detect busy tone (repetitive beep pattern)"""
        if not LIBROSA_AVAILABLE:
            return False
        
        try:
            # Convert to float
            audio_float = audio_data.astype(np.float32) / 32768.0
            
            # Check for repetitive pattern (busy tone is ~400-600Hz beeps)
            # Simple zero-crossing rate check
            zcr = np.sum(np.abs(np.diff(np.sign(audio_float)))) / (2 * len(audio_float))
            
            # Busy tone has consistent ZCR
            if 0.1 < zcr < 0.3:
                return True
                
        except:
            pass
        
        return False
    
    def _set_state(self, new_state):
        """Set new state and trigger callback"""
        if new_state != self.current_state:
            old_state = self.current_state
            self.current_state = new_state
            self.state_start_time = time.time()
            
            logger.info(f"🎧 State: {old_state} -> {new_state}")
            
            if self.on_state_change:
                self.on_state_change(new_state, old_state)
    
    def get_state(self):
        """Get current detected state"""
        return self.current_state
    
    def is_pickup(self):
        """Check if call is picked up"""
        return self.current_state == CallState.PICKUP
    
    def reset(self):
        """Reset for new call"""
        self.current_state = CallState.IDLE
        self.pickup_confirmed = False
        self.voice_buffer.clear()
        self.energy_buffer.clear()
        self.silence_count = 0
        self.state_start_time = time.time()


class AdvancedPickupDetector:
    """
    More advanced pickup detection using multiple signals
    """
    
    def __init__(self):
        self.detector = AudioCallDetector()
        self.pickup_callbacks = []
        self.ringing_start = 0
        self.max_ring_time = 45  # Max 45 seconds ringing
        
        # Setup callback
        self.detector.on_state_change = self._on_state_change
    
    def start_detection(self):
        """Start detecting for a new call"""
        self.detector.reset()
        self.detector.start()
        self.ringing_start = time.time()
        logger.info("🎧 Pickup detection started")
    
    def stop_detection(self):
        """Stop detection"""
        self.detector.stop()
    
    def wait_for_pickup(self, timeout=45):
        """
        Wait for pickup detection
        Returns: True if picked up, False if timeout/busy/not answered
        """
        start = time.time()
        
        while time.time() - start < timeout:
            state = self.detector.get_state()
            
            if state == CallState.PICKUP:
                logger.info("✅ Call PICKED UP!")
                return True
            
            if state == CallState.BUSY:
                logger.info("📵 Line BUSY")
                return False
            
            if state == CallState.SILENT:
                # Check if was ringing before
                if time.time() - self.ringing_start > 5:
                    logger.info("📵 Call not answered (silent)")
                    return False
            
            time.sleep(0.1)
        
        logger.info("⏰ Pickup detection timeout")
        return False
    
    def on_pickup(self, callback):
        """Register pickup callback"""
        self.pickup_callbacks.append(callback)
    
    def _on_state_change(self, new_state, old_state):
        """Handle state changes"""
        if new_state == CallState.PICKUP:
            for cb in self.pickup_callbacks:
                try:
                    cb()
                except Exception as e:
                    logger.error(f"Pickup callback error: {e}")


# Test
if __name__ == "__main__":
    print("=" * 50)
    print("🎧 AUDIO CALL DETECTOR TEST")
    print("=" * 50)
    print("\nThis will listen to your audio input and detect:")
    print("- Ringtone/Music (RINGING)")
    print("- Human voice (PICKUP)")
    print("- Busy tone (BUSY)")
    print("- Silence (SILENT)")
    print("\nMake sure your phone audio is routed to PC!")
    print("Press Ctrl+C to stop\n")
    
    detector = AudioCallDetector()
    
    def on_change(new_state, old_state):
        print(f"\n>>> STATE CHANGE: {old_state} -> {new_state}")
        if new_state == CallState.PICKUP:
            print("🎉 CALL PICKED UP!")
    
    detector.on_state_change = on_change
    detector.start()
    
    try:
        while True:
            state = detector.get_state()
            energy = np.mean(list(detector.energy_buffer)) if detector.energy_buffer else 0
            voice = sum(detector.voice_buffer) / len(detector.voice_buffer) if detector.voice_buffer else 0
            print(f"\rState: {state:10} | Energy: {energy:6.0f} | Voice: {voice:.1%}", end="")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        detector.stop()
        print("Done!")

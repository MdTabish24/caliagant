"""
Calling Agent - GUI Application
Easy to use interface for non-technical users
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import sys
import os
from datetime import datetime

class CallingAgentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Calling Agent System")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        
        self.agent_thread = None
        self.agent_instance = None  # Store agent reference
        self.is_running = False
        self.audio_file = ""
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="📞 Calling Agent System", 
                                font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, pady=10)
        
        # Control Panel
        control_frame = ttk.LabelFrame(main_frame, text="Control Panel", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Audio File Selection
        ttk.Label(control_frame, text="Audio File:", font=("Arial", 10)).grid(row=0, column=0, padx=5, sticky=tk.W)
        
        self.audio_label = ttk.Label(control_frame, text="No file selected", 
                                     font=("Arial", 9), foreground="gray")
        self.audio_label.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        ttk.Button(control_frame, text="📁 Browse", 
                  command=self.browse_audio).grid(row=0, column=2, padx=5)
        
        # Mode Selection
        ttk.Label(control_frame, text="Select Mode:", font=("Arial", 10)).grid(row=1, column=0, padx=5, sticky=tk.W, pady=5)
        
        self.mode_var = tk.StringVar(value="Y")
        mode_frame = ttk.Frame(control_frame)
        mode_frame.grid(row=1, column=1, columnspan=2, padx=5, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(mode_frame, text="AI Agent (Y)", variable=self.mode_var, 
                       value="Y").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Audio Only (N)", variable=self.mode_var, 
                       value="N").pack(side=tk.LEFT, padx=5)
        
        # Start/Stop Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="▶ Start Agent", 
                                    command=self.start_agent, width=20)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop Agent", 
                                   command=self.stop_agent, width=20, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(control_frame, text="Status: Ready", 
                                     font=("Arial", 10, "bold"), foreground="blue")
        self.status_label.grid(row=3, column=0, columnspan=3, pady=5)
        
        # Logs Panel
        logs_frame = ttk.LabelFrame(main_frame, text="System Logs", padding="10")
        logs_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, 
                                                  height=20, font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear logs button
        ttk.Button(logs_frame, text="Clear Logs", 
                  command=self.clear_logs).grid(row=1, column=0, pady=5)
        
        # Initial log
        self.log("System initialized. Ready to start.")
        self.log("Steps:")
        self.log("  1. Select audio file (Browse button)")
        self.log("  2. Choose mode (AI Agent or Audio Only)")
        self.log("  3. Connect phone via USB with USB debugging ON")
        self.log("  4. Click Start Agent")
    
    def browse_audio(self):
        """Browse and select audio file"""
        file_path = filedialog.askopenfilename(
            title="Select Opening Audio",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.m4a"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.audio_file = file_path
            self.audio_label.config(text=os.path.basename(file_path), foreground="green")
            self.log(f"✅ Audio selected: {os.path.basename(file_path)}")
        
    def log(self, message):
        """Add message to log window"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.update()
        
    def clear_logs(self):
        """Clear log window"""
        self.log_text.delete(1.0, tk.END)
        
    def start_agent(self):
        """Start the calling agent"""
        if self.is_running:
            self.log("⚠ Agent already running!")
            return
        
        if not self.audio_file:
            messagebox.showwarning("Warning", "Please select an audio file first!")
            return
            
        mode = self.mode_var.get()
        self.log(f"Starting agent in {'AI Agent' if mode == 'Y' else 'Audio Only'} mode...")
        
        # Disable start button, enable stop button
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Running", foreground="green")
        
        # Start agent in separate thread
        self.agent_thread = threading.Thread(target=self.run_agent, args=(mode,), daemon=True)
        self.agent_thread.start()
        
    def run_agent(self, mode):
        """Run the main agent directly"""
        self.is_running = True
        
        try:
            # Add current directory to path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            
            # Import CallingAgent class only (not main function)
            from main import CallingAgent
            
            self.log(f"✅ Audio: {os.path.basename(self.audio_file)}")
            self.log(f"🤖 Mode: {'AI Agent' if mode == 'Y' else 'Audio Only'}")
            self.log("🔌 Connecting to phone via USB...")
            
            # Create and start agent directly (no banner in GUI mode)
            self.agent_instance = CallingAgent(self.audio_file, mode == 'Y', show_banner=False)
            self.agent_instance.start()
            
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            self.is_running = False
            self.agent_instance = None
            self.root.after(0, self.on_agent_stopped)
            
    def stop_agent(self):
        """Stop the running agent"""
        if not self.is_running:
            return
            
        self.log("⚠ Stopping agent...")
        self.is_running = False
        
        # Stop the agent properly
        if self.agent_instance:
            try:
                # Stop USB monitoring
                if hasattr(self.agent_instance, 'usb_detector'):
                    self.agent_instance.usb_detector.running = False
                
                # Stop audio playback
                if hasattr(self.agent_instance, 'tts'):
                    self.agent_instance.tts.stop()
                
                # Stop listener if AI mode
                if hasattr(self.agent_instance, 'listener') and self.agent_instance.listener:
                    self.agent_instance.listener.stop_continuous()
                
                # Mark as not in call
                self.agent_instance.in_call = False
                
                self.log("✅ Agent stopped successfully")
            except Exception as e:
                self.log(f"⚠ Error stopping agent: {e}")
        
    def on_agent_stopped(self):
        """Called when agent stops"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Stopped", foreground="red")
        self.log("Agent stopped.")
        
    def on_closing(self):
        """Handle window close"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "Agent is running. Stop and quit?"):
                self.stop_agent()
                self.root.after(1000, self.root.destroy)
        else:
            self.root.destroy()

def main():
    # Redirect stdout to GUI
    root = tk.Tk()
    app = CallingAgentGUI(root)
    
    # Redirect print statements to log
    class StdoutRedirector:
        def write(self, text):
            if text.strip():
                app.log(text.strip())
        def flush(self):
            pass
    
    sys.stdout = StdoutRedirector()
    sys.stderr = StdoutRedirector()
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()

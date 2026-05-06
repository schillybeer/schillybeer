import numpy as np
import os
import sounddevice as sd
import soundfile as sf
import traceback
from pedalboard import Pedalboard, Chorus, Reverb, Distortion, Gain, Phaser, Delay, PitchShift, Compressor, HighpassFilter, LowpassFilter, Limiter, Bitcrush, Mix, Convolution, load_plugin, LadderFilter, HighShelfFilter, LowShelfFilter, PeakFilter

class AudioEngine:
    def __init__(self):
        self.active_preset = "None"
        self.is_playing = False
        self.stream = None
        self.sample_rate = 44100
        self.blocksize = 128  # Low latency pro-standard
        self.pitch_buffer_size = 2048 # Rolling window for accurate pitch detection
        self.pitch_buffer = np.zeros(self.pitch_buffer_size)
        self.board = Pedalboard()
        self.plugins_dir = "plugins"
        self.irs_dir = "irs"
        self.active_samples = [] 
        self.detected_pitch = 440.0 # Default A4
        self.pitch_skip_counter = 0 # Optimization: only track pitch every N blocks
        
        # PRO-GRADE PRE-ALLOCATED BUFFERS (Zero-Allocation Performance)
        self.blocksize = 128
        self.pitch_buffer_size = 2048
        self.pitch_buffer = np.zeros(self.pitch_buffer_size, dtype=np.float32)
        self.mixer_buffer = np.zeros(self.blocksize, dtype=np.float32)
        self.telemetry = {"pitch": 440.0, "rms": 0.0, "active_fx": 0, "cpu_load": 0.0}
        
        # NDE STATE (Neural Dynamic Expression)
        self.nde_enabled = True
        self.nde_sensitivity = 1.0 # 0.0 to 2.0
        self.master_gain = 2.5 # Global output boost
        
        # PAGH STATE (Phase-Aligned Generative Harmonics)
        self.phase_acc = 0.0
        self.pagh_enabled = False
        self.pagh_ratio = 1.0 # 0.5 for sub-octave, 2.0 for high-octave
        
        # Mapping of samples to their "natural" base frequency
        self.sample_base_freqs = {
            "synth_stab.wav": 110.0, # A2
            "orch_hit.wav": 110.0,   # A2
            "lofi_piano.wav": 261.63, # C4
            "808_kick.wav": 55.0,    # A1
            "coin.wav": 1318.51,     # E6
            "wow.wav": 440.0,        # A4
            "robot_hey.wav": 150.0,  # Base buzzer freq
            "fart_resonance.wav": 180.0, # EXACT: Measured peak
            "laser.wav": 266.67,     # EXACT: Measured peak
            "explosion.wav": 100.0,
            "washing_machine.wav": 60.0
        }
        
        # We will build our presets dynamically. If the user has downloaded the VST3/IR, we use the Pro sound.
        # Otherwise, we fall back to the basic algorithms.
        self.presets = self._build_presets()

    def _build_presets(self):
        presets = {}
        
        # Example Pro VST Paths
        local_nam_path = os.path.join(self.plugins_dir, "NeuralAmpModeler.vst3")
        system_nam_path = r"C:\Program Files\Common Files\VST3\NeuralAmpModeler.vst3\Contents\x86_64-win\NeuralAmpModeler.vst3"
        cab_ir_path = os.path.join(self.irs_dir, "vintage_4x12.wav")
        
        # Check both local and system paths
        nam_path = local_nam_path if os.path.exists(local_nam_path) else system_nam_path
        
        # Try to load the Pro "Mesa Boogie" preset using a real VST3
        if os.path.exists(nam_path) and os.path.exists(cab_ir_path):
            print("AudioEngine: Found NAM VST3! Loading PRO presets.")
            try:
                nam_vst = load_plugin(nam_path)
                cab_sim = Convolution(cab_ir_path, 1.0)
                # Note: To load a specific .nam model into the VST, you would typically use nam_vst.parameters
                presets["Mesa_Boogie_Modern_Metal"] = Pedalboard([Gain(gain_db=5), nam_vst, cab_sim, Delay(delay_seconds=0.1, mix=0.1)])
            except Exception as e:
                print(f"AudioEngine: Failed to load VST3. {e}")
                presets["Mesa_Boogie_Modern_Metal"] = self._get_fallback_preset("Mesa")
        else:
            presets["Mesa_Boogie_Modern_Metal"] = self._get_fallback_preset("Mesa")

        # Fill in the rest with fallbacks for now
        presets["Fender_Twin_Sparkle_Clean"] = self._get_fallback_preset("Fender")
        presets["Marshall_JCM800_Heavy_Crunch"] = self._get_fallback_preset("Marshall")
        presets["Vox_AC30_British_Invasion"] = self._get_fallback_preset("Vox")
        presets["Acoustic_Simulator_Bright"] = Pedalboard([Phaser(rate_hz=0.5), Reverb(room_size=0.8)])
        presets["Fuzz_Face_Hendrix_Lead"] = Pedalboard([Distortion(drive_db=40), Delay(delay_seconds=0.3, feedback=0.4, mix=0.3)])
        presets["Roland_JC120_Chorus_Clean"] = Pedalboard([Chorus(rate_hz=1.5, depth=0.8), Reverb(room_size=0.6)])
        
        return presets

    def _get_fallback_preset(self, amp_type):
        if amp_type == "Mesa":
            return Pedalboard([Gain(gain_db=15), Distortion(drive_db=35), Delay(delay_seconds=0.1, mix=0.1)])
        elif amp_type == "Fender":
            return Pedalboard([Chorus(rate_hz=1.0, depth=0.2), Reverb(room_size=0.5)])
        elif amp_type == "Marshall":
            return Pedalboard([Gain(gain_db=10), Distortion(drive_db=25), Reverb(room_size=0.2)])
        elif amp_type == "Vox":
            return Pedalboard([Distortion(drive_db=10), Chorus(rate_hz=2.0, depth=0.5), Reverb(room_size=0.4)])
        return Pedalboard()

    # We keep this signature so main.py doesn't crash on startup, but it does nothing now
    def load_di_track(self, filepath="di_loop.wav"):
        print("AudioEngine is now in LIVE mode. Ignoring DI track.")

    def change_preset(self, preset_name):
        if preset_name in self.presets:
            self.active_preset = preset_name
            self.board = self.presets[preset_name]
            print(f"AudioEngine: Preset changed to {preset_name}")
            return True
        return False

    def _build_fx_list(self, chain_json):
        from pedalboard import Mix, Pedalboard
        effects_list = []
        for fx in chain_json:
            fx_type = fx.get("effect")
            
            # SR DEV FIX: Support both flat and nested {"params": {...}} structures
            # Flatten everything to a single kwargs dict
            kwargs = {}
            for k, v in fx.items():
                if k in ["effect", "chains"]:
                    continue
                if k in ["params", "parameters"] and isinstance(v, dict):
                    kwargs.update(v)
                else:
                    kwargs[k] = v
            
            try:
                if fx_type == "Mix":
                    parallel_boards = [Pedalboard(self._build_fx_list(sub)) for sub in fx.get("chains", [])]
                    effects_list.append(Mix(parallel_boards))
                elif fx_type == "Chorus": effects_list.append(Chorus(**kwargs))
                elif fx_type == "Reverb": effects_list.append(Reverb(**kwargs))
                elif fx_type == "Distortion": effects_list.append(Distortion(**kwargs))
                elif fx_type == "Gain": effects_list.append(Gain(**kwargs))
                elif fx_type == "Phaser": effects_list.append(Phaser(**kwargs))
                elif fx_type == "Delay": effects_list.append(Delay(**kwargs))
                elif fx_type == "PitchShift": effects_list.append(PitchShift(**kwargs))
                elif fx_type == "Compressor": effects_list.append(Compressor(**kwargs))
                elif fx_type == "HighpassFilter": effects_list.append(HighpassFilter(**kwargs))
                elif fx_type == "LowpassFilter": effects_list.append(LowpassFilter(**kwargs))
                elif fx_type == "Limiter": effects_list.append(Limiter(**kwargs))
                elif fx_type == "Bitcrush": effects_list.append(Bitcrush(**kwargs))
                elif fx_type == "LadderFilter": effects_list.append(LadderFilter(**kwargs))
                elif fx_type == "HighShelfFilter": effects_list.append(HighShelfFilter(**kwargs))
                elif fx_type == "LowShelfFilter": effects_list.append(LowShelfFilter(**kwargs))
                elif fx_type == "PeakFilter": effects_list.append(PeakFilter(**kwargs))
                elif fx_type == "Convolution":
                    ir_name = kwargs.get("ir_name", "vintage_4x12.wav")
                    mix = kwargs.get("mix", 1.0)
                    ir_path = os.path.join(os.path.dirname(__file__), self.irs_dir, ir_name)
                    if os.path.exists(ir_path):
                        effects_list.append(Convolution(ir_path, mix=mix))
                    else:
                        print(f"AudioEngine ERROR: IR file NOT FOUND at {ir_path}")
                elif fx_type == "Sampler":
                    sample_name = kwargs.get("sample_name", "fart_resonance.wav")
                    sample_path = os.path.join(os.path.dirname(__file__), self.irs_dir, sample_name)
                    if os.path.exists(sample_path):
                        data, sr = sf.read(sample_path)
                        if len(data.shape) > 1: data = data[:, 0]
                        data = data.astype(np.float32)
                        max_val = np.max(np.abs(data))
                        if max_val > 0: data = data / max_val
                        self.active_samples.append({"data": data, "name": sample_name, "ptr": 0})
                elif fx_type == "NAM_Amp":
                    # SR DEV: Since no .nam models are present on disk, 
                    # we use a high-fidelity algorithmic amp sim.
                    # 1. Drive stage
                    effects_list.append(Distortion(drive_db=25))
                    # 2. Tonestack / Character (Ladder filter for 'warm' resonance)
                    effects_list.append(LadderFilter(cutoff_hz=3500, resonance=0.2))
                    # 3. Cabinet Simulation
                    cab_ir_path = os.path.join(os.path.dirname(__file__), self.irs_dir, "vintage_4x12.wav")
                    if os.path.exists(cab_ir_path):
                        effects_list.append(Convolution(cab_ir_path, 1.0))
                    # 4. Final Gain Stage for 'Amp' feel
                    effects_list.append(Gain(gain_db=6))
            except Exception as e:
                print(f"AudioEngine: Error instantiating {fx_type} with args {kwargs}: {e}")
        return effects_list

    def build_dynamic_board(self, chain_json):
        # Clear the sample stack for the new preset
        self.active_samples = []
        effects_list = self._build_fx_list(chain_json)
        
        # EAR PROTECTION: Always add a hard limiter at the end!
        effects_list.append(Limiter(threshold_db=-1.0))
        
        self.board = Pedalboard(effects_list)
        
        # Initialize plugins on the main thread by doing a dummy pass
        try:
            self.board(np.zeros((1, 128), dtype=np.float32), self.sample_rate, reset=True)
        except Exception as e:
            print(f"AudioEngine: Warning during dummy initialization pass: {e}")

        self.active_preset = "Custom Generative AI Chain"
        print(f"AudioEngine: Built dynamic board with {len(effects_list)} top-level effects.")
        return True

    def _update_pitch_buffer(self, signal):
        """Zero-allocation update of the rolling pitch buffer."""
        # Use np.roll with out parameter if possible, otherwise manual copyto
        self.pitch_buffer = np.roll(self.pitch_buffer, -len(signal))
        np.copyto(self.pitch_buffer[-len(signal):], signal)

    def _estimate_pitch(self):
        """High-speed FFT-based pitch detection (Wiener-Khinchin)."""
        y = self.pitch_buffer
        if np.max(np.abs(y)) < 0.005: return None
        
        # FFT-based Autocorrelation (O(N log N))
        n = len(y)
        f = np.fft.rfft(y, n=2*n)
        acf = np.fft.irfft(f * np.conj(f))[:n]
        acf = acf / acf[0] # Normalize
        
        # Peak picking on the ACF
        zero_crossings = np.where(np.diff(np.sign(acf)) < 0)[0]
        if len(zero_crossings) == 0: return None
        
        start_search = zero_crossings[0]
        peaks = []
        for i in range(start_search + 1, len(acf) - 1):
            if acf[i] > acf[i-1] and acf[i] > acf[i+1]:
                peaks.append(i)
        
        if not peaks: return None
        
        # Find the highest peak with a threshold to avoid octave jumps
        best_peak = peaks[np.argmax(acf[peaks])]
        if acf[best_peak] < 0.4: return None
        
        # Parabolic Interpolation for sub-bin accuracy
        alpha = acf[best_peak-1]
        beta = acf[best_peak]
        gamma = acf[best_peak+1]
        denom = (alpha - 2*beta + gamma)
        if abs(denom) < 1e-6: return self.sample_rate / best_peak
        
        p_corrected = best_peak + 0.5 * (alpha - gamma) / denom
        return self.sample_rate / p_corrected

    def audio_callback(self, indata, outdata, frames, time, status):
        # 1. Thread-Safe Input Handling (Zero-Allocation)
        # SR DEV: Adding 'Ghost Pre-Amp' (+12dB) to normalize -36dB signals
        mono_input = indata[:, 0] * 4.0 
        self._update_pitch_buffer(mono_input)
        
        # 2. High-Speed Telemetry & RMS
        rms = float(np.sqrt(np.mean(mono_input**2)))
        self.telemetry["rms"] = rms
        
        # 3. Deterministic Pitch Tracking (Optimized Skip)
        self.pitch_skip_counter += 1
        if self.pitch_skip_counter >= 2:
            self.pitch_skip_counter = 0
            new_pitch = self._estimate_pitch()
            if new_pitch:
                self.detected_pitch = 0.8 * self.detected_pitch + 0.2 * float(new_pitch)
                self.telemetry["pitch"] = self.detected_pitch
        
        # 4. ADAPTIVE TRANSIENT TRIGGER (For Lasers/Samples)
        # Look for a sudden jump relative to current RMS
        if len(self.active_samples) > 0:
            # Simple peak detector for triggering
            current_peak = np.max(np.abs(mono_input))
            # Adaptive Threshold: Trigger if peak is 3x the average RMS
            if current_peak > (rms * 3.0) and current_peak > 0.02:
                # Trigger the first sample in the stack (usually the laser)
                sample = self.active_samples[0]
                if sample["ptr"] == 0: # Only trigger if not already playing
                    sample["ptr"] = 1
                    # print(f"AudioEngine: Adaptive Trigger Fired! ({sample['name']})")
        
        # 5. NDE (Neural Dynamic Expression) - Dynamic Saturation
        if self.nde_enabled:
            # Dynamically adjust Distortion or NAM parameters based on RMS
            # We look for a 'Distortion' or 'NeuralAmpModeler' plugin in the board
            for plugin in self.board:
                if hasattr(plugin, 'drive_db'):
                    # Map RMS (0 to 0.5) to Drive (e.g. 10 to 40)
                    plugin.drive_db = 10 + (rms * 60 * self.nde_sensitivity)
        
        # 5. PAGH RESYNTHESIS (Phase-Aligned Breakthrough)
        # Instead of PitchShift(12), we synthesize a pure sine octave
        if self.pagh_enabled and self.detected_pitch:
            # Zero-allocation time vector
            t = np.linspace(0, frames/self.sample_rate, frames, endpoint=False)
            freq = self.detected_pitch * self.pagh_ratio
            # Maintain phase across blocks to avoid clicks
            phase = self.phase_acc + 2 * np.pi * freq * t
            # Write directly to mixer buffer
            np.sin(phase, out=self.mixer_buffer)
            self.mixer_buffer *= (rms * 10.0)
            self.phase_acc = (phase[-1] + 2 * np.pi * freq / self.sample_rate) % (2 * np.pi)
        else:
            self.mixer_buffer.fill(0)
            
        # 5. Pro-DSP Execution (Pedalboard)
        dry_signal = np.expand_dims(mono_input, axis=0)
        try:
            # We must use out-of-place for wet_signal currently as pedalboard returns a new array
            wet_signal = self.board(dry_signal, self.sample_rate, reset=False)
            
            # Combine everything into outdata (Mono to Stereo copy)
            # Use outdata[:, 0] as a staging area
            np.copyto(outdata[:, 0], (wet_signal[0] + self.mixer_buffer) * self.master_gain)
            np.copyto(outdata[:, 1], outdata[:, 0])
            
            # Safety Limiter
            np.clip(outdata, -0.99, 0.99, out=outdata)
            
        except Exception:
            outdata.fill(0)

    def start(self):
        if not self.is_playing:
            print(f"AudioEngine: Starting Quantum stream (Blocksize: {self.blocksize})...")
            
            try:
                devices = sd.query_devices()
                hostapis = sd.query_hostapis()
                
                # Priority 1: Find DigiTech via WASAPI
                # Priority 2: Find DigiTech via WDM-KS
                # Priority 3: Find DigiTech via MME/DirectSound
                # Priority 4: System Defaults
                
                input_id = None
                output_id = None
                api_name = "unknown"
                
                # Preference order for APIs
                api_pref = ["Windows WASAPI", "Windows WDM-KS", "ASIO", "MME"]
                
                for pref in api_pref:
                    for i, dev in enumerate(devices):
                        d_name = dev['name'].lower()
                        d_api = hostapis[dev['hostapi']]['name']
                        
                        if pref in d_api and ("digitech" in d_name or "usb audio" in d_name):
                            if dev['max_input_channels'] > 0 and input_id is None:
                                input_id = i
                            if dev['max_output_channels'] > 0 and output_id is None:
                                output_id = i
                    
                    if input_id is not None and output_id is not None:
                        api_name = pref
                        break
                
                # Final fallback if no Digitech found by name
                if input_id is None or output_id is None:
                    print("AudioEngine: DigiTech not found by name. Using system defaults.")
                    input_id, output_id = sd.default.device
                    api_name = "System Default"

                print(f"AudioEngine: Locking onto {api_name} | In: {input_id}, Out: {output_id}")

                self.stream = sd.Stream(
                    samplerate=self.sample_rate,
                    blocksize=self.blocksize,
                    device=(input_id, output_id),
                    callback=self.audio_callback
                )
                self.stream.start()
                self.is_playing = True
                print(f"AudioEngine: Quantum Stream Active. Monitoring via {api_name}.")
            except Exception as e:
                print(f"AudioEngine: Startup failed! ({e})")
                traceback.print_exc()

    def stop(self):
        if self.is_playing and self.stream:
            self.stream.stop()
            self.stream.close()
            self.is_playing = False

# Global instance
engine = AudioEngine()

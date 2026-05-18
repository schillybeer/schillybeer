import numpy as np
import os
import sounddevice as sd
import soundfile as sf
import traceback
from pedalboard import Pedalboard, Chorus, Reverb, Distortion, Gain, Phaser, Delay, PitchShift, Compressor, NoiseGate, HighpassFilter, LowpassFilter, Limiter, Bitcrush, Mix, Convolution, load_plugin, LadderFilter, HighShelfFilter, LowShelfFilter, PeakFilter, Chain

class NativeNAM:
    """
    A custom wrapper to execute PyTorch .nam neural network models
    natively as a Pedalboard node, bypassing VST3 limitations.
    """
    def __init__(self, nam_file_path):
        import json
        from nam.models._from_nam import init_from_nam
        print(f"NativeNAM: Loading neural weights from {nam_file_path}...")
        with open(nam_file_path, "r") as fp:
            config = json.load(fp)
            self.model = init_from_nam(config)
        self.model.eval() # Set to evaluation mode
        print("NativeNAM: Neural model loaded successfully!")

    def __call__(self, audio, sample_rate, reset=False):
        import torch
        # Audio is shape (channels, frames)
        if len(audio.shape) > 1:
            # NAM processes mono. Take left channel.
            mono = audio[0, :]
        else:
            mono = audio
            
        # The PyTorch NAM model expects a 2D tensor [1, frames]
        with torch.no_grad():
            tensor = torch.from_numpy(mono).unsqueeze(0).to(torch.float32)
            processed = self.model(tensor).squeeze(0).numpy()
        
        # Return as stereo to match Pedalboard pipeline
        if len(audio.shape) > 1:
            return np.vstack((processed, processed)).astype(np.float32)
        return processed.astype(np.float32)

class AsymmetricDistortion:
    """Simulates the uneven clipping characteristics of vacuum tubes."""
    def __init__(self, drive_db=20, asymmetry=0.3):
        self.drive_db = drive_db
        self.asymmetry = asymmetry # 0.0 to 1.0

    def process(self, data):
        drive = 10**(self.drive_db / 20)
        # Apply asymmetric gain
        pos_mask = data > 0
        neg_mask = ~pos_mask
        
        # Positive side clips harder/differently than negative
        data[pos_mask] = np.tanh(data[pos_mask] * drive)
        data[neg_mask] = np.tanh(data[neg_mask] * drive * (1.0 - self.asymmetry))
        
        return data

class PowerAmpSag:
    """Simulates 'Voltage Sag' where the amp compresses and darkens under heavy load."""
    def __init__(self, sensitivity=0.5):
        self.sensitivity = sensitivity
        self.rms_history = 0.0

    def process(self, data):
        # Calculate block RMS
        current_rms = np.sqrt(np.mean(data**2))
        # Slow smoothing for "Sag" feel
        self.rms_history = 0.9 * self.rms_history + 0.1 * current_rms
        
        # As RMS goes up, gain goes down slightly (Sag)
        sag_factor = 1.0 - (self.rms_history * self.sensitivity)
        sag_factor = max(0.7, sag_factor) # Don't mute it
        
        return data * sag_factor

class SpatialRotary:
    """Berklee-Engineered Leslie Speaker Simulation with 8D Spatial Auto-Panning."""
    def __init__(self, speed_hz=4.0, width=1.0, mix=1.0):
        self.speed_hz = speed_hz
        self.width = width
        self.mix = mix
        self.phase = 0.0
        self.sample_rate = 44100
        
    def process(self, data):
        # data is [channels, frames] (either 1 or 2 channels)
        frames = data.shape[-1]
        
        t = np.arange(frames) / self.sample_rate
        angle = 2 * np.pi * self.speed_hz * t + self.phase
        
        lfo_sin = np.sin(angle)
        lfo_cos = np.cos(angle)
        
        self.phase = (self.phase + 2 * np.pi * self.speed_hz * (frames / self.sample_rate)) % (2 * np.pi)
        
        # Tremolo (Amplitude modulation): 0.7 to 1.0 amplitude
        tremolo = 1.0 - (0.3 * (lfo_sin * 0.5 + 0.5))
        
        # Auto-panning (8D Spatial movement)
        pan_l = np.clip(0.5 + (lfo_cos * 0.5 * self.width), 0.0, 1.0)
        pan_r = np.clip(0.5 - (lfo_cos * 0.5 * self.width), 0.0, 1.0)
        
        # Convert to stereo if mono
        if len(data.shape) == 1 or data.shape[0] == 1:
            in_data = data[0] if len(data.shape) > 1 else data
            left = in_data * tremolo * pan_l
            right = in_data * tremolo * pan_r
            wet = np.vstack((left, right))
            dry = np.vstack((in_data, in_data))
        else:
            left = data[0] * tremolo * pan_l
            right = data[1] * tremolo * pan_r
            wet = np.vstack((left, right))
            dry = data
            
        return (dry * (1.0 - self.mix)) + (wet * self.mix)

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
        self.effects_chain = [] # SR DEV: The new Hybrid List
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
        # Global instance limits and buffers
        self.master_gain = 1.0
        
        # --- STOMPBOX OVERRIDE SYSTEM (DAISY CHAIN) ---
        self.pre_amp_chain = []
        self.post_amp_chain = []
        
        # We store the raw state (list of dicts) from the frontend
        self.manual_pedals_state = {
            "pre": [],
            "post": []
        }
        
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

    def create_stompbox(self, type_id, params):
        """Factory for the 15 boutique multi-parameter stompboxes."""
        def norm(key):
            # Helper to grab parameter 0-100 and normalize to 0.0 - 1.0
            return params.get(key, 50) / 100.0

        if type_id == "comp": 
            return Compressor(
                threshold_db=-10.0 - (norm('sustain') * 30.0), 
                ratio=2.0 + (norm('sustain') * 18.0), 
                attack_ms=1.0 + (norm('attack') * 10.0)
            ) # Note: 'level' is not directly a Compressor arg, could add Gain in chain, but simple is fine.
            
        elif type_id == "od": 
            return Chain([
                HighShelfFilter(cutoff_frequency_hz=1500, gain_db=(norm('tone') - 0.5) * 12.0),
                Distortion(drive_db=5.0 + (norm('drive') * 30.0))
            ])
            
        elif type_id == "fuzz": 
            return AsymmetricDistortion(drive_db=20.0 + (norm('fuzz') * 50.0), asymmetry=0.5 + (norm('fuzz') * 0.4))
            
        elif type_id == "ts9": 
            return Chain([
                PeakFilter(cutoff_frequency_hz=800, gain_db=3.0 + (norm('tone') * 6.0)),
                Distortion(drive_db=5.0 + (norm('drive') * 25.0))
            ])
            
        elif type_id == "klon": 
            return Chain([
                Distortion(drive_db=2.0 + (norm('gain') * 15.0)),
                HighShelfFilter(cutoff_frequency_hz=2000, gain_db=(norm('treble') - 0.5) * 15.0)
            ])
            
        elif type_id == "rat": 
            return Chain([
                Distortion(drive_db=15.0 + (norm('dist') * 45.0)),
                # Rat filter acts backwards: high value = high cut
                LowpassFilter(cutoff_frequency_hz=10000.0 - (norm('filter') * 9000.0))
            ])
            
        elif type_id == "muff": 
            # Pi Fuzz tone scoop
            t = norm('tone')
            return Chain([
                Distortion(drive_db=30.0 + (norm('sustain') * 30.0)),
                LowpassFilter(cutoff_frequency_hz=3000.0 + (t * 5000.0)),
                HighpassFilter(cutoff_frequency_hz=100.0 + (t * 500.0))
            ])
            
        elif type_id == "octavia": 
            return Chain([
                PitchShift(semitones=12),
                Distortion(drive_db=20.0 + (norm('fuzz') * 40.0))
            ])
            
        elif type_id == "chorus": 
            return Chorus(rate_hz=0.1 + (norm('rate') * 5.0), depth=0.05 + (norm('depth') * 0.25), mix=0.5)
            
        elif type_id == "delay": 
            return Delay(
                delay_seconds=0.05 + (norm('time') * 0.95), 
                feedback=norm('repeats') * 0.85, # Cap at 85% to prevent blowout
                mix=norm('mix') * 0.5 # Cap at 0.5 so 100% UI means 50/50 blend (prevents muting dry signal)
            )
            
        elif type_id == "phaser": 
            return Phaser(rate_hz=0.1 + (norm('speed') * 8.0), depth=0.8)
            
        elif type_id == "flanger": 
            return Chorus(
                rate_hz=0.1 + (norm('rate') * 4.0), 
                depth=0.1 + (norm('depth') * 0.4), 
                centre_delay_ms=1.0 + (norm('manual') * 5.0),
                mix=0.5 + (norm('res') * 0.5) # Simulating feedback with mix for now
            )
            
        elif type_id == "vibe": 
            return Phaser(rate_hz=0.5 + (norm('speed') * 6.0), depth=0.5 + (norm('intensity') * 0.5), centre_frequency_hz=800)
            
        elif type_id == "reverb": 
            return Chain([
                Reverb(room_size=norm('dwell'), damping=1.0 - norm('tone'), wet_level=norm('mixer')),
                HighShelfFilter(cutoff_frequency_hz=3000, gain_db=(norm('tone') - 0.5) * 12.0)
            ])
            
        elif type_id == "gate": 
            return NoiseGate(threshold_db=-80.0 + (norm('threshold') * 80.0), release_ms=10.0 + (norm('decay') * 490.0))
            
        elif type_id == "leslie": 
            # Returns a list of effects to simulate the Rotary Speaker
            return [
                Chorus(rate_hz=0.5 + (norm('speed') * 7.5), depth=0.3, mix=0.4),
                SpatialRotary(speed_hz=0.5 + (norm('speed') * 7.5), width=0.2 + (norm('width') * 0.8), mix=norm('mix'))
            ]
        
        return Gain(gain_db=0.0)

    def update_daisy_chain(self, pre_pedals, post_pedals):
        """Rebuilds the pre and post amp chains based on UI state."""
        self.manual_pedals_state = {"pre": pre_pedals, "post": post_pedals}
        
        new_pre = []
        for p in pre_pedals:
            if p.get("enabled", True):
                fx = self.create_stompbox(p["type"], p["params"])
                if isinstance(fx, list): new_pre.extend(fx)
                else: new_pre.append(fx)
                
        new_post = []
        for p in post_pedals:
            if p.get("enabled", True):
                fx = self.create_stompbox(p["type"], p["params"])
                if isinstance(fx, list): new_post.extend(fx)
                else: new_post.append(fx)
                
        self.pre_amp_chain = new_pre
        self.post_amp_chain = new_post
        return self.manual_pedals_state

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
                # Flaw 2 Fix: Handle parameter name mismatch for Pedalboard filters
                if "cutoff_hz" in kwargs and fx_type in ["HighpassFilter", "LowpassFilter", "PeakFilter", "HighShelfFilter", "LowShelfFilter", "LadderFilter"]:
                    kwargs["cutoff_frequency_hz"] = kwargs.pop("cutoff_hz")

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
                # CUSTOM DSP COMPONENTS
                elif fx_type == "AsymmetricDistortion":
                    effects_list.append(AsymmetricDistortion(**kwargs))
                elif fx_type == "PowerAmpSag":
                    effects_list.append(PowerAmpSag(**kwargs))
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
                    # Look for ANY .nam file in the plugins directory
                    plugins_dir = os.path.join(os.path.dirname(__file__), self.plugins_dir)
                    nam_files = [f for f in os.listdir(plugins_dir) if f.endswith('.nam')] if os.path.exists(plugins_dir) else []
                    
                    if nam_files:
                        # Load the first .nam file found
                        nam_path = os.path.join(plugins_dir, nam_files[0])
                        effects_list.append(NativeNAM(nam_path))
                    else:
                        print("AudioEngine: No .nam file found in plugins directory. Falling back to algorithmic amp.")
                        # SR DEV: High-fidelity algorithmic amp sim fallback
                        effects_list.append(Distortion(drive_db=25))
                        effects_list.append(LadderFilter(cutoff_hz=3500, resonance=0.2))
                    
                    # 3. Cabinet Simulation (Always apply to both neural and algorithmic unless overridden)
                    cab_ir_path = os.path.join(os.path.dirname(__file__), self.irs_dir, "vintage_4x12.wav")
                    if os.path.exists(cab_ir_path):
                        effects_list.append(Convolution(cab_ir_path, 1.0))
                    else:
                        # Fallback Algorithmic 4x12 Cabinet (Eliminates digital fizz)
                        effects_list.extend([
                            LowShelfFilter(cutoff_frequency_hz=100, gain_db=-3.0),
                            HighpassFilter(cutoff_frequency_hz=80),
                            PeakFilter(cutoff_frequency_hz=2500, gain_db=2.0, q=1.0),
                            LowpassFilter(cutoff_frequency_hz=5000)
                        ])
                    # 4. Final Gain Stage for 'Amp' feel
                    effects_list.append(Gain(gain_db=6))
            except Exception as e:
                print(f"AudioEngine: Error instantiating {fx_type} with args {kwargs}: {e}")
        return effects_list

    def build_dynamic_board(self, chain_json):
        # Clear the sample stack for the new preset
        self.active_samples = []
        # SR DEV: We now store effects as a list to allow Custom Python plugins
        self.effects_chain = self._build_fx_list(chain_json)
        
        # EAR PROTECTION & MASTERING BUS
        self.effects_chain.append(Compressor(threshold_db=-6.0, ratio=2.0, attack_ms=10.0))
        self.effects_chain.append(Limiter(threshold_db=-1.0))
        
        # Initialize standard plugins
        for fx in self.effects_chain:
            if not hasattr(fx, 'process'):
                try:
                    fx(np.zeros((1, 128), dtype=np.float32), self.sample_rate, reset=True)
                except: pass

        self.active_preset = "Custom Generative AI Chain"
        print(f"AudioEngine: Built hybrid board with {len(self.effects_chain)} plugins.")
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

    def _process_plugin(self, fx, signal):
        """Helper to process a signal through a single plugin natively handling stereo arrays."""
        # Ensure signal is 2D: [channels, frames]
        if len(signal.shape) == 1:
            dry = np.expand_dims(signal, axis=0)
        else:
            dry = signal
            
        if isinstance(fx, (AsymmetricDistortion, PowerAmpSag, SpatialRotary)):
            return fx.process(dry)
        else:
            wet = fx(dry, self.sample_rate, reset=False)
            return wet

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
        if len(self.active_samples) > 0:
            current_peak = np.max(np.abs(mono_input))
            if current_peak > (rms * 3.0) and current_peak > 0.02:
                sample = self.active_samples[0]
                if sample["ptr"] == 0:
                    sample["ptr"] = 1
        
        # 5. NDE (Neural Dynamic Expression) - Dynamic Saturation
        if self.nde_enabled:
            for plugin in self.effects_chain:
                if hasattr(plugin, 'drive_db') and not isinstance(plugin, AsymmetricDistortion):
                    try:
                        plugin.drive_db = 10 + (rms * 60 * self.nde_sensitivity)
                    except: pass
        
        # 6. PAGH RESYNTHESIS (Phase-Aligned Breakthrough)
        if self.pagh_enabled and self.detected_pitch:
            t = np.linspace(0, frames/self.sample_rate, frames, endpoint=False)
            freq = self.detected_pitch * self.pagh_ratio
            phase = self.phase_acc + 2 * np.pi * freq * t
            np.sin(phase, out=self.mixer_buffer)
            self.mixer_buffer *= (rms * 10.0)
            self.phase_acc = (phase[-1] + 2 * np.pi * freq / self.sample_rate) % (2 * np.pi)
        else:
            self.mixer_buffer.fill(0)

        # 7. Final DSP Chain - DAISY CHAIN OVERRIDE
        processed = mono_input
        
        # 7a. Pre-Amp Daisy Chain
        for fx in self.pre_amp_chain:
            try: processed = self._process_plugin(fx, processed)
            except: pass

        # 7b. AI Generative Chain
        for fx in self.effects_chain:
            try: processed = self._process_plugin(fx, processed)
            except: pass

        # 7c. Post-Amp Daisy Chain
        for fx in self.post_amp_chain:
            try: processed = self._process_plugin(fx, processed)
            except: pass

        # 8. Output Prep (Stereo Mirror + Mixer)
        try:
            # Combine wet signal with PAGH mixer buffer
            if len(processed.shape) > 1 and processed.shape[0] == 2:
                # True Stereo output
                final_out_l = (processed[0] + self.mixer_buffer) * self.master_gain
                final_out_r = (processed[1] + self.mixer_buffer) * self.master_gain
                np.copyto(outdata[:, 0], final_out_l)
                np.copyto(outdata[:, 1], final_out_r)
            else:
                # Mono output duplicated to L/R
                final_out = (processed.squeeze() + self.mixer_buffer) * self.master_gain
                np.copyto(outdata[:, 0], final_out)
                np.copyto(outdata[:, 1], final_out)
            
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

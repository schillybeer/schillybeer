import numpy as np
import os
import sounddevice as sd
from pedalboard import Pedalboard, Chorus, Reverb, Distortion, Gain, Phaser, Delay, PitchShift, Compressor, HighpassFilter, LowpassFilter, Limiter, Bitcrush

class AudioEngine:
    def __init__(self):
        self.active_preset = "None"
        self.is_playing = False
        self.stream = None
        self.sample_rate = 44100
        self.blocksize = 1024  # Buffer size for stability
        self.board = Pedalboard()
        self.plugins_dir = "plugins"
        self.irs_dir = "irs"
        self.active_sample = None
        self.active_sample_name = None
        self.sample_ptr = 0
        self.detected_pitch = 440.0 # Default A4
        
        # Mapping of samples to their "natural" base frequency
        self.sample_base_freqs = {
            "synth_stab.wav": 110.0, # A2
            "orch_hit.wav": 110.0,   # A2
            "lofi_piano.wav": 261.63, # C4
            "808_kick.wav": 55.0,    # A1
            "laser.wav": 1000.0,     # Reference
            "coin.wav": 1318.51,     # E6
            "wow.wav": 440.0,        # A4
            "robot_hey.wav": 150.0   # Base buzzer freq
        }
        
        # We will build our presets dynamically. If the user has downloaded the VST3/IR, we use the Pro sound.
        # Otherwise, we fall back to the basic algorithms.
        self.presets = self._build_presets()

    def _build_presets(self):
        import os
        from pedalboard import load_plugin, Convolution
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
            kwargs = {k: v for k, v in fx.items() if k not in ["effect", "chains"]}
            
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
                elif fx_type == "Convolution":
                    from pedalboard import Convolution
                    ir_name = kwargs.get("ir_name", "vintage_4x12.wav")
                    mix = kwargs.get("mix", 1.0)
                    ir_path = os.path.join(os.path.dirname(__file__), self.irs_dir, ir_name)
                    if os.path.exists(ir_path):
                        effects_list.append(Convolution(ir_path, mix=mix))
                    else:
                        print(f"AudioEngine ERROR: IR file NOT FOUND at {ir_path}")
                elif fx_type == "Sampler":
                    import soundfile as sf
                    sample_name = kwargs.get("sample_name", "fart_resonance.wav")
                    sample_path = os.path.join(os.path.dirname(__file__), self.irs_dir, sample_name)
                    if os.path.exists(sample_path):
                        data, sr = sf.read(sample_path)
                        # Ensure mono
                        if len(data.shape) > 1: data = data[:, 0]
                        self.active_sample = data.astype(np.float32)
                        self.active_sample_name = sample_name
                        self.sample_ptr = 0
                        print(f"AudioEngine: Loaded sample {sample_name} into Sampler.")
                elif fx_type == "NAM_Amp":
                    import os
                    from pedalboard import load_plugin, Convolution
                    system_nam_path = r"C:\Program Files\Common Files\VST3\NeuralAmpModeler.vst3\Contents\x86_64-win\NeuralAmpModeler.vst3"
                    cab_ir_path = os.path.join(self.irs_dir, "vintage_4x12.wav")
                    if os.path.exists(system_nam_path) and os.path.exists(cab_ir_path):
                        nam_vst = load_plugin(system_nam_path)
                        cab_sim = Convolution(cab_ir_path, 1.0)
                        effects_list.append(nam_vst)
                        effects_list.append(cab_sim)
            except Exception as e:
                print(f"AudioEngine: Error instantiating {fx_type} with args {kwargs}: {e}")
        return effects_list

    def build_dynamic_board(self, chain_json):
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

    def _estimate_pitch(self, signal):
        """Estimate fundamental frequency using autocorrelation."""
        if np.max(np.abs(signal)) < 0.003:
            return None
        
        # Calculate autocorrelation
        corr = np.correlate(signal, signal, mode='full')
        corr = corr[len(corr)//2:]
        
        # Find first peak after first zero-crossing
        # This is a classic simple pitch tracker
        d = np.diff(corr)
        positive_slopes = np.where(d > 0)[0]
        if len(positive_slopes) == 0:
            return None
        
        start = positive_slopes[0]
        peak = np.argmax(corr[start:]) + start
        
        if peak > 0:
            freq = self.sample_rate / peak
            # Filter for realistic guitar range (approx 80Hz to 1200Hz)
            if 70 < freq < 1500:
                return freq
        return None

    def audio_callback(self, indata, outdata, frames, time, status):
        if status:
            pass # Suppress print to avoid console spam
            
        # sounddevice gives us shape (frames, channels), pedalboard wants (channels, frames)
        mono_input = indata[:, 0]
        
        # Reshape for pedalboard (1 channel, N frames)
        dry_signal = np.expand_dims(mono_input, axis=0)
        
        try:
            # PITCH TRACKING: Detect guitar pitch for the Tuner (ALWAYS active)
            new_pitch = self._estimate_pitch(mono_input)
            if new_pitch:
                if self.detected_pitch is None:
                    self.detected_pitch = new_pitch
                else:
                    # Balanced smoothing (0.85) for responsive but stable needle
                    self.detected_pitch = 0.85 * self.detected_pitch + 0.15 * new_pitch
            elif np.max(np.abs(mono_input)) < 0.003: # Lower threshold to allow for note decay
                # Reset if silent
                self.detected_pitch = None
            
            # Process the audio through the active pedalboard
            wet_signal = self.board(dry_signal, self.sample_rate, reset=False)
            
            # SAMPLER MODE: If a sample is active, overlay it onto the wet signal!
            if self.active_sample is not None:
                # Calculate the envelope (amplitude) of the dry guitar signal
                envelope = np.abs(mono_input)
                
                # USE PEAK DETECTION for maximum impact on attacks
                # Increase sensitivity to 15.0 for a "stronger" feel
                env_level = np.max(envelope) * 15.0
                
                # NOISE GATE: Kill background noise so the samples "pop"
                if env_level < 0.2: 
                    env_level = 0
                
                # Calculate playback speed ratio based on detected pitch
                base_freq = self.sample_base_freqs.get(self.active_sample_name, 440.0)
                speed_ratio = self.detected_pitch / base_freq
                
                # Get the next chunk of the sample with dynamic resampling
                chunk_size = len(mono_input)
                
                # We need chunk_size * speed_ratio samples from the source
                source_frames = int(chunk_size * speed_ratio)
                end_ptr = self.sample_ptr + source_frames
                
                if end_ptr > len(self.active_sample):
                    # Loop the sample
                    raw_chunk = self.active_sample[self.sample_ptr:]
                    remaining = source_frames - len(raw_chunk)
                    raw_chunk = np.concatenate([raw_chunk, self.active_sample[:remaining]])
                    self.sample_ptr = remaining
                else:
                    raw_chunk = self.active_sample[self.sample_ptr:end_ptr]
                    self.sample_ptr = end_ptr
                
                # Resample raw_chunk to chunk_size using linear interpolation
                xp = np.linspace(0, 1, len(raw_chunk))
                x = np.linspace(0, 1, chunk_size)
                sample_chunk = np.interp(x, xp, raw_chunk)

                # MIX: Reduce guitar volume (0.05) to make the sample (the "instrument") dominate
                wet_signal[0] = (wet_signal[0] * 0.05) + (sample_chunk * env_level)

            # Prevent shape broadcast crashes if a plugin swallows the audio block
            if wet_signal.shape[1] != outdata.shape[0]:
                outdata.fill(0)
                return
                
            out_channels = outdata.shape[1]
            if out_channels == 2:
                outdata[:, 0] = wet_signal[0] # Left
                outdata[:, 1] = wet_signal[0] # Right
            else:
                outdata[:, 0] = wet_signal[0] # Mono
        except Exception as e:
            import traceback
            print(f"AUDIO THREAD ERROR: {e}")
            # If anything crashes in the audio thread, output silence to prevent a hard CFFI crash
            outdata.fill(0)

    def start(self):
        if not self.is_playing:
            print("AudioEngine: Starting LIVE audio stream on default devices...")
            
            # Find the default WASAPI devices
            try:
                wasapi_api_info = None
                for api in sd.query_hostapis():
                    if 'WASAPI' in api['name']:
                        wasapi_api_info = api
                        break
                
                input_device = wasapi_api_info['default_input_device'] if wasapi_api_info else None
                output_device = wasapi_api_info['default_output_device'] if wasapi_api_info else None

                self.stream = sd.Stream(
                    samplerate=self.sample_rate,
                    blocksize=128,
                    latency='low',
                    device=(input_device, output_device) if input_device is not None else None,
                    channels=(1, 2),
                    callback=self.audio_callback
                )
                print("AudioEngine: WASAPI Driver engaged (Low Latency Mode)!")
            except Exception as e:
                print(f"AudioEngine: WASAPI failed, falling back to OS defaults. ({e})")
                self.stream = sd.Stream(
                    samplerate=self.sample_rate,
                    blocksize=128,
                    latency='low',
                    device=None, 
                    channels=(1, 2),
                    callback=self.audio_callback
                )
            self.stream.start()
            self.is_playing = True

    def stop(self):
        if self.is_playing and self.stream:
            self.stream.stop()
            self.stream.close()
            self.is_playing = False

# Global instance
engine = AudioEngine()

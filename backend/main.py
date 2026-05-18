import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
from audio_engine import engine
from tone_library import ARTIST_PRESETS

# Load environment variables from .env file (if it exists)
load_dotenv()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the audio engine when the server starts
    engine.start()
    yield
    # Stop the engine when the server shuts down
    engine.stop()

app = FastAPI(
    title="Schillybeer Brain API", 
    description="AI Guitar Pedal Dashboard API",
    lifespan=lifespan
)

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock database of available presets in our "Audio Engine"
AVAILABLE_PRESETS = [
    "Fender_Twin_Sparkle_Clean",
    "Marshall_JCM800_Heavy_Crunch",
    "Mesa_Boogie_Modern_Metal",
    "Vox_AC30_British_Invasion",
    "Acoustic_Simulator_Bright",
    "Fuzz_Face_Hendrix_Lead",
    "Roland_JC120_Chorus_Clean"
]

class TonePrompt(BaseModel):
    prompt: str

class PresetChange(BaseModel):
    preset_name: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Schillybeer Brain is running."}

def freq_to_note(freq):
    if not freq or freq <= 0:
        return None, 0
    
    import math
    # A4 = 440Hz, MIDI 69
    n = 12 * math.log2(freq / 440.0) + 69
    midi_note = round(n)
    cents = (n - midi_note) * 100
    
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    name = note_names[midi_note % 12]
    
    return f"{name}{octave}", round(cents, 1)

@app.get("/api/tuner")
def get_tuner():
    pitch = getattr(engine, 'detected_pitch', None)
    if pitch is None:
        return {"note": "--", "cents": 0, "freq": 0}
    
    note, cents = freq_to_note(pitch)
    return {
        "note": note if note else "--",
        "cents": cents,
        "freq": round(pitch, 1),
        "is_tuned": abs(cents) < 5
    }

@app.post("/api/tone/prompt")
def prompt_tone(request: TonePrompt):
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    client = genai.Client(api_key=api_key)
    
    system_instruction = """
    You are the Lead Sound Librarian and Senior DSP Engineer for the Schillybeer Quantum Rig.
    Your goal is to provide ultra-accurate guitar tones by using verified 'Gold Standard' templates as a base layer.
    
    MASTER TONE LIBRARY (Reference these for artist requests):
    {artist_library_summary}
    
    AVAILABLE DSP COMPONENTS:
    - Compressor(threshold_db, ratio): Use at start for consistency.
    - Distortion(drive_db): High-gain saturation.
    - NAM_Amp(): High-end Algorithmic Amp. ALWAYS use this for realistic amp tones.
    - Convolution(ir_name, mix): Cabinet simulation ('vintage_4x12.wav').
    - Chorus(rate_hz, depth, mix): Modulation.
    - Reverb(room_size, wet_level): Spatial depth.
    - Delay(delay_seconds, feedback, mix): Echo.
    - PitchShift(semitones): Harmonic shifting.
    - Gain(gain_db): Final level adjustment.
    - PeakFilter(cutoff_hz, gain_db, q): Surgical frequency adjustment.
    - LowpassFilter/HighpassFilter: Tonal balancing.
    - Phaser(rate_hz, mix): Movement.
    - Sampler(sample_name): Trigger sound effects (e.g., 'laser.wav', 'explosion.wav', 'space_drone.wav').
    
    PROFESSIONAL WORKFLOW:
    1. If the user mentions a specific artist (e.g., 'Ted Nugent', 'SRV'), START with their verified chain from the library.
    2. TONE MORPHING: If multiple artists are mentioned (e.g., 'Nugent + B.B. King'), blend their key characteristics (e.g., Nugent's bite + King's smooth mid-hump).
    3. CREATIVE OVERLAY: If the user adds a theme (e.g., 'in space', 'with lasers'), keep the artist's base tone but add the thematic DSP (e.g., Large Reverb + Sampler('laser.wav')).
    4. PRECISION: Use technical terms in your 'message' to confirm you've matched the reference template.
    
    Return ONLY a raw JSON object:
    "suggested_preset": Descriptive name.
    "chain": array of effect objects.
    "message": Technical explanation of how you matched the reference and added the 'special sauce'.
    """

    try:
        # Dynamically inject the artist library summary
        library_summary = "\n".join([f"- {name}: {info['description']}" for name, info in ARTIST_PRESETS.items()])
        formatted_instruction = system_instruction.format(artist_library_summary=library_summary)
        
        # Upgraded to Gemini 3 Flash for cutting-edge DSP chain generation
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=request.prompt,
            config=types.GenerateContentConfig(
                system_instruction=formatted_instruction,
                temperature=0.2, # Low temperature for more deterministic preset mapping
            )
        )
        
        # Parse the JSON response
        result_text = response.text.strip()
        # Clean up in case the model returns markdown code blocks despite instructions
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()

        data = json.loads(result_text)
        data["status"] = "success"
        
        # ACTUALLY change the sound in our audio engine!
        if "chain" in data:
            engine.build_dynamic_board(data["chain"])
        elif "suggested_preset" in data:
            # Fallback to old behavior just in case
            engine.change_preset(data["suggested_preset"])
            
        return data

    except Exception as e:
        error_msg = str(e)
        print(f"Gemini API Error: {error_msg}")
        
        # Local Fallback Matcher
        prompt_lower = request.prompt.lower()
        fallback_name = "Default Tone"
        fallback_chain = [{"effect": "Reverb", "room_size": 0.5}]
        
        reason = "Unknown Error"
        if "429" in error_msg or "quota" in error_msg.lower():
            reason = "Quota Exhausted (429)"
        elif "503" in error_msg or "overloaded" in error_msg.lower():
            reason = "Server Overloaded (503)"
        elif "404" in error_msg or "not found" in error_msg.lower():
            reason = "Model Not Found (404)"
        else:
            reason = f"Error: {error_msg[:60]}..."
            
        message = f"API Issue [{reason}]: Used Local Offline Brain!"
        
        if "organ" in prompt_lower or "church" in prompt_lower:
            fallback_name = "Gothic Pipe Organ"
            fallback_chain = [
                {"effect": "Mix", "chains": [
                    [{"effect": "PitchShift", "semitones": 12}],
                    [{"effect": "PitchShift", "semitones": -12}],
                    [] # Pass dry signal through as well
                ]}, 
                {"effect": "Chorus", "rate_hz": 3.0, "depth": 0.8},
                {"effect": "Reverb", "room_size": 0.9}
            ]
        elif "12" in prompt_lower or "string" in prompt_lower:
            fallback_name = "12-String Simulator"
            fallback_chain = [
                {"effect": "Mix", "chains": [
                    [], # Dry
                    [{"effect": "PitchShift", "semitones": 12}] # Octave Up
                ]},
                {"effect": "Chorus", "rate_hz": 1.5, "depth": 0.2, "mix": 0.3},
                {"effect": "Reverb", "room_size": 0.3, "wet_level": 0.2}
            ]
        elif "metal" in prompt_lower or "heavy" in prompt_lower or "distort" in prompt_lower:
            fallback_name = "Heavy Metal (Offline)"
            fallback_chain = [
                {"effect": "Distortion", "drive_db": 35},
                {"effect": "Gain", "gain_db": 10},
                {"effect": "Reverb", "room_size": 0.4}
            ]
        elif "opera" in prompt_lower or "singer" in prompt_lower:
            fallback_name = "Soprano Vocoder"
            fallback_chain = [{"effect": "Phaser", "rate_hz": 5.0}, {"effect": "Distortion", "drive_db": 10}, {"effect": "Reverb", "room_size": 0.8}]
        elif "fart" in prompt_lower or "stomach" in prompt_lower or "flatulence" in prompt_lower:
            fallback_name = "80s Fart Sampler (Offline)"
            fallback_chain = [
                {"effect": "Sampler", "sample_name": "fart_resonance.wav"},
                {"effect": "Distortion", "drive_db": 10},
                {"effect": "Gain", "gain_db": 10}
            ]
            
        engine.build_dynamic_board(fallback_chain)
        
        return {
            "suggested_preset": fallback_name,
            "chain": fallback_chain,
            "message": message,
            "status": "success"
        }

@app.post("/api/tone/preset")
def change_preset(request: PresetChange):
    if not engine.change_preset(request.preset_name):
        raise HTTPException(status_code=400, detail="Preset not found in Audio Engine.")
    
    return {
        "status": "success", 
        "message": f"Successfully loaded preset: {request.preset_name}"
    }

@app.get("/api/tones/library")
def get_tone_library():
    """Returns the list of available verified artist templates."""
    return {
        "artists": [
            {"id": name, "name": name.replace("_", " ").title(), "description": info["description"]}
            for name, info in ARTIST_PRESETS.items()
        ]
    }

@app.post("/api/engine/reset")
def reset_engine():
    """Returns the rig to its fresh launch settings."""
    engine.build_dynamic_board([])
    engine.update_daisy_chain([], [])
    engine.active_preset = "None"
    return {"status": "success", "message": "Rig initialized"}

@app.post("/api/engine/mute")
def toggle_mute(request: dict):
    """Mutes or unmutes the master output."""
    mute = request.get("mute", False)
    engine.master_gain = 0.0 if mute else 1.0
    return {"status": "success", "muted": mute}

@app.get("/api/tones/artist/{artist_id}")
def get_artist_rig(artist_id: str):
    """Fetches the visual stompbox rig for an artist and initializes the Amp block."""
    if artist_id not in ARTIST_PRESETS:
        raise HTTPException(status_code=404, detail="Artist not found")
        
    preset = ARTIST_PRESETS[artist_id]
    
    # Load the Core Amp and Cab block into the backend
    amp_chain = [
        {"effect": "NAM_Amp", "params": {}},
        {"effect": "Convolution", "ir_name": "vintage_4x12.wav", "mix": 1.0}
    ]
    engine.build_dynamic_board(amp_chain)
    engine.active_preset = artist_id.replace("_", " ").title()
    
    return {
        "status": "success",
        "visual_rig": preset.get("visual_rig", {"pre": [], "post": []})
    }

@app.post("/api/engine/toggle")
def toggle_engine_feature(request: dict):
    feature = request.get("feature")
    if feature == "nde":
        engine.nde_enabled = not engine.nde_enabled
        return {"status": "success", "feature": "nde", "state": engine.nde_enabled}
    elif feature == "pagh":
        engine.pagh_enabled = not engine.pagh_enabled
        return {"status": "success", "feature": "pagh", "state": engine.pagh_enabled}
    return {"status": "error", "message": "Unknown feature"}

# --- STOMPBOX OVERRIDE API ---

class PedalState(BaseModel):
    id: str
    type: str
    enabled: bool
    params: dict[str, float]

class ChainUpdate(BaseModel):
    pre: list[PedalState]
    post: list[PedalState]

@app.get("/api/pedals/state")
def get_pedals_state():
    return engine.manual_pedals_state

@app.post("/api/pedals/update")
def update_pedal(update: ChainUpdate):
    try:
        new_state = engine.update_daisy_chain(
            pre_pedals=[p.dict() for p in update.pre],
            post_pedals=[p.dict() for p in update.post]
        )
        return {"status": "success", "state": new_state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/telemetry")
async def get_telemetry():
    """Expose high-speed engine telemetry to the dashboard."""
    # Ensure all telemetry values are serializable
    safe_telemetry = {}
    for k, v in engine.telemetry.items():
        if hasattr(v, "item"):
            safe_telemetry[k] = float(v.item())
        else:
            try:
                safe_telemetry[k] = float(v)
            except:
                safe_telemetry[k] = v
    return safe_telemetry

if __name__ == "__main__":
    import uvicorn
    # Optimized for low-latency performance
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)

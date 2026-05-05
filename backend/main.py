import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
from audio_engine import engine

# Load environment variables from .env file (if it exists)
load_dotenv()

app = FastAPI(title="Schillybeer Brain API", description="AI Guitar Pedal Dashboard API")

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
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set on the server.")

    client = genai.Client(api_key=api_key)
    
    system_instruction = """
    You are the brain of a smart guitar pedal called Schillybeer.
    The user will describe a guitar tone they want (e.g., 'church organ', '12 string guitar', '80s Metallica').
    You must dynamically build a digital signal processing (DSP) chain to create this sound using the following available effects:
    - Chorus(rate_hz, depth, mix)
    - Reverb(room_size, wet_level, dry_level)
    - Distortion(drive_db) (CRUCIAL: Use this for ALL heavy metal, rock, and crunch tones!)
    - Gain(gain_db) (Use this AFTER distortion to make it loud and aggressive!)
    - Phaser(rate_hz, mix)
    - Delay(delay_seconds, feedback, mix)
    - PitchShift(semitones)
    - LowpassFilter(cutoff_frequency_hz)
    - Bitcrush(bit_depth) (PERFECT for that 80s lo-fi floppy disk sound. Use bit_depth=8 for maximum crunch!)
    - Convolution(ir_name, mix) (Texturizes the guitar with a snapshot.)
    - Sampler(sample_name) (TRULY COMICAL: The guitar triggers and plays the actual audio file like an 80s keyboard sampler!)
    - Mix(chains) (takes an array of arrays. Crucial for blending octaves!)
    
    NON-MUSICAL SOUND LIBRARY:
    - 'fart_resonance.wav': Use with Sampler() for a comical farting guitar.
    - 'laser.wav', 'explosion.wav', 'coin.wav', 'powerup.wav': Retro arcade pack.
    - 'wow.wav', 'robot_hey.wav', 'hey_hit.wav': Vocal effects.
    - '808_kick.wav', '808_snare.wav', 'cowbell.wav': Drum machine pack.
    - 'synth_stab.wav', 'orch_hit.wav': Classic 80s sampler hits.
    - 'lofi_piano.wav', 'lofi_strings.wav': Instrument pack.
    - 'washing_machine.wav', 'robotic_drone.wav', 'metallic_clang.wav', 'alien_chatter.wav'
    
    AUDIO ENGINEERING RULES:
    1. For COMICAL Farts: ALWAYS use Sampler('fart_resonance.wav').
    2. For Retro Arcade: Use Sampler('laser.wav' or 'coin.wav') + Delay(delay_seconds=0.1, feedback=0.4, mix=0.5).
    3. For 80s Sampler Feel: Use Sampler('synth_stab.wav' or 'orch_hit.wav') + Bitcrush(bit_depth=8).
    4. For Heavy Metal: Use Distortion(drive_db=30-50) + Gain(gain_db=15).
    5. For 12-String: Use Mix(chains=[[], [{"effect": "PitchShift", "semitones": 12}]]).
    6. PitchShift is 100% wet. ALWAYS use Mix() for parallel octaves.
    7. Be Bold: Crank the mix and wet_level parameters to 0.7-1.0 for wacky effects!
    
    Return ONLY a raw JSON object with exactly three keys:
    "suggested_preset": a short, creative 2-4 word name for the custom tone you just built.
    "chain": an array of effect objects. 
    "message": a short, fun 1-sentence confirmation.
    """

    try:
        # Upgraded to Gemini 3 Flash for cutting-edge DSP chain generation
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=request.prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
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

# Start the audio engine when the server starts
@app.on_event("startup")
def startup_event():
    engine.load_di_track("di_loop.wav")
    engine.start()

@app.on_event("shutdown")
def shutdown_event():
    engine.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

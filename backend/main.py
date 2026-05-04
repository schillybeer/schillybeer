from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Schillybeer Brain API", description="AI Guitar Pedal Dashboard API")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TonePrompt(BaseModel):
    prompt: str

class PresetChange(BaseModel):
    preset_name: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Schillybeer Brain is running."}

@app.post("/api/tone/prompt")
def prompt_tone(request: TonePrompt):
    # Placeholder for LLM logic to convert prompt -> plugin preset/settings
    return {
        "status": "success",
        "message": f"Received prompt: '{request.prompt}'. Searching for best tone...",
        "suggested_preset": "Marshall_JCM800_Lead"
    }

@app.post("/api/tone/preset")
def change_preset(request: PresetChange):
    # Placeholder for local DAW/NAM control logic (e.g., via MIDI or OSC)
    return {
        "status": "success", 
        "message": f"Successfully loaded preset: {request.preset_name}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

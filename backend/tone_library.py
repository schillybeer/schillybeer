# Schillybeer Master Tone Library: Verified Pro-Audio Signal Chains
# This acts as the "Source of Truth" for the AI Sound Librarian.

# visual_rig params are 0-100 scale

ARTIST_PRESETS = {
    "TED_NUGENT": {
        "description": "The raw, biting mid-range of the Byrdland. High-output saturation with a focused mid-peak.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -15, "ratio": 3.0, "attack_ms": 5.0},
            {"effect": "Distortion", "drive_db": 32},
            {"effect": "PeakFilter", "cutoff_hz": 2800, "gain_db": 6, "q": 1.5},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "LowShelfFilter", "cutoff_hz": 150, "gain_db": -3},
            {"effect": "Gain", "gain_db": 4}
        ],
        "visual_rig": {
            "pre": [
                {"type": "comp", "params": {"sustain": 60, "attack": 40, "level": 70}},
                {"type": "od", "params": {"drive": 80, "tone": 60, "level": 75}}
            ],
            "post": []
        }
    },
    "STEVIE_RAY_VAUGHAN": {
        "description": "Texas Flood blues. Mid-hump overdrive into a glass-shattering clean amp.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -20, "ratio": 4.0},
            {"effect": "Distortion", "drive_db": 12},
            {"effect": "PeakFilter", "cutoff_hz": 720, "gain_db": 4, "q": 0.7},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Reverb", "room_size": 0.35, "wet_level": 0.2},
            {"effect": "HighShelfFilter", "cutoff_hz": 4000, "gain_db": 3}
        ],
        "visual_rig": {
            "pre": [
                {"type": "comp", "params": {"sustain": 50, "attack": 50, "level": 60}},
                {"type": "ts9", "params": {"drive": 40, "tone": 65, "level": 80}}
            ],
            "post": [
                {"type": "reverb", "params": {"dwell": 35, "tone": 70, "mixer": 30}}
            ]
        }
    },
    "DAVID_GILMOUR": {
        "description": "Epic, ethereal sustain. Fuzz-driven leads with complex modulation and delay.",
        "chain": [
            {"effect": "Distortion", "drive_db": 40},
            {"effect": "Phaser", "rate_hz": 0.4, "mix": 0.3},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Delay", "delay_seconds": 0.44, "feedback": 0.4, "mix": 0.35},
            {"effect": "Reverb", "room_size": 0.85, "wet_level": 0.3}
        ],
        "visual_rig": {
            "pre": [
                {"type": "muff", "params": {"sustain": 80, "tone": 55, "volume": 70}},
                {"type": "phaser", "params": {"speed": 30}}
            ],
            "post": [
                {"type": "delay", "params": {"time": 44, "repeats": 40, "mix": 45}},
                {"type": "reverb", "params": {"dwell": 85, "tone": 50, "mixer": 40}}
            ]
        }
    },
    "BB_KING": {
        "description": "The 'Lucille' sound. Smooth, rounded clean-to-edge-of-breakup with light compression.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -12, "ratio": 2.0},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "PeakFilter", "cutoff_hz": 400, "gain_db": 3, "q": 0.5},
            {"effect": "LowpassFilter", "cutoff_hz": 5000},
            {"effect": "Reverb", "room_size": 0.25, "wet_level": 0.1}
        ],
        "visual_rig": {
            "pre": [
                {"type": "comp", "params": {"sustain": 30, "attack": 60, "level": 50}}
            ],
            "post": [
                {"type": "reverb", "params": {"dwell": 25, "tone": 40, "mixer": 20}}
            ]
        }
    },
    "JOHN_MAYER": {
        "description": "Pristine 'Big Dipper' cleans. Ultra-transparent and dynamic.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -24, "ratio": 2.5, "attack_ms": 10.0},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "PeakFilter", "cutoff_hz": 500, "gain_db": -3, "q": 0.5},
            {"effect": "Chorus", "rate_hz": 0.8, "depth": 0.1, "mix": 0.15},
            {"effect": "Reverb", "room_size": 0.5, "wet_level": 0.15}
        ],
        "visual_rig": {
            "pre": [
                {"type": "comp", "params": {"sustain": 40, "attack": 20, "level": 60}},
                {"type": "klon", "params": {"gain": 20, "treble": 60, "output": 70}}
            ],
            "post": [
                {"type": "chorus", "params": {"rate": 20, "depth": 30}},
                {"type": "reverb", "params": {"dwell": 50, "tone": 60, "mixer": 25}}
            ]
        }
    },
    "EDDIE_VAN_HALEN": {
        "description": "The 'Brown Sound'. Saturated harmonic richness with a vintage plate reverb.",
        "chain": [
            {"effect": "Distortion", "drive_db": 22},
            {"effect": "Phaser", "rate_hz": 0.2, "mix": 0.25},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "PeakFilter", "cutoff_hz": 3000, "gain_db": 4, "q": 1.0},
            {"effect": "Reverb", "room_size": 0.6, "wet_level": 0.25}
        ],
        "visual_rig": {
            "pre": [
                {"type": "phaser", "params": {"speed": 20}},
                {"type": "od", "params": {"drive": 85, "tone": 65, "level": 60}}
            ],
            "post": [
                {"type": "reverb", "params": {"dwell": 60, "tone": 75, "mixer": 35}}
            ]
        }
    },
    "SLASH": {
        "description": "Appetite for Destruction. High-fidelity 'mid-honk' (2.8kHz) with saturated power-amp sag.",
        "chain": [
            {"effect": "Distortion", "drive_db": 32},
            {"effect": "PeakFilter", "cutoff_hz": 700, "gain_db": 3, "q": 1.0},
            {"effect": "PeakFilter", "cutoff_hz": 2800, "gain_db": 4, "q": 1.5},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Convolution", "ir_name": "vintage_4x12.wav", "mix": 1.0}
        ],
        "visual_rig": {
            "pre": [
                {"type": "od", "params": {"drive": 90, "tone": 75, "level": 80}}
            ],
            "post": []
        }
    },
    "THE_EDGE": {
        "description": "Infinite Echo. Rhythmic dual-delay with shimmering top-end and light compression.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -20, "ratio": 4.0},
            {"effect": "PeakFilter", "cutoff_hz": 3000, "gain_db": 3, "q": 0.8},
            {"effect": "Delay", "delay_seconds": 0.375, "feedback": 0.4, "mix": 0.3},
            {"effect": "Delay", "delay_seconds": 0.5, "feedback": 0.3, "mix": 0.2},
            {"effect": "Reverb", "room_size": 0.6, "wet_level": 0.1}
        ],
        "visual_rig": {
            "pre": [
                {"type": "comp", "params": {"sustain": 60, "attack": 40, "level": 60}}
            ],
            "post": [
                {"type": "delay", "params": {"time": 37, "repeats": 40, "mix": 50}},
                {"type": "delay", "params": {"time": 50, "repeats": 30, "mix": 40}},
                {"type": "reverb", "params": {"dwell": 60, "tone": 80, "mixer": 20}}
            ]
        }
    },
    "TONY_IOMMI": {
        "description": "Architect of Doom. Thin pre-drive clank (350Hz cut) into massive power-amp saturation.",
        "chain": [
            {"effect": "HighpassFilter", "cutoff_hz": 350},
            {"effect": "PeakFilter", "cutoff_hz": 2200, "gain_db": 6, "q": 1.0},
            {"effect": "Distortion", "drive_db": 45},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "LowpassFilter", "cutoff_hz": 3500}
        ],
        "visual_rig": {
            "pre": [
                {"type": "rat", "params": {"dist": 90, "filter": 70, "volume": 60}}
            ],
            "post": []
        }
    },
    "ERIC_JOHNSON": {
        "description": "The 'Violin' Lead. Liquid sustain with high-shelf attenuation for smooth top-end.",
        "chain": [
            {"effect": "Distortion", "drive_db": 35},
            {"effect": "HighShelfFilter", "cutoff_hz": 3000, "gain_db": -6},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Delay", "delay_seconds": 0.5, "feedback": 0.4, "mix": 0.25},
            {"effect": "Chorus", "rate_hz": 0.6, "depth": 0.1, "mix": 0.15}
        ],
        "visual_rig": {
            "pre": [
                {"type": "fuzz", "params": {"fuzz": 70, "level": 60}}
            ],
            "post": [
                {"type": "delay", "params": {"time": 50, "repeats": 40, "mix": 40}},
                {"type": "chorus", "params": {"rate": 20, "depth": 30}}
            ]
        }
    },
    "JOE_SATRIANI": {
        "description": "Alien Surfing Tones. High-gain compression and surgical EQ for melodic leads.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -18, "ratio": 8.0},
            {"effect": "Distortion", "drive_db": 38},
            {"effect": "PeakFilter", "cutoff_hz": 1200, "gain_db": 5, "q": 1.2},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Reverb", "room_size": 0.5, "wet_level": 0.2}
        ],
        "visual_rig": {
            "pre": [
                {"type": "comp", "params": {"sustain": 80, "attack": 30, "level": 60}},
                {"type": "ts9", "params": {"drive": 60, "tone": 50, "level": 80}}
            ],
            "post": [
                {"type": "reverb", "params": {"dwell": 50, "tone": 50, "mixer": 35}}
            ]
        }
    },
    "DEREK_TRUCKS": {
        "description": "Slide Master Soul. Vocal mid-range (630Hz) with smooth pre-amp saturation.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -18, "ratio": 3.0},
            {"effect": "PeakFilter", "cutoff_hz": 630, "gain_db": 7, "q": 0.9},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Reverb", "room_size": 0.35, "wet_level": 0.1}
        ],
        "visual_rig": {
            "pre": [
                {"type": "comp", "params": {"sustain": 50, "attack": 60, "level": 60}},
                {"type": "klon", "params": {"gain": 40, "treble": 50, "output": 80}}
            ],
            "post": [
                {"type": "reverb", "params": {"dwell": 35, "tone": 45, "mixer": 20}}
            ]
        }
    },
    "ACE_FREHLEY": {
        "description": "Space Ace Roar. Classic 70s stadium rock with bridge-humbucker bite.",
        "chain": [
            {"effect": "Distortion", "drive_db": 25},
            {"effect": "PeakFilter", "cutoff_hz": 3200, "gain_db": 4, "q": 1.2},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Convolution", "ir_name": "vintage_4x12.wav", "mix": 1.0}
        ],
        "visual_rig": {
            "pre": [
                {"type": "od", "params": {"drive": 75, "tone": 60, "level": 70}}
            ],
            "post": []
        }
    },
    "KURT_COBAIN": {
        "description": "Nevermind Grunge. Abrasive high-gain distortion paired with a thick, watery chorus.",
        "chain": [
            {"effect": "Distortion", "drive_db": 45},
            {"effect": "Chorus", "rate_hz": 1.5, "depth": 0.4, "mix": 0.3},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Reverb", "room_size": 0.4, "wet_level": 0.15}
        ],
        "visual_rig": {
            "pre": [
                {"type": "rat", "params": {"dist": 85, "filter": 30, "volume": 70}}
            ],
            "post": [
                {"type": "chorus", "params": {"rate": 45, "depth": 80}},
                {"type": "reverb", "params": {"dwell": 40, "tone": 30, "mixer": 25}}
            ]
        }
    },
    "TOM_MORELLO": {
        "description": "Sonic Saboteur. Punchy high-gain saturation with whammy-style pitch potential.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -20, "ratio": 4.0},
            {"effect": "Distortion", "drive_db": 30},
            {"effect": "PitchShift", "semitones": 12}, 
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "HighpassFilter", "cutoff_hz": 120}
        ],
        "visual_rig": {
            "pre": [
                {"type": "comp", "params": {"sustain": 60, "attack": 30, "level": 70}},
                {"type": "od", "params": {"drive": 80, "tone": 80, "level": 60}},
                {"type": "octavia", "params": {"fuzz": 60, "volume": 60}}
            ],
            "post": []
        }
    }
}

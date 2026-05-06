# Schillybeer Master Tone Library: Verified Pro-Audio Signal Chains
# This acts as the "Source of Truth" for the AI Sound Librarian.

ARTIST_PRESETS = {
    "TED_NUGENT": {
        "description": "The raw, biting mid-range of the Byrdland. High-output saturation with a focused mid-peak.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -15, "ratio": 3.0, "attack_ms": 5.0},
            {"effect": "Distortion", "drive_db": 32},
            {"effect": "PeakFilter", "cutoff_hz": 2800, "gain_db": 6, "q": 1.5},
            {"effect": "NAM_Amp", "params": {}}, # Resolves to our high-fidelity Algorithmic Amp
            {"effect": "LowShelfFilter", "cutoff_hz": 150, "gain_db": -3},
            {"effect": "Gain", "gain_db": 4}
        ]
    },
    "STEVIE_RAY_VAUGHAN": {
        "description": "Texas Flood blues. Mid-hump overdrive into a glass-shattering clean amp.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -20, "ratio": 4.0},
            {"effect": "Distortion", "drive_db": 12}, # Tube Screamer style 'warm' drive
            {"effect": "PeakFilter", "cutoff_hz": 720, "gain_db": 4, "q": 0.7},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Reverb", "room_size": 0.35, "wet_level": 0.2},
            {"effect": "HighShelfFilter", "cutoff_hz": 4000, "gain_db": 3}
        ]
    },
    "DAVID_GILMOUR": {
        "description": "Epic, ethereal sustain. Fuzz-driven leads with complex modulation and delay.",
        "chain": [
            {"effect": "Distortion", "drive_db": 40}, # Big Muff style saturation
            {"effect": "Phaser", "rate_hz": 0.4, "mix": 0.3},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Delay", "delay_seconds": 0.44, "feedback": 0.4, "mix": 0.35},
            {"effect": "Reverb", "room_size": 0.85, "wet_level": 0.3}
        ]
    },
    "BB_KING": {
        "description": "The 'Lucille' sound. Smooth, rounded clean-to-edge-of-breakup with light compression.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -12, "ratio": 2.0},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "PeakFilter", "cutoff_hz": 400, "gain_db": 3, "q": 0.5}, # Thick mids
            {"effect": "LowpassFilter", "cutoff_hz": 5000}, # Tame the bite
            {"effect": "Reverb", "room_size": 0.25, "wet_level": 0.1}
        ]
    },
    "JOHN_MAYER": {
        "description": "Pristine 'Big Dipper' cleans. Ultra-transparent and dynamic.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -24, "ratio": 2.5, "attack_ms": 10.0},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "PeakFilter", "cutoff_hz": 500, "gain_db": -3, "q": 0.5}, # Mid-scoop
            {"effect": "Chorus", "rate_hz": 0.8, "depth": 0.1, "mix": 0.15},
            {"effect": "Reverb", "room_size": 0.5, "wet_level": 0.15}
        ]
    },
    "EDDIE_VAN_HALEN": {
        "description": "The 'Brown Sound'. Saturated harmonic richness with a vintage plate reverb.",
        "chain": [
            {"effect": "Distortion", "drive_db": 22},
            {"effect": "Phaser", "rate_hz": 0.2, "mix": 0.25},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "PeakFilter", "cutoff_hz": 3000, "gain_db": 4, "q": 1.0},
            {"effect": "Reverb", "room_size": 0.6, "wet_level": 0.25}
        ]
    },
    "SLASH": {
        "description": "Appetite for Distortion. Double-mid hump (700Hz/1.8kHz) for that vocal cocked-wah bite.",
        "chain": [
            {"effect": "Distortion", "drive_db": 30},
            {"effect": "PeakFilter", "cutoff_hz": 700, "gain_db": 4, "q": 1.0},
            {"effect": "PeakFilter", "cutoff_hz": 1800, "gain_db": 3, "q": 1.2},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Convolution", "ir_name": "vintage_4x12.wav", "mix": 1.0}
        ]
    },
    "THE_EDGE": {
        "description": "Infinite modulated delays. The signature rhythmic shimmer.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -20, "ratio": 4.0},
            {"effect": "Chorus", "rate_hz": 1.5, "depth": 0.2, "mix": 0.3},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Delay", "delay_seconds": 0.42, "feedback": 0.5, "mix": 0.4},
            {"effect": "Delay", "delay_seconds": 0.31, "feedback": 0.3, "mix": 0.2}
        ]
    },
    "ERIC_JOHNSON": {
        "description": "The 'Violin' Lead. Liquid sustain with high-shelf attenuation for smooth top-end.",
        "chain": [
            {"effect": "Distortion", "drive_db": 35},
            {"effect": "HighShelfFilter", "cutoff_hz": 3000, "gain_db": -6}, # Smooth top end
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Delay", "delay_seconds": 0.5, "feedback": 0.4, "mix": 0.25},
            {"effect": "Chorus", "rate_hz": 0.6, "depth": 0.1, "mix": 0.15}
        ]
    },
    "JOE_SATRIANI": {
        "description": "Alien Surfing Tones. High-gain compression and surgical EQ for melodic leads.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -18, "ratio": 8.0},
            {"effect": "Distortion", "drive_db": 38},
            {"effect": "PeakFilter", "cutoff_hz": 1200, "gain_db": 5, "q": 1.2},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Reverb", "room_size": 0.5, "wet_level": 0.2}
        ]
    },
    "DEREK_TRUCKS": {
        "description": "Slide Master Soul. Vocal mid-range (630Hz) with smooth pre-amp saturation.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -18, "ratio": 3.0},
            {"effect": "PeakFilter", "cutoff_hz": 630, "gain_db": 7, "q": 0.9},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Reverb", "room_size": 0.35, "wet_level": 0.1}
        ]
    },
    "ACE_FREHLEY": {
        "description": "Space Ace Roar. Classic 70s stadium rock with bridge-humbucker bite.",
        "chain": [
            {"effect": "Distortion", "drive_db": 25},
            {"effect": "PeakFilter", "cutoff_hz": 3200, "gain_db": 4, "q": 1.2},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "Convolution", "ir_name": "vintage_4x12.wav", "mix": 1.0}
        ]
    },
    "TONY_IOMMI": {
        "description": "Architect of Doom. Treble-boosted (RangeMaster style) input into heavy power-amp saturation.",
        "chain": [
            {"effect": "HighpassFilter", "cutoff_hz": 300}, # Pre-drive low cut
            {"effect": "PeakFilter", "cutoff_hz": 2500, "gain_db": 5, "q": 1.0}, # RangeMaster Boost
            {"effect": "Distortion", "drive_db": 42},
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "LowpassFilter", "cutoff_hz": 3800}
        ]
    },
    "TOM_MORELLO": {
        "description": "Sonic Saboteur. Punchy high-gain saturation with whammy-style pitch potential.",
        "chain": [
            {"effect": "Compressor", "threshold_db": -20, "ratio": 4.0},
            {"effect": "Distortion", "drive_db": 30},
            {"effect": "PitchShift", "semitones": 12}, 
            {"effect": "NAM_Amp", "params": {}},
            {"effect": "HighpassFilter", "cutoff_hz": 120}
        ]
    }
}

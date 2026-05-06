# 🎸 Schillybeer Quantum Rig

The **Schillybeer Quantum Rig** is an AI-native, high-fidelity guitar processing system designed to replace physical pedalboards with a deterministic, generative DSP engine powered by Gemini 3 Flash.

## 🚀 The Vision
This is not a "Guess-based" tone generator. It is a **Lead Sound Librarian** that uses a verified Master Tone Library of legendary artist fingerprints (SRV, Iommi, Slash, etc.) to construct phase-aligned, boutique signal chains in real-time.

---

## 🛠 Hardware Requirements
To replicate this rig, you need:
1.  **ASIO-Compatible Audio Interface**: Optimized for the **DigiTech USB 1-2** hardware, but compatible with any high-speed Windows ASIO/WASAPI interface.
2.  **Ultra-Low Latency Setup**: The system is tuned for a **128-sample blocksize** at 44.1kHz.
3.  **Windows OS**: Required for current WASAPI/ASIO driver integration.

---

## 💻 Software Setup

### 1. Backend (Python 3.10+)
The brain of the rig.
```bash
cd backend
pip install -r requirements.txt
# Copy .env.example to .env and add your GEMINI_API_KEY
python main.py
```

### 2. Frontend (Vite + React)
The tactical dashboard.
```bash
cd frontend
npm install
npm run dev
```

---

## 💎 Core Technologies
*   **Gemini 3 Flash**: Generative DSP chain architecture.
*   **Python Pedalboard**: High-performance C++ audio processing wrapper.
*   **Neural Dynamic Expression (NDE)**: Real-time dynamic saturation.
*   **Adaptive Transient Detection**: Level-aware effect triggering.

---

## 🛡 Security Note
This repository uses a **Hardened Privacy Layer**. All API keys and local hardware paths must be configured in a `.env` file. See `.env.example` for details.

**Handcrafted for the next generation of generative guitarists.** 🎸⚡️🦾

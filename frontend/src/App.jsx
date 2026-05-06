import { useState, useEffect } from 'react'
import './index.css'

function App() {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  
  // New States for Library and Telemetry
  const [backendStatus, setBackendStatus] = useState('Checking...')
  const [activePreset, setActivePreset] = useState('None')
  const [artistLibrary, setArtistLibrary] = useState([])
  const [telemetry, setTelemetry] = useState({ pitch: 440, rms: 0, active_fx: 0, cpu_load: 0 })
  const [showTuner, setShowTuner] = useState(true)
  const [ndeEnabled, setNdeEnabled] = useState(true) // NDE is on by default in engine
  const [paghEnabled, setPaghEnabled] = useState(false)

  // Initial Boot Sequence
  useEffect(() => {
    const bootRig = async () => {
      try {
        const [statusRes, libraryRes] = await Promise.all([
          fetch('http://127.0.0.1:8000/'),
          fetch('http://127.0.0.1:8000/api/tones/library')
        ])
        
        if (statusRes.ok) setBackendStatus('Connected')
        if (libraryRes.ok) {
          const libData = await libraryRes.json()
          setArtistLibrary(libData.artists)
        }
      } catch (error) {
        setBackendStatus('Disconnected')
      }
    }
    bootRig()

    // High-speed telemetry loop
    const telInterval = setInterval(async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/telemetry')
        if (res.ok) {
          const data = await res.json()
          setTelemetry(data)
        }
      } catch (e) {}
    }, 100)

    return () => clearInterval(telInterval)
  }, [])

  const handleToggle = async (feature) => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/engine/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feature })
      })
      const data = await res.json()
      if (data.status === 'success') {
        if (feature === 'nde') setNdeEnabled(data.state)
        if (feature === 'pagh') setPaghEnabled(data.state)
      }
    } catch (e) {
      console.error("Toggle failed:", e)
    }
  }

  const handleArtistLoad = async (artistId) => {
    setLoading(true)
    try {
      const res = await fetch('http://127.0.0.1:8000/api/tone/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: `Load verified profile for ${artistId}` })
      })
      const data = await res.json()
      setResult(data)
      if (data.suggested_preset) setActivePreset(data.suggested_preset)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateTone = async (e) => {
    e.preventDefault()
    if (!prompt.trim()) return
    setLoading(true)
    setResult(null)

    try {
      const response = await fetch('http://127.0.0.1:8000/api/tone/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      })
      const data = await response.json()
      setResult(data)
      if (data.suggested_preset) setActivePreset(data.suggested_preset)
    } catch (error) {
      setResult({ status: "error", message: "Brain Communication Failure." })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="dashboard">
      <header>
        <div className="status-badge" style={{ background: backendStatus === 'Connected' ? '#00ff8822' : '#ff4b4b22' }}>
          <div className="status-dot" style={{ background: backendStatus === 'Connected' ? '#00ff88' : '#ff4b4b' }} />
          {backendStatus}
        </div>
        <h1>Schillybeer</h1>
        <p className="subtitle">Quantum Rig Control • Phase-Aligned DSP</p>
      </header>

      {/* NEW: Utility Strip */}
      <div className="utility-strip">
        <button 
          className={`util-btn ${showTuner ? 'active' : ''}`} 
          onClick={() => setShowTuner(!showTuner)}
        >
          {showTuner ? 'HIDE TUNER' : 'SHOW TUNER'}
        </button>
        <button 
          className={`util-btn ${ndeEnabled ? 'active' : ''}`} 
          onClick={() => handleToggle('nde')}
        >
          NDE MODE
        </button>
        <button 
          className={`util-btn ${paghEnabled ? 'active' : ''}`} 
          onClick={() => handleToggle('pagh')}
        >
          PAGH GEN
        </button>
        <button className="util-btn mute" onClick={() => alert('Mute Engaged')}>
          MASTER MUTE
        </button>
      </div>

      <main>
        <div className="grid-layout">
          {/* Left Column: Core Controls */}
          <div className="left-column">
            <section className="panel artist-vault">
              <div className="panel-header">
                <h2>Master Tone Library</h2>
                <span className="badge">{artistLibrary.length} PROFILES</span>
              </div>
              <div className="artist-grid">
                {artistLibrary.map(artist => (
                  <button 
                    key={artist.id} 
                    className={`artist-card minimalist ${activePreset === artist.id ? 'active' : ''}`}
                    onClick={() => handleArtistLoad(artist.id)}
                    title={artist.description} // Hover description
                    disabled={loading}
                  >
                    <div className="artist-name">{artist.name}</div>
                  </button>
                ))}
              </div>
            </section>

            <section className="panel tone-brain">
              <h2>Generative AI Brain</h2>
              <form onSubmit={handleGenerateTone} className="input-group">
                <input 
                  type="text" 
                  placeholder="e.g., 'SRV Blues but on a space ship with lasers'" 
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  disabled={loading}
                />
                <button type="submit" className="pulse-btn" disabled={loading}>
                  {loading ? 'CALCULATING...' : 'EVOLVE TONE'}
                </button>
              </form>
              {result && (
                <div className="technical-log">
                  <div className="log-header">SIGNAL CHAIN CONFIRMED</div>
                  {result.message}
                </div>
              )}
            </section>
          </div>

          {/* Right Column: Telemetry & Tuner */}
          <div className="right-column">
            <section className="panel telemetry-panel">
              <h2>Quantum Telemetry</h2>
              <div className="telemetry-grid">
                <div className="metric">
                  <label>Signal RMS</label>
                  <div className="progress-bg">
                    <div className="progress-bar" style={{ width: `${Math.min(telemetry.rms * 500, 100)}%` }} />
                  </div>
                </div>
                <div className="metric">
                  <label>Pitch Depth</label>
                  <div className="value">{telemetry.pitch.toFixed(1)} Hz</div>
                </div>
              </div>
            </section>

            {showTuner && (
              <section className="panel tuner-panel">
                <h2>Smart Tuner</h2>
                <Tuner />
              </section>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

function Tuner() {
  const [tunerData, setTunerData] = useState({ note: '--', cents: 0, freq: 0, is_tuned: false });

  useEffect(() => {
    const fetchTuner = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/tuner');
        const data = await response.json();
        setTunerData(data);
      } catch (err) {
        console.error("Tuner error:", err);
      }
    };

    const interval = setInterval(fetchTuner, 30); // 33Hz polling for ultra-smooth reading
    return () => clearInterval(interval);
  }, []);

  const needleRotation = (tunerData.cents / 50) * 45; // Max 45 degree tilt

  return (
    <div className="tuner-container">
      <div className={`tuner-note ${tunerData.is_tuned ? 'in-tune' : ''}`}>
        {tunerData.note}
      </div>
      
      <div className="tuner-display">
        <div className="tuner-scale">
          {[...Array(9)].map((_, i) => (
            <div key={i} className={`scale-tick ${i === 4 ? 'center' : ''}`} />
          ))}
        </div>
        <div 
          className={`tuner-needle ${tunerData.is_tuned ? 'in-tune' : ''}`}
          style={{ transform: `translateX(-50%) rotate(${needleRotation}deg)` }}
        />
      </div>
      
      <div className="tuner-info">
        {tunerData.freq > 0 ? `${tunerData.freq} Hz` : 'Waiting for signal...'}
      </div>
    </div>
  );
}

export default App;

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
  const [ndeEnabled, setNdeEnabled] = useState(true)
  const [paghEnabled, setPaghEnabled] = useState(false)
  const [pedalChain, setPedalChain] = useState({ pre: [], post: [] })
  const [isMuted, setIsMuted] = useState(false)

  const AVAILABLE_PEDALS = [
    { type: 'comp', name: 'Blue Comp', color: '#0078D7', controls: [{id:'sustain', label:'SUSTAIN'}, {id:'attack', label:'ATTACK'}, {id:'level', label:'LEVEL'}] },
    { type: 'od', name: 'Vintage OD', color: '#FF8C00', controls: [{id:'drive', label:'DRV'}, {id:'tone', label:'TONE'}, {id:'level', label:'LVL'}] },
    { type: 'fuzz', name: 'Fuzz Face', color: '#FF003C', controls: [{id:'fuzz', label:'FUZZ'}, {id:'level', label:'LVL'}] },
    { type: 'ts9', name: 'Green Scream', color: '#32CD32', controls: [{id:'drive', label:'DRV'}, {id:'tone', label:'TONE'}, {id:'level', label:'LVL'}] },
    { type: 'klon', name: 'The Centaur', color: '#DAA520', controls: [{id:'gain', label:'GAIN'}, {id:'treble', label:'TREB'}, {id:'output', label:'OUT'}] },
    { type: 'rat', name: 'Rat Tail', color: '#111111', controls: [{id:'dist', label:'DIST'}, {id:'filter', label:'FLTR'}, {id:'volume', label:'VOL'}] },
    { type: 'muff', name: 'Pi Fuzz', color: '#C0C0C0', controls: [{id:'sustain', label:'SUST'}, {id:'tone', label:'TONE'}, {id:'volume', label:'VOL'}] },
    { type: 'octavia', name: 'Octavia', color: '#8A2BE2', controls: [{id:'fuzz', label:'FUZZ'}, {id:'volume', label:'VOL'}] },
    { type: 'chorus', name: 'Analog Chorus', color: '#00CED1', controls: [{id:'rate', label:'RATE'}, {id:'depth', label:'DEPTH'}] },
    { type: 'delay', name: 'Tape Echo', color: '#9370DB', controls: [{id:'time', label:'TIME'}, {id:'repeats', label:'FDBK'}, {id:'mix', label:'MIX'}] },
    { type: 'phaser', name: 'Phase 90', color: '#FF4500', controls: [{id:'speed', label:'SPEED'}] },
    { type: 'flanger', name: 'Flanger', color: '#A9A9A9', controls: [{id:'manual', label:'MAN'}, {id:'depth', label:'DEPTH'}, {id:'rate', label:'RATE'}, {id:'res', label:'RES'}] },
    { type: 'vibe', name: 'Uni-Vibe', color: '#8B008B', controls: [{id:'speed', label:'SPEED'}, {id:'intensity', label:'INT'}, {id:'volume', label:'VOL'}] },
    { type: 'reverb', name: 'Spring Tank', color: '#F4A460', controls: [{id:'dwell', label:'DWELL'}, {id:'tone', label:'TONE'}, {id:'mixer', label:'MIX'}] },
    { type: 'gate', name: 'Noise Silencer', color: '#F8F8FF', controls: [{id:'threshold', label:'THRESH'}, {id:'decay', label:'DECAY'}] },
    { type: 'leslie', name: 'Leslie Spinner', color: '#9932CC', controls: [{id:'speed', label:'SPEED'}, {id:'width', label:'WIDTH'}, {id:'mix', label:'MIX'}] }
  ]

  // Initial Boot Sequence
  useEffect(() => {
    const bootRig = async () => {
      try {
        const [statusRes, libraryRes, pedalsRes] = await Promise.all([
          fetch('http://127.0.0.1:8000/'),
          fetch('http://127.0.0.1:8000/api/tones/library'),
          fetch('http://127.0.0.1:8000/api/pedals/state')
        ])
        
        if (statusRes.ok) setBackendStatus('Connected')
        if (libraryRes.ok) {
          const libData = await libraryRes.json()
          setArtistLibrary(libData.artists)
        }
        if (pedalsRes.ok) {
          const pedalData = await pedalsRes.json()
          setPedalChain(pedalData)
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

  const handlePedalUpdate = async (newChain) => {
    setPedalChain(newChain)
    try {
      await fetch('http://127.0.0.1:8000/api/pedals/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newChain)
      })
    } catch (e) {
      console.error("Pedal update failed:", e)
    }
  }

  const addPedal = (type, stage) => {
    const pedalDef = AVAILABLE_PEDALS.find(p => p.type === type)
    if (!pedalDef) return

    // Initialize all params to 50
    const initialParams = {}
    pedalDef.controls.forEach(c => initialParams[c.id] = 50)

    const newPedal = { 
      id: Math.random().toString(36).substr(2, 9), 
      type, 
      enabled: true, 
      params: initialParams 
    }
    const newChain = { ...pedalChain, [stage]: [...pedalChain[stage], newPedal] }
    handlePedalUpdate(newChain)
  }

  const removePedal = (id, stage) => {
    const newChain = { ...pedalChain, [stage]: pedalChain[stage].filter(p => p.id !== id) }
    handlePedalUpdate(newChain)
  }

  const handleClearAll = async () => {
    const emptyChain = { pre: [], post: [] }
    setPedalChain(emptyChain)
    setPrompt('')
    setResult(null)
    setActivePreset('None')
    try {
      await fetch('http://127.0.0.1:8000/api/engine/reset', { method: 'POST' })
    } catch (e) {
      console.error("Initialize board failed:", e)
    }
  }

  const handleMuteAll = async () => {
    const newState = !isMuted;
    setIsMuted(newState);
    try {
      await fetch('http://127.0.0.1:8000/api/engine/mute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mute: newState })
      })
    } catch (e) {
      console.error("Mute failed:", e)
    }
  }

  const updatePedalParam = (id, stage, updates) => {
    const newChain = {
      ...pedalChain,
      [stage]: pedalChain[stage].map(p => {
        if (p.id === id) {
          // If updates contains nested params, merge them
          if (updates.params) {
            return { ...p, params: { ...p.params, ...updates.params } }
          }
          // Otherwise it's top level (like enabled)
          return { ...p, ...updates }
        }
        return p
      })
    }
    handlePedalUpdate(newChain)
  }

  const movePedal = (index, stage, direction) => {
    const newStage = [...pedalChain[stage]]
    if (direction === -1 && index > 0) {
      [newStage[index - 1], newStage[index]] = [newStage[index], newStage[index - 1]]
    } else if (direction === 1 && index < newStage.length - 1) {
      [newStage[index + 1], newStage[index]] = [newStage[index], newStage[index + 1]]
    }
    handlePedalUpdate({ ...pedalChain, [stage]: newStage })
  }

  const renderStompbox = (pedal, index, stage) => {
    const pedalDef = AVAILABLE_PEDALS.find(p => p.type === pedal.type) || AVAILABLE_PEDALS[0]
    return (
      <div className={`stompbox ${pedal.enabled ? 'active' : ''}`} style={{ '--pedal-color': pedalDef.color }} key={pedal.id}>
        <div className="stomp-controls-top">
          <button className="move-btn" onClick={() => movePedal(index, stage, -1)}>◀</button>
          <button className="delete-btn" onClick={() => removePedal(pedal.id, stage)}>✕</button>
          <button className="move-btn" onClick={() => movePedal(index, stage, 1)}>▶</button>
        </div>
        <div className="stomp-led" />
        <div className="stompbox-title">{pedalDef.name}</div>
        
        <div className="faders-container">
          {pedalDef.controls.map(ctrl => (
            <div className="stomp-dial" key={ctrl.id}>
              <div className="fader-wrapper">
                <input 
                  type="range" 
                  min="0" max="100" 
                  value={pedal.params[ctrl.id]} 
                  onChange={(e) => updatePedalParam(pedal.id, stage, { params: { [ctrl.id]: parseInt(e.target.value) } })}
                />
              </div>
              <label>{ctrl.label}</label>
            </div>
          ))}
        </div>

        <div 
          className="stomp-switch" 
          onClick={() => updatePedalParam(pedal.id, stage, { enabled: !pedal.enabled })}
        />
      </div>
    )
  }

  const handleArtistLoad = async (artistId) => {
    setLoading(true)
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/tones/artist/${artistId}`)
      const data = await res.json()
      
      if (data.status === 'success') {
        const visualRig = data.visual_rig || { pre: [], post: [] }
        
        // Prepare pedals for frontend rendering with unique IDs
        const prepareChain = (chain) => chain.map(p => ({
          ...p,
          id: Math.random().toString(36).substr(2, 9),
          enabled: true
        }))
        
        const newChain = {
          pre: prepareChain(visualRig.pre),
          post: prepareChain(visualRig.post)
        }
        
        // Instantly update the UI board
        setPedalChain(newChain)
        setActivePreset(artistId.replace(/_/g, " "))
        
        // Push the manual pedals to the backend
        await fetch('http://127.0.0.1:8000/api/pedals/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newChain)
        })
      }
    } catch (e) {
      console.error("Failed to load artist visual rig:", e)
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
          title="Toggles the visibility of the visual guitar tuner interface."
        >
          {showTuner ? 'HIDE TUNER' : 'SHOW TUNER'}
        </button>
        <button 
          className={`util-btn ${ndeEnabled ? 'active' : ''}`} 
          onClick={() => handleToggle('nde')}
          title="Neural Drive Engine: Toggles the advanced neural network amp simulation."
        >
          NDE MODE
        </button>
        <button 
          className={`util-btn ${paghEnabled ? 'active' : ''}`} 
          onClick={() => handleToggle('pagh')}
          title="Phase-Aligned Generative Harmonics: Toggles AI harmonic generation."
        >
          PAGH GEN
        </button>
      </div>

      <div className="master-controls-strip">
        <button 
          className="master-action-btn reset" 
          onClick={handleClearAll}
          title="Completely clears the pedalboard and returns the system to a clean, fresh state."
        >
          RESET ALL
        </button>
        <button 
          className={`master-action-btn mute ${isMuted ? 'active' : ''}`} 
          onClick={handleMuteAll}
          title="Instantly cuts all audio output (Master Panic Mute) without losing your pedal settings."
        >
          {isMuted ? 'UNMUTE ALL' : 'MUTE ALL'}
        </button>
      </div>

      <main>
        {/* NEW: Daisy Chain Board */}
        <section className="stompbox-board">
          <div className="pedal-adder">
            <select id="pedal-select" defaultValue="">
              <option value="" disabled>+ ADD PEDAL...</option>
              {AVAILABLE_PEDALS.map(p => <option key={p.type} value={p.type}>{p.name}</option>)}
            </select>
            <button 
              onClick={() => addPedal(document.getElementById('pedal-select').value, 'pre')}
              title="Inserts the selected pedal before the main amplifier block."
            >
              ADD TO PRE-AMP
            </button>
            <button 
              onClick={() => addPedal(document.getElementById('pedal-select').value, 'post')}
              title="Inserts the selected pedal into the amplifier's FX loop (post-amp)."
            >
              ADD TO FX LOOP
            </button>
          </div>

          <div className="daisy-chain-container">
            {/* Pre-Amp Chain */}
            <div className="pedal-stage">
              <div className="stage-label">PRE-AMP</div>
              <div className="pedal-row">
                {pedalChain.pre.map((p, i) => renderStompbox(p, i, 'pre'))}
              </div>
            </div>

            {/* Artificial Amp Block */}
            <div className="amp-block">
              <div className="amp-grill">
                <h3>{activePreset !== 'None' ? activePreset : 'AI AMPLIFIER'}</h3>
                <div className="amp-status">GENERATIVE DSP ACTIVE</div>
              </div>
            </div>

            {/* Post-Amp Chain */}
            <div className="pedal-stage">
              <div className="stage-label">FX LOOP</div>
              <div className="pedal-row">
                {pedalChain.post.map((p, i) => renderStompbox(p, i, 'post'))}
              </div>
            </div>
          </div>
        </section>

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

import { useState, useEffect } from 'react'
import './index.css'

function App() {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  
  // Dynamic status states
  const [backendStatus, setBackendStatus] = useState('Checking...')
  const [activePreset, setActivePreset] = useState('None')

  // Check if backend is alive on load
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/')
        if (response.ok) {
          setBackendStatus('Connected')
        } else {
          setBackendStatus('Disconnected')
        }
      } catch (error) {
        setBackendStatus('Disconnected')
      }
    }
    checkBackend()
    // Poll every 5 seconds
    const interval = setInterval(checkBackend, 5000)
    return () => clearInterval(interval)
  }, [])

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
      
      // Update the active preset if Gemini successfully mapped it
      if (data.suggested_preset) {
        setActivePreset(data.suggested_preset)
      }
    } catch (error) {
      console.error("Error connecting to Brain:", error)
      setResult({ 
        status: "error", 
        message: "Failed to connect to Schillybeer Brain. Make sure your GEMINI_API_KEY is correct and the backend is running." 
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="dashboard">
      <header>
        <h1>Schillybeer</h1>
        <p className="subtitle">AI-Powered Smart Guitar Rig</p>
      </header>

      <main>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
          <div className="left-column">
            <section className="panel">
              <h2>Tone Generator</h2>
              <p>Describe the tone you want, and the AI Brain will configure your rig.</p>
              
              <form onSubmit={handleGenerateTone} className="input-group">
                <input 
                  type="text" 
                  placeholder="e.g., 'Sparkly clean John Mayer tone with a touch of reverb'" 
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  disabled={loading}
                />
                <button type="submit" disabled={loading}>
                  {loading ? 'Dialing in...' : 'Get Tone'}
                </button>
              </form>

              {result && (
                <div className="result" style={{ borderColor: result.status === 'error' || result.detail ? '#ff4b4b' : 'var(--primary-color)' }}>
                  {result.detail || result.message}
                </div>
              )}
            </section>

            <section className="panel" style={{ marginTop: '2rem' }}>
              <h2>Current Rig Status</h2>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem', color: 'var(--text-secondary)' }}>
                <span>
                  Backend: 
                  <strong style={{ color: backendStatus === 'Connected' ? '#00f2fe' : '#ff4b4b', marginLeft: '8px' }}>
                    {backendStatus}
                  </strong>
                </span>
                <span>
                  Audio Engine: 
                  <strong style={{ color: backendStatus === 'Connected' ? '#00f2fe' : '#ff4b4b', marginLeft: '8px' }}>
                    {backendStatus === 'Connected' ? 'Online' : 'Offline'}
                  </strong>
                </span>
                <span>
                  Active Preset: 
                  <strong style={{ color: activePreset !== 'None' ? '#00f2fe' : 'inherit', marginLeft: '8px' }}>
                    {activePreset.replace(/_/g, ' ')}
                  </strong>
                </span>
              </div>
            </section>
          </div>

          <div className="right-column">
            <section className="panel">
              <h2>Smart Tuner</h2>
              <Tuner />
            </section>
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

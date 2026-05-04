import { useState } from 'react'
import './index.css'

function App() {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const handleGenerateTone = async (e) => {
    e.preventDefault()
    if (!prompt.trim()) return

    setLoading(true)
    setResult(null)

    try {
      // Call our FastAPI backend (assuming it's running on port 8000)
      const response = await fetch('http://127.0.0.1:8000/api/tone/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      })
      
      const data = await response.json()
      setResult(data)
    } catch (error) {
      console.error("Error connecting to Brain:", error)
      setResult({ 
        status: "error", 
        message: "Failed to connect to Schillybeer Brain. Make sure the backend is running!" 
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
            <div className="result">
              {result.message}
              {result.suggested_preset && (
                <div style={{ marginTop: '0.5rem', fontSize: '1.1rem', color: 'var(--primary-color)' }}>
                  <strong>Loaded Preset:</strong> {result.suggested_preset}
                </div>
              )}
            </div>
          )}
        </section>

        <section className="panel" style={{ marginTop: '2rem' }}>
          <h2>Current Rig Status</h2>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem', color: 'var(--text-secondary)' }}>
            <span>Backend: <strong style={{ color: '#ff4b4b' }}>Disconnected</strong></span>
            <span>Audio Engine: <strong style={{ color: '#ff4b4b' }}>Offline</strong></span>
            <span>Active Preset: <strong>None</strong></span>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App

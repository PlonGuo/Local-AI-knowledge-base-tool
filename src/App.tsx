import { useEffect, useState } from 'react'
import AppLayout from './components/layout/AppLayout'

interface HealthStatus {
  status: string
  version: string
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [backendUrl, setBackendUrl] = useState('http://127.0.0.1:8000')

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const url = await window.api?.getBackendUrl?.() ?? 'http://127.0.0.1:8000'
        setBackendUrl(url)
        const res = await fetch(`${url}/health`)
        const data: HealthStatus = await res.json()
        setHealth(data)
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      }
    }
    fetchHealth()
  }, [])

  return <AppLayout health={health} error={error} backendUrl={backendUrl} />
}

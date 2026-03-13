import { useEffect, useState } from 'react'
import AppLayout from './components/layout/AppLayout'

interface HealthStatus {
  status: string
  version: string
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const backendUrl = await window.api?.getBackendUrl?.() ?? 'http://127.0.0.1:8000'
        const res = await fetch(`${backendUrl}/health`)
        const data: HealthStatus = await res.json()
        setHealth(data)
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      }
    }
    fetchHealth()
  }, [])

  return <AppLayout health={health} error={error} />
}

import { useEffect, useState } from 'react'

interface AppConfig {
  llm_provider: 'ollama' | 'openai-compatible' | 'anthropic'
  model_name: string
  base_url: string
  api_key: string | null
  embedding_language: 'english' | 'chinese' | 'mixed'
}

interface TestResult {
  success: boolean
  message?: string
  error?: string
}

interface SettingsPageProps {
  backendUrl: string
  onBack?: () => void
  onConfigSaved?: () => void
}

const defaultConfig: AppConfig = {
  llm_provider: 'ollama',
  model_name: 'llama3',
  base_url: 'http://localhost:11434',
  api_key: null,
  embedding_language: 'english',
}

export default function SettingsPage({ backendUrl, onBack, onConfigSaved }: SettingsPageProps) {
  const [config, setConfig] = useState<AppConfig>(defaultConfig)
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    fetch(`${backendUrl}/config`)
      .then((r) => r.json())
      .then((data: AppConfig) => setConfig(data))
      .catch(() => {})
  }, [backendUrl])

  const handleSave = async () => {
    setSaveMessage(null)
    setTestResult(null)
    try {
      await fetch(`${backendUrl}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      setSaveMessage('Settings saved')
      onConfigSaved?.()
    } catch {
      setSaveMessage('Failed to save settings')
    }
  }

  const handleTestConnection = async () => {
    setTestResult(null)
    setTesting(true)
    try {
      // Save current config first so test-llm uses latest values
      await fetch(`${backendUrl}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      const res = await fetch(`${backendUrl}/config/test-llm`, { method: 'POST' })
      const data: TestResult = await res.json()
      setTestResult(data)
    } catch {
      setTestResult({ success: false, error: 'Request failed' })
    } finally {
      setTesting(false)
    }
  }

  const inputClass =
    'w-full rounded-md border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring'
  const labelClass = 'block text-sm font-medium text-foreground mb-1'
  const selectClass =
    'w-full rounded-md border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring'

  return (
    <div data-testid="settings-page" className="flex-1 overflow-y-auto p-6">
      <div className="mx-auto max-w-lg">
        <div className="mb-6 flex items-center gap-3">
          <button
            data-testid="settings-back-button"
            onClick={onBack}
            className="rounded-md px-2 py-1 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          >
            &larr; Back
          </button>
          <h1 className="text-xl font-bold text-foreground">Settings</h1>
        </div>

        <div className="space-y-5">
          {/* LLM Provider */}
          <div>
            <label className={labelClass}>LLM Provider</label>
            <select
              data-testid="llm-provider-select"
              value={config.llm_provider}
              onChange={(e) =>
                setConfig({ ...config, llm_provider: e.target.value as AppConfig['llm_provider'] })
              }
              className={selectClass}
            >
              <option value="ollama">Ollama</option>
              <option value="openai-compatible">OpenAI Compatible</option>
              <option value="anthropic">Anthropic Claude</option>
            </select>
          </div>

          {/* Model Name */}
          <div>
            <label className={labelClass}>Model Name</label>
            <input
              data-testid="model-name-input"
              type="text"
              value={config.model_name}
              onChange={(e) => setConfig({ ...config, model_name: e.target.value })}
              className={inputClass}
            />
          </div>

          {/* Base URL */}
          <div>
            <label className={labelClass}>Base URL</label>
            <input
              data-testid="base-url-input"
              type="text"
              value={config.base_url}
              onChange={(e) => setConfig({ ...config, base_url: e.target.value })}
              className={inputClass}
            />
          </div>

          {/* API Key (conditional) */}
          {(config.llm_provider === 'openai-compatible' || config.llm_provider === 'anthropic') && (
            <div>
              <label className={labelClass}>API Key</label>
              <input
                data-testid="api-key-input"
                type="password"
                value={config.api_key ?? ''}
                onChange={(e) =>
                  setConfig({ ...config, api_key: e.target.value || null })
                }
                className={inputClass}
                placeholder="sk-..."
              />
            </div>
          )}

          {/* Embedding Language */}
          <div>
            <label className={labelClass}>Embedding Language</label>
            <select
              data-testid="embedding-language-select"
              value={config.embedding_language}
              onChange={(e) =>
                setConfig({
                  ...config,
                  embedding_language: e.target.value as AppConfig['embedding_language'],
                })
              }
              className={selectClass}
            >
              <option value="english">English</option>
              <option value="chinese">Chinese</option>
              <option value="mixed">Mixed</option>
            </select>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              data-testid="save-button"
              onClick={handleSave}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Save
            </button>
            <button
              data-testid="test-connection-button"
              onClick={handleTestConnection}
              disabled={testing}
              className="rounded-md border px-4 py-2 text-sm font-medium text-foreground hover:bg-accent disabled:opacity-50"
            >
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
          </div>

          {/* Feedback */}
          {saveMessage && (
            <p className="text-sm text-green-600">{saveMessage}</p>
          )}
          {testResult && (
            <p
              className={`text-sm ${testResult.success ? 'text-green-600' : 'text-red-600'}`}
            >
              {testResult.success ? testResult.message : testResult.error}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

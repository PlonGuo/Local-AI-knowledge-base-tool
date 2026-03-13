import { useEffect, useState } from 'react'

interface SetupStatus {
  python_ok: boolean
  uv_ok: boolean
  ollama_ok: boolean
  first_run: boolean
}

interface OnboardingPageProps {
  backendUrl: string
  onComplete: () => void
}

function StatusIcon({ ok }: { ok: boolean | null }) {
  if (ok === null) return <span className="text-gray-400">…</span>
  return ok
    ? <span className="text-green-500 font-bold">✓</span>
    : <span className="text-red-500 font-bold">✗</span>
}

export default function OnboardingPage({ backendUrl, onComplete }: OnboardingPageProps) {
  const [step, setStep] = useState(1)
  const [status, setStatus] = useState<SetupStatus | null>(null)

  useEffect(() => {
    fetch(`${backendUrl}/setup/status`)
      .then((r) => r.json())
      .then((data: SetupStatus) => setStatus(data))
      .catch(() => {})
  }, [backendUrl])

  const nextEnabled = status?.uv_ok === true

  if (step === 1) {
    return (
      <div data-testid="onboarding-page" className="flex flex-1 flex-col items-center justify-center gap-8 p-12">
        <h1 className="text-2xl font-bold">Welcome to KnowHive</h1>
        <p className="text-gray-500">Let's check your dependencies before getting started.</p>

        <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white p-6 shadow-sm space-y-4">
          <div data-testid="dep-python" className="flex items-center justify-between">
            <span className="font-medium">Python 3.11+</span>
            <StatusIcon ok={status ? status.python_ok : null} />
          </div>

          <div data-testid="dep-uv" className="flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <span className="font-medium">uv (package manager)</span>
              <StatusIcon ok={status ? status.uv_ok : null} />
            </div>
            {status && !status.uv_ok && (
              <p className="text-sm text-red-600">
                uv is required.{' '}
                <a
                  href="https://docs.astral.sh/uv/getting-started/installation/"
                  target="_blank"
                  rel="noreferrer"
                  className="underline"
                >
                  Install uv
                </a>
              </p>
            )}
          </div>

          <div data-testid="dep-ollama" className="flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <span className="font-medium">Ollama (optional)</span>
              <StatusIcon ok={status ? status.ollama_ok : null} />
            </div>
            {status && !status.ollama_ok && (
              <p className="text-sm text-yellow-600">
                Ollama not detected — you can configure another LLM provider in settings.
              </p>
            )}
          </div>
        </div>

        <button
          data-testid="onboarding-next-btn"
          disabled={!nextEnabled}
          onClick={() => setStep(2)}
          className="rounded-md bg-blue-600 px-6 py-2 text-white font-medium disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    )
  }

  // Steps 2+ rendered by later tasks; fall through to onComplete for now
  onComplete()
  return null
}

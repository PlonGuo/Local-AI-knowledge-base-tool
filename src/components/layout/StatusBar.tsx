interface StatusBarProps {
  health: { status: string; version: string } | null
  error: string | null
}

export default function StatusBar({ health, error }: StatusBarProps) {
  let statusText: string
  let statusColor: string

  if (error) {
    statusText = 'Disconnected'
    statusColor = 'text-red-500'
  } else if (health) {
    statusText = `Backend: ${health.status} v${health.version}`
    statusColor = 'text-green-600'
  } else {
    statusText = 'Connecting...'
    statusColor = 'text-muted-foreground'
  }

  return (
    <footer
      data-testid="status-bar"
      className="flex h-7 items-center border-t bg-secondary/50 px-4"
    >
      <span className={`text-xs ${statusColor}`}>{statusText}</span>
    </footer>
  )
}

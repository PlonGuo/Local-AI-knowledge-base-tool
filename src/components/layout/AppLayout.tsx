import Sidebar from './Sidebar'
import ChatArea from './ChatArea'
import StatusBar from './StatusBar'

interface AppLayoutProps {
  health: { status: string; version: string } | null
  error: string | null
}

export default function AppLayout({ health, error }: AppLayoutProps) {
  return (
    <div data-testid="app-layout" className="flex h-screen flex-col">
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <ChatArea />
      </div>
      <StatusBar health={health} error={error} />
    </div>
  )
}

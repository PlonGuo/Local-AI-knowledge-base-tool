interface SidebarProps {
  onSettingsClick?: () => void
}

export default function Sidebar({ onSettingsClick }: SidebarProps) {
  return (
    <aside
      data-testid="sidebar"
      className="flex w-64 flex-col border-r bg-secondary/50"
    >
      <div className="flex h-12 items-center gap-2 border-b px-4">
        <span className="text-lg font-bold text-foreground">KnowHive</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Knowledge
        </div>
        <p className="text-sm text-muted-foreground">No files imported yet</p>
      </div>

      <div className="border-t p-2">
        <button
          data-testid="settings-button"
          onClick={onSettingsClick}
          className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        >
          Settings
        </button>
      </div>
    </aside>
  )
}

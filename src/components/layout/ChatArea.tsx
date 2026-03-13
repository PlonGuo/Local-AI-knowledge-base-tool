export default function ChatArea() {
  return (
    <main
      data-testid="chat-area"
      className="flex flex-1 flex-col bg-background"
    >
      <div className="flex flex-1 items-center justify-center">
        <div className="text-center space-y-2">
          <p className="text-lg text-muted-foreground">Start a conversation</p>
          <p className="text-sm text-muted-foreground">
            Ask questions about your knowledge base
          </p>
        </div>
      </div>
    </main>
  )
}

export function App() {
  return (
    <div className="flex h-screen flex-col bg-editor-bg text-editor-text">
      <header className="flex h-12 items-center justify-between border-b border-editor-surface px-4">
        <h1 className="text-lg font-bold tracking-tight">
          Audio AI Editor
        </h1>
        <span className="text-xs text-editor-muted">v0.1.0</span>
      </header>

      <main className="flex flex-1 overflow-hidden">
        <div className="flex flex-1 items-center justify-center">
          <p className="text-editor-muted">
            Drop an audio file here or click to upload
          </p>
        </div>
      </main>

      <footer className="flex h-8 items-center border-t border-editor-surface px-4">
        <span className="text-xs text-editor-muted">Ready</span>
      </footer>
    </div>
  );
}

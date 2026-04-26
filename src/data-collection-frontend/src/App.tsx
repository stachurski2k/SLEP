import Editor from './components/Editor'
import './App.css'

function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true" />
          <div>
            <p className="eyebrow">Editing workspace</p>
            <h1>SLEP video</h1>
          </div>
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar" aria-label="Primary">
          <nav className="nav-panel">
            <button className="nav-item nav-item-active" type="button">
              Video editor
            </button>
          </nav>
        </aside>

        <main className="editor-view">
          <Editor />
        </main>
      </div>
    </div>
  )
}

export default App

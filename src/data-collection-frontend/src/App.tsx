import Editor from './components/Editor'
import Navbar from './ui/Navbar'
import Topbar from './ui/Topbar'
import './App.css'

function App() {
  return (
    <div className="app-shell">
      <Topbar />
      <div className="workspace">
        <Navbar />
        <main className="editor-view">
          <Editor />
        </main>
      </div>
    </div>
  )
}

export default App

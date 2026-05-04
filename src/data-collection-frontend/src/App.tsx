import { useState } from 'react'
import DatasetManager from './components/DatasetManager'
import Editor from './components/Editor'
import Navbar from './ui/Navbar'
import Topbar from './ui/Topbar'
import './App.css'

export type Page = 'editor' | 'dataset-manager'

function App() {
  const [activePage, setActivePage] = useState<Page>('editor')

  return (
    <div className="app-shell">
      <Topbar />
      <div className="workspace">
        <Navbar activePage={activePage} onPageChange={setActivePage} />
        <main className="editor-view">
          {activePage === 'editor' ? <Editor /> : <DatasetManager />}
        </main>
      </div>
    </div>
  )
}

export default App

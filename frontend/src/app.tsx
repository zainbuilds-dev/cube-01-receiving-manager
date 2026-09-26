import { useState } from 'react'
import { EvidenceRecord } from './types'
import NewRecordForm from './components/NewRecordForm'
import RecordList from './components/RecordList'
import ResultsView from './components/ResultsView'

type View = { name: 'home' } | { name: 'new' } | { name: 'result'; record: EvidenceRecord }

export default function App() {
  const [view, setView] = useState<View>({ name: 'home' })
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand" onClick={() => setView({ name: 'home' })}>
          📦 Receiving Manager
        </div>
        <nav>
          <button onClick={() => setView({ name: 'home' })}>Records</button>
          <button className="primary" onClick={() => setView({ name: 'new' })}>+ New Receiving Record</button>
        </nav>
      </header>
      <main>
        {view.name === 'home' && <RecordList onOpen={r => setView({ name: 'result', record: r })} />}
        {view.name === 'new' && (
          <NewRecordForm
            onDone={r => setView({ name: 'result', record: r })}
            onCancel={() => setView({ name: 'home' })}
          />
        )}
        {view.name === 'result' && <ResultsView record={view.record} />}
      </main>
    </div>
  )
}
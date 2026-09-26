import { useState } from 'react'
import { EvidenceRecord } from './types'
import { ORGS, currentOrgId, setOrg } from './api'
import NewRecordForm from './components/NewRecordForm'
import RecordList from './components/RecordList'
import ResultsView from './components/ResultsView'

type View = { name: 'home' } | { name: 'new' } | { name: 'result'; record: EvidenceRecord }

export default function App() {
  const [view, setView] = useState<View>({ name: 'home' })
  const orgId = currentOrgId()
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand" onClick={() => setView({ name: 'home' })}>
          📦 Receiving Manager
        </div>
        <nav>
          <div className="orgswitch" title="Organisation (tenant)">
            {ORGS.map(o => (
              <button key={o.id} className={orgId === o.id ? 'active' : ''}
                      onClick={() => setOrg(o.token)}>{o.label}</button>
            ))}
          </div>
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
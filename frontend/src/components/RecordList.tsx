import { useEffect, useState } from 'react'
import { getRecord, inspect, listRecords } from '../api'
import { EvidenceRecord, RecordSummary } from '../types'

export default function RecordList({ onOpen }: { onOpen: (r: EvidenceRecord) => void }) {
  const [rows, setRows] = useState<RecordSummary[] | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    listRecords().then(setRows).catch(e => setErr(String(e?.message ?? e)))
  }, [])

  async function open(rid: string) {
    setErr(null); setBusy(rid)
    try {
      const rec = await getRecord(rid)
      if ('checks' in rec) onOpen(rec as EvidenceRecord)
      else onOpen(await inspect(rid)) // created but never inspected -> inspect now
    } catch (e: any) {
      setErr(String(e?.message ?? e))
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="card">
      <h3>Receiving Records</h3>
      {err && <div className="error">{err}</div>}
      {rows === null && !err && <p className="muted">Loading…</p>}
      {rows && rows.length === 0 && (
        <p className="muted">No records yet — create one with “New Receiving Record”.</p>
      )}
      {rows?.map(r => (
        <div className="row" key={r.record_id}>
          <div>
            <div><strong>{r.record_id}</strong></div>
            <div className="muted">{new Date(r.created_at).toLocaleString()} · {r.status}</div>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {r.decision && <span className={`badge ${r.decision.toLowerCase()}`}>{r.decision}</span>}
            <button
              style={{ margin: 0, padding: '7px 14px', fontSize: 13 }}
              className="cta"
              onClick={() => open(r.record_id)}
              disabled={!!busy}
            >
              {busy === r.record_id ? 'Inspecting…' : r.decision ? 'View' : 'Inspect'}
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
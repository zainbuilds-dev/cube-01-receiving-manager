import { useEffect, useState } from 'react'
import { getRecord, inspect, listRecords } from '../api'
import { EvidenceRecord, RecordSummary } from '../types'

export default function RecordList({ onOpen }: { onOpen: (r: EvidenceRecord) => void }) {
  const [rows, setRows] = useState<RecordSummary[] | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'review'>('all')

  useEffect(() => {
    listRecords().then(setRows).catch(e => setErr(String(e?.message ?? e)))
  }, [])

  async function open(rid: string) {
    setErr(null); setBusy(rid)
    try {
      const rec = await getRecord(rid)
      if ('checks' in rec) onOpen(rec as EvidenceRecord)
      else onOpen(await inspect(rid))
    } catch (e: any) {
      setErr(String(e?.message ?? e))
    } finally {
      setBusy(null)
    }
  }

  const needsReview = (r: RecordSummary) =>
    r.decision === 'UNCERTAIN' || r.status === 'PENDING_REVIEW'
  const shown = rows?.filter(r => filter === 'all' || needsReview(r)) ?? null

  return (
    <div className="card">
      <div className="check-head">
        <h3 style={{ margin: 0 }}>Receiving Records</h3>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className={`cta ${filter === 'all' ? '' : 'muted-btn'}`}
                  style={{ margin: 0, padding: '6px 12px', fontSize: 13 }}
                  onClick={() => setFilter('all')}>All</button>
          <button className={`cta ${filter === 'review' ? '' : 'muted-btn'}`}
                  style={{ margin: 0, padding: '6px 12px', fontSize: 13 }}
                  onClick={() => setFilter('review')}>
            Review queue ({shown ? shown.filter(needsReview).length : '…'})
          </button>
        </div>
      </div>
      {err && <div className="error">{err}</div>}
      {shown === null && !err && <p className="muted">Loading…</p>}
      {shown && shown.length === 0 && (
        <p className="muted">{filter === 'review'
          ? 'No records need review.'
          : 'No records for this organisation — create one with “New Receiving Record”.'}</p>
      )}
      {shown?.map(r => (
        <div className="row" key={r.record_id}>
          <div>
            <div><strong>{r.record_id}</strong> · {r.unit_id}</div>
            <div className="muted">{new Date(r.created_at).toLocaleString()} · {r.status}</div>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {needsReview(r) && <span className="chip">NEEDS REVIEW</span>}
            {r.decision && <span className={`badge ${r.decision.toLowerCase()}`}>{r.decision}</span>}
            <button style={{ margin: 0, padding: '7px 14px', fontSize: 13 }} className="cta"
                    onClick={() => open(r.record_id)} disabled={!!busy}>
              {busy === r.record_id ? 'Inspecting…' : r.decision ? 'View' : 'Inspect'}
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
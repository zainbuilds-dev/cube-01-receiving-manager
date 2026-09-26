import { EvidenceRecord, POLineItem } from '../types'
import { imageUrl } from '../api'

const CHECK_LABELS: Record<string, string> = {
  sku_identity: 'SKU / Product Identity',
  quantity: 'Quantity (Expected vs Observed)',
  variant: 'Variant / Colour',
  carton_damage: 'Carton Condition / Visible Damage',
}
const BADGE: Record<string, string> = {
  PASS: 'pass', FAIL: 'fail', UNCERTAIN: 'uncertain', NOT_APPLICABLE: 'na',
}

function expectedFor(key: string, li: POLineItem): string {
  switch (key) {
    case 'sku_identity': return li.sku
    case 'quantity': return `${li.expected_qty} units`
    case 'variant': return li.variant ?? '—'
    case 'carton_damage': return li.expected_cartons ? `${li.expected_cartons} carton(s), undamaged` : 'undamaged'
    default: return '—'
  }
}

function downloadJson(rec: EvidenceRecord) {
  const blob = new Blob([JSON.stringify(rec, null, 2)], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${rec.record_id}_evidence.json`
  a.click()
  URL.revokeObjectURL(a.href)
}

export default function ResultsView({ record }: { record: EvidenceRecord }) {
  const li = record.subject.line_items[0]
  const shaFor = (iid?: string | null) => record.images.find(i => i.image_id === iid)?.sha256

  return (
    <div>
      <section className={`banner ${record.outcome.decision.toLowerCase()}`}>
        <div>
          <div className="decision">{record.outcome.decision}</div>
          <div className="disposition">{record.outcome.disposition} — {record.outcome.reason}</div>
        </div>
        <div className="meta">
          <div>{record.record_id}</div>
          <div>{record.outcome.decided_by}</div>
          <div>captured {new Date(record.captured_at).toLocaleString()}</div>
        </div>
      </section>

      <section className="card">
        <h3>Expected vs Observed</h3>
        <table className="summary">
          <thead>
            <tr><th>Check</th><th>Expected</th><th>Verdict</th><th>Confidence</th></tr>
          </thead>
          <tbody>
            {record.checks.map(c => (
              <tr key={c.check_key}>
                <td>{CHECK_LABELS[c.check_key] ?? c.check_key}</td>
                <td>{expectedFor(c.check_key, li)}</td>
                <td>
                  <span className={`badge ${BADGE[c.verdict]}`}>{c.verdict}</span>
                  {c.uncertainty_reason && <span className="chip">{c.uncertainty_reason}</span>}
                </td>
                <td>{Math.round(c.confidence * 100)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {record.checks.map(c => (
        <section className="card" key={c.check_key}>
          <div className="check-head">
            <h3>{CHECK_LABELS[c.check_key] ?? c.check_key}</h3>
            <span className={`badge ${BADGE[c.verdict]}`}>{c.verdict}</span>
          </div>
          <p className="detail">{c.detail}</p>
          {c.uncertainty_reason && <span className="chip big">UNCERTAIN — {c.uncertainty_reason}</span>}
          <div className="evidence">
            <h4>Evidence</h4>
            {c.evidence.map((e, i) => {
              const sha = shaFor(e.image_id)
              return (
                <div className="ev" key={i}>
                  {sha && (
                    <a href={imageUrl(sha)} target="_blank" rel="noreferrer">
                      <img src={imageUrl(sha)} alt={e.image_id ?? 'evidence'} />
                    </a>
                  )}
                  <div>
                    <div className="ev-type">
                      {e.type}{e.image_id ? ` · ${e.image_id}` : ''} · strength {Math.round(e.strength * 100)}%
                    </div>
                    <div>{e.description}</div>
                    {e.quote && <div><code>“{e.quote}”</code></div>}
                  </div>
                </div>
              )
            })}
          </div>
          <div className="prov">
            model: <code>{c.model_version}</code> · latency {c.latency_ms} ms
          </div>
        </section>
      ))}

      <section className="card">
        <h3>Evidence Record</h3>
        <div className="prov">
          schema {record.schema_version} · agent {record.agent.name} v{record.agent.version} ·
          PO {record.subject.po_number} · content hash <code>{record.content_hash.slice(0, 20)}…</code>
        </div>
        <p className="muted">
          Overrides: {record.overrides.length === 0 ? 'none — original machine decision stands' : `${record.overrides.length} recorded`}
        </p>
        <button className="cta" onClick={() => downloadJson(record)}>Export Evidence JSON</button>
      </section>
    </div>
  )
}
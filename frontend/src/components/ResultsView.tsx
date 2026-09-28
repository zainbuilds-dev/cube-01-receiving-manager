import { useEffect, useState } from 'react'
import { EvidenceRecord, POLineItem } from '../types'
import { fetchImageUrl } from '../api'

const CHECK_LABELS: Record<string, string> = {
  sku_identity: 'SKU / Product Identity',
  colour: 'Colour (spec)',
  variant: 'Variant (spec)',
  quantity: 'Quantity (ordered vs received)',
  carton_count: 'Carton Count',
  carton_damage: 'Carton Condition',
  unit_damage: 'Product Condition',
    units_per_carton: 'Units per Carton',
  missing_components: 'Components (spec)',
  other_quality: 'Other Quality Issues',
}
const BADGE: Record<string, string> = {
  PASS: 'pass', FAIL: 'fail', UNCERTAIN: 'uncertain', NOT_APPLICABLE: 'na',
}
const SUMMARY_ROWS: [string, string][] = [
  ['identity_match', 'Identity match'],
  ['carton_damage', 'Carton damage'],
  ['unit_damage', 'Unit damage'],
  ['cartons_received', 'Cartons received'],
  ['units_per_carton_counted', 'Units per carton (counted)'],
  ['qty_received', 'Qty received'],
]

function expectedFor(key: string, li: POLineItem): string {
  switch (key) {
    case 'sku_identity': return li.sku
    case 'colour': return li.spec_colour ?? '—'
    case 'variant': return li.spec_variant ?? '—'
    case 'quantity': return `${li.qty_ordered} units`
    case 'carton_count': return li.cartons_ordered ? `${li.cartons_ordered} carton(s)` : '—'
    case 'carton_damage': return 'undamaged'
    case 'unit_damage': return 'undamaged'
    case 'units_per_carton': return li.units_per_carton_ordered ? `${li.units_per_carton_ordered} per carton` : '—'
    case 'missing_components': return li.spec_components ? li.spec_components.join('; ') : '—'
    case 'other_quality': return 'none'
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
  const [urls, setUrls] = useState<Record<string, string>>({})

  useEffect(() => {
    let dead = false
    const made: Record<string, string> = {}
    Promise.all(record.images.map(async im => {
      made[im.sha256] = await fetchImageUrl(im.sha256)
    })).then(() => { if (!dead) setUrls({ ...made }) }).catch(() => {})
    return () => { dead = true; Object.values(made).forEach(u => URL.revokeObjectURL(u)) }
  }, [record.record_id])

  const urlFor = (iid?: string | null) => {
    const sha = record.images.find(i => i.image_id === iid)?.sha256
    return sha ? urls[sha] : undefined
  }

  return (
    <div>
      <section className={`banner ${record.outcome.decision.toLowerCase()}`}>
        <div>
          <div className="decision">{record.outcome.decision}</div>
          <div className="disposition">{record.outcome.disposition} — {record.outcome.reason}</div>
        </div>
        <div className="meta">
          <div>{record.record_id} · {record.subject.unit_id}</div>
          <div>org: {record.organization_id}</div>
          <div>{record.outcome.decided_by}</div>
          <div>captured {new Date(record.captured_at).toLocaleString()}</div>
        </div>
      </section>

      {record.receiving_summary && (
        <section className="card">
          <h3>Receiving Summary (stage contract)</h3>
          <table className="summary">
            <tbody>
              {SUMMARY_ROWS.map(([k, label]) => (
                <tr key={k}>
                  <td>{label}</td>
                  <td><strong>{String((record.receiving_summary as any)[k])}</strong></td>
                </tr>
              ))}
              <tr>
                <td>Quality flags</td>
                <td>{record.receiving_summary.quality_flags.length
                  ? record.receiving_summary.quality_flags.join('; ') : '—'}</td>
              </tr>
            </tbody>
          </table>
          {record.receiving_summary.note && <p className="muted">{record.receiving_summary.note}</p>}
          {record.inspection_status === 'PENDING_REVIEW' && (
            <span className="chip big">PENDING REVIEW — extraction failed; human review required</span>
          )}
        </section>
      )}

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
              const url = urlFor(e.image_id)
              return (
                <div className="ev" key={i}>
                  {url && (<a href={url} target="_blank" rel="noreferrer"><img src={url} alt={e.image_id ?? 'evidence'} /></a>)}
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
          <div className="prov">model: <code>{c.model_version}</code> · latency {c.latency_ms} ms</div>
        </section>
      ))}

      <section className="card">
        <h3>Evidence Record</h3>
        <div className="prov">
          schema {record.schema_version} · agent {record.agent.name} v{record.agent.version} ·
          PO {record.subject.po_number} line {record.subject.po_line} ·
          content hash <code>{record.content_hash.slice(0, 20)}…</code>
        </div>
        <p className="muted">
          Overrides: {record.overrides.length === 0
            ? 'none — original machine decision stands'
            : `${record.overrides.length} recorded`}
        </p>
        <button className="cta" onClick={() => downloadJson(record)}>Export Evidence JSON</button>
      </section>
    </div>
  )
}
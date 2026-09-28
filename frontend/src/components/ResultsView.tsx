import { useEffect, useState } from 'react'
import { EvidenceRecord, POLineItem } from '../types'
import { fetchImageUrl, overrideRecord } from '../api'

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
    case 'units_per_carton': return li.units_per_carton_ordered ? `${li.units_per_carton_ordered} per carton` : '—'
    case 'missing_components': return li.spec_components ? li.spec_components.join('; ') : '—'
    case 'carton_damage': return 'undamaged'
    case 'unit_damage': return 'undamaged'
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

interface OverrideEntry {
  override_by: string; override_reason: string
  original_decision: string; new_decision: string; timestamp: string
}

export default function ResultsView({ record }: { record: EvidenceRecord }) {
  const [rec, setRec] = useState<EvidenceRecord>(record)
  const li = rec.subject.line_items[0]
  const [urls, setUrls] = useState<Record<string, string>>({})
  const [ovBy, setOvBy] = useState('')
  const [ovReason, setOvReason] = useState('')
  const [ovDecision, setOvDecision] = useState('PASS')
  const [ovBusy, setOvBusy] = useState(false)
  const [ovErr, setOvErr] = useState<string | null>(null)

  useEffect(() => { setRec(record) }, [record])

  useEffect(() => {
    let dead = false
    const made: Record<string, string> = {}
    Promise.all(rec.images.map(async im => {
      made[im.sha256] = await fetchImageUrl(im.sha256)
    })).then(() => { if (!dead) setUrls({ ...made }) }).catch(() => {})
    return () => { dead = true; Object.values(made).forEach(u => URL.revokeObjectURL(u)) }
  }, [rec.record_id])

  const urlFor = (iid?: string | null) => {
    const sha = rec.images.find(i => i.image_id === iid)?.sha256
    return sha ? urls[sha] : undefined
  }

  async function submitOverride() {
    setOvErr(null); setOvBusy(true)
    try {
      setRec(await overrideRecord(rec.record_id, {
        override_by: ovBy, override_reason: ovReason, new_decision: ovDecision,
      }))
      setOvBy(''); setOvReason('')
    } catch (e: any) {
      setOvErr(String(e?.message ?? e))
    } finally {
      setOvBusy(false)
    }
  }

  return (
    <div>
      <section className={`banner ${rec.outcome.decision.toLowerCase()}`}>
        <div>
          <div className="decision">
            {rec.outcome.decision}{rec.status === 'OVERRIDDEN' ? ' (OVERRIDDEN)' : ''}
          </div>
          <div className="disposition">{rec.outcome.disposition} — {rec.outcome.reason}</div>
        </div>
        <div className="meta">
          <div>{rec.record_id} · {rec.subject.unit_id}</div>
          <div>org: {rec.organization_id}</div>
          <div>{rec.outcome.decided_by}</div>
          <div>captured {new Date(rec.captured_at).toLocaleString()}</div>
        </div>
      </section>

      {rec.receiving_summary && (
        <section className="card">
          <h3>Receiving Summary (stage contract)</h3>
          <table className="summary">
            <tbody>
              {SUMMARY_ROWS.map(([k, label]) => (
                <tr key={k}>
                  <td>{label}</td>
                  <td><strong>{String((rec.receiving_summary as any)[k])}</strong></td>
                </tr>
              ))}
              <tr>
                <td>Quality flags</td>
                <td>{rec.receiving_summary.quality_flags.length
                  ? rec.receiving_summary.quality_flags.join('; ') : '—'}</td>
              </tr>
            </tbody>
          </table>
          {rec.receiving_summary.note && <p className="muted">{rec.receiving_summary.note}</p>}
          {rec.inspection_status === 'PENDING_REVIEW' && (
            <span className="chip big">PENDING REVIEW — extraction failed or photos rejected; human review required</span>
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
            {rec.checks.map(c => (
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

      {rec.checks.map(c => (
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
        <h3>Human Review & Override</h3>
        {(rec.overrides as OverrideEntry[]).length > 0 && (
          <div>
            <h4>Override history</h4>
            {(rec.overrides as OverrideEntry[]).map((o, i) => (
              <div className="ev" key={i}>
                <div>
                  <div className="ev-type">
                    {o.original_decision} → {o.new_decision} · by {o.override_by} ·{' '}
                    {new Date(o.timestamp).toLocaleString()}
                  </div>
                  <div>{o.override_reason}</div>
                </div>
              </div>
            ))}
          </div>
        )}
        <div className="grid2">
          <div>
            <label>Operator ID</label>
            <input value={ovBy} onChange={e => setOvBy(e.target.value)} />
          </div>
          <div>
            <label>New decision</label>
            <select value={ovDecision} onChange={e => setOvDecision(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', border: '1px solid var(--line)', borderRadius: 6 }}>
              <option>PASS</option><option>FAIL</option><option>UNCERTAIN</option>
            </select>
          </div>
        </div>
        <div>
          <label>Override reason (required, recorded in the audit trail)</label>
          <textarea value={ovReason} onChange={e => setOvReason(e.target.value)}
                    rows={3} style={{ width: '100%', padding: '8px 10px',
                    border: '1px solid var(--line)', borderRadius: 6, fontFamily: 'inherit' }} />
        </div>
        {ovErr && <div className="error">{ovErr}</div>}
        <button className="cta" onClick={submitOverride}
                disabled={ovBusy || !ovBy.trim() || !ovReason.trim()}>
          {ovBusy ? 'Recording…' : 'Record Override'}
        </button>
      </section>

      <section className="card">
        <h3>Evidence Record</h3>
        <div className="prov">
          schema {rec.schema_version} · agent {rec.agent.name} v{rec.agent.version} ·
          PO {rec.subject.po_number} line {rec.subject.po_line} ·
          content hash <code>{rec.content_hash.slice(0, 20)}…</code>
        </div>
        <div className="prov">
          Photo quality: {rec.images.map(i =>
            `${i.image_id}: ${i.quality
              ? i.quality.verdict + (i.quality.reasons.length
                  ? ` (${i.quality.reasons.join(', ')})` : '')
              : 'not assessed'}`).join(' · ')}
        </div>
        <p className="muted">
          Overrides: {(rec.overrides as OverrideEntry[]).length === 0
            ? 'none — original machine decision stands'
            : `${(rec.overrides as OverrideEntry[]).length} recorded (original decisions preserved)`}
        </p>
        <button className="cta" onClick={() => downloadJson(rec)}>Export Evidence JSON</button>
      </section>
    </div>
  )
}
import { useState } from 'react'
import { createRecord, inspect, uploadImages } from '../api'
import { EvidenceRecord } from '../types'

export default function NewRecordForm(
  { onDone, onCancel }: { onDone: (r: EvidenceRecord) => void; onCancel: () => void },
) {
  const [po_number, setPoNumber] = useState('PO-2026-0142')
  const [supplier, setSupplier] = useState('Acme Supplies')
  const [sku, setSku] = useState('BLUE-BOTTLE-001')
  const [product_name, setProductName] = useState('Sports Bottle 750ml')
  const [expected_qty, setQty] = useState('24')
  const [variant, setVariant] = useState('Blue')
  const [expected_cartons, setCartons] = useState('1')
  const [units_per_carton, setUpc] = useState('24')
  const [files, setFiles] = useState<File[]>([])
  const [stage, setStage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    setError(null)
    if (!po_number || !sku || !expected_qty) return setError('PO number, SKU and expected quantity are required.')
    if (files.length === 0) return setError('Upload at least one receiving photograph.')
    try {
      setStage('Creating receiving record…')
      const { record_id } = await createRecord({
        po_number,
        supplier: supplier || null,
        line_items: [{
          sku,
          product_name: product_name || null,
          expected_qty: Number(expected_qty),
          variant: variant || null,
          expected_cartons: expected_cartons ? Number(expected_cartons) : null,
          units_per_carton: units_per_carton ? Number(units_per_carton) : null,
        }],
      })
      setStage(`Uploading ${files.length} photograph(s)…`)
      await uploadImages(record_id, files)
      setStage('Running AI inspection — extracting observations, evaluating checks, deciding (15–60 s)…')
      const rec = await inspect(record_id)
      setStage(null)
      onDone(rec)
    } catch (e: any) {
      setStage(null)
      setError(String(e?.message ?? e))
    }
  }

  return (
    <div>
      <div className="card">
        <h3>1 · Purchase Order</h3>
        <div className="grid2">
          <div><label>PO Number *</label><input value={po_number} onChange={e => setPoNumber(e.target.value)} /></div>
          <div><label>Supplier</label><input value={supplier} onChange={e => setSupplier(e.target.value)} /></div>
          <div><label>SKU *</label><input value={sku} onChange={e => setSku(e.target.value)} /></div>
          <div><label>Product Name</label><input value={product_name} onChange={e => setProductName(e.target.value)} /></div>
          <div><label>Expected Quantity *</label><input type="number" value={expected_qty} onChange={e => setQty(e.target.value)} /></div>
          <div><label>Variant / Colour</label><input value={variant} onChange={e => setVariant(e.target.value)} /></div>
          <div><label>Expected Cartons</label><input type="number" value={expected_cartons} onChange={e => setCartons(e.target.value)} /></div>
          <div><label>Units per Carton</label><input type="number" value={units_per_carton} onChange={e => setUpc(e.target.value)} /></div>
        </div>
      </div>

      <div className="card">
        <h3>2 · Receiving Photographs</h3>
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          onChange={e => setFiles(Array.from(e.target.files ?? []))}
        />
        {files.length > 0 && (
          <p className="muted">{files.length} file(s): {files.map(f => f.name).join(', ')}</p>
        )}
      </div>

      {error && <div className="error">{error}</div>}
      {stage && (
        <div className="stage"><div className="spinner" />{stage}</div>
      )}

      <button className="cta" onClick={submit} disabled={!!stage}>
        {stage ? 'Processing…' : 'Run Receiving Inspection'}
      </button>
      {' '}
      <button className="cta" style={{ background: '#64748b' }} onClick={onCancel} disabled={!!stage}>
        Cancel
      </button>
    </div>
  )
}
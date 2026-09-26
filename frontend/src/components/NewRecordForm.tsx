import { useState } from 'react'
import { createRecord, inspect, uploadImages } from '../api'
import { EvidenceRecord } from '../types'

export default function NewRecordForm(
  { onDone, onCancel }: { onDone: (r: EvidenceRecord) => void; onCancel: () => void },
) {
  const [f, setF] = useState({
    unit_id: 'UNIT-0201', po_number: 'PO-7026', po_line: '1',
    supplier: 'Supplier North (DUMMY)', operator_id: 'op_eli',
    sku: 'SKU-BOTTLE-750', asin: 'B0DUMMY622', product_title: 'Steel Water Bottle',
    spec_colour: 'black', spec_variant: '750ml', spec_components: 'bottle;lid',
    cartons_ordered: '2', units_per_carton_ordered: '12', qty_ordered: '24',
  })
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setF(prev => ({ ...prev, [k]: e.target.value }))
  const [files, setFiles] = useState<File[]>([])
  const [stage, setStage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    setError(null)
    if (!f.unit_id || !f.po_number || !f.sku || !f.qty_ordered)
      return setError('Unit ID, PO number, SKU and ordered quantity are required.')
    if (files.length === 0) return setError('Upload at least one receiving photograph.')
    try {
      setStage('Creating receiving record…')
      const { record_id } = await createRecord({
        unit_id: f.unit_id, po_number: f.po_number, po_line: Number(f.po_line) || 1,
        supplier: f.supplier || null, operator_id: f.operator_id || null,
        line_items: [{
          sku: f.sku,
          asin: f.asin || null,
          product_title: f.product_title || null,
          spec_colour: f.spec_colour || null,
          spec_variant: f.spec_variant || null,
          spec_components: f.spec_components
            ? f.spec_components.split(';').map(s => s.trim()).filter(Boolean) : null,
          cartons_ordered: f.cartons_ordered ? Number(f.cartons_ordered) : null,
          units_per_carton_ordered: f.units_per_carton_ordered
            ? Number(f.units_per_carton_ordered) : null,
          qty_ordered: Number(f.qty_ordered),
        }],
      })
      setStage(`Uploading ${files.length} photograph(s)…`)
      await uploadImages(record_id, files)
      setStage('Running AI inspection — quality gate, extraction, checks, decision (15–60 s)…')
      onDone(await inspect(record_id))
    } catch (e: any) {
      setStage(null)
      setError(String(e?.message ?? e))
    }
  }

  const field = (label: string, key: keyof typeof f, type = 'text') => (
    <div>
      <label>{label}</label>
      <input type={type} value={f[key]} onChange={set(key)} />
    </div>
  )

  return (
    <div>
      <div className="card">
        <h3>1 · Purchase Order</h3>
        <div className="grid2">
          {field('Unit ID *', 'unit_id')}
          {field('PO Number *', 'po_number')}
          {field('PO Line', 'po_line', 'number')}
          {field('Supplier', 'supplier')}
          {field('Operator ID', 'operator_id')}
        </div>
      </div>

      <div className="card">
        <h3>2 · Line Item Spec (expected)</h3>
        <div className="grid2">
          {field('SKU *', 'sku')}
          {field('ASIN', 'asin')}
          {field('Product Title', 'product_title')}
          {field('Spec Colour', 'spec_colour')}
          {field('Spec Variant', 'spec_variant')}
          {field('Spec Components (;-separated)', 'spec_components')}
          {field('Cartons Ordered', 'cartons_ordered', 'number')}
          {field('Units per Carton (ordered)', 'units_per_carton_ordered', 'number')}
          {field('Qty Ordered *', 'qty_ordered', 'number')}
        </div>
      </div>

      <div className="card">
        <h3>3 · Receiving Photographs</h3>
        <input type="file" accept="image/jpeg,image/png,image/webp" multiple
               onChange={e => setFiles(Array.from(e.target.files ?? []))} />
        {files.length > 0 && <p className="muted">{files.length} file(s): {files.map(x => x.name).join(', ')}</p>}
      </div>

      {error && <div className="error">{error}</div>}
      {stage && <div className="stage"><div className="spinner" />{stage}</div>}

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
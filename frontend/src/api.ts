import { EvidenceRecord, PO, RecordSummary } from './types'

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText
    try { const b = await res.json(); detail = (b as any).detail || JSON.stringify(b) } catch { /* keep statusText */ }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export const createRecord = (po: PO) =>
  fetch('/api/records', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(po),
  }).then(r => j<{ record_id: string }>(r))

export async function uploadImages(rid: string, files: File[]) {
  const fd = new FormData()
  files.forEach(f => fd.append('files', f))
  return j<{ uploaded: { image_id: string; sha256: string }[] }>(
    await fetch(`/api/records/${rid}/images`, { method: 'POST', body: fd }))
}

export const inspect = (rid: string) =>
  fetch(`/api/records/${rid}/inspect`, { method: 'POST' }).then(r => j<EvidenceRecord>(r))

export const listRecords = () => fetch('/api/records').then(r => j<RecordSummary[]>(r))

export async function getRecord(rid: string): Promise<EvidenceRecord | { status: string }> {
  return j(await fetch(`/api/records/${rid}`))
}

export const imageUrl = (sha: string) => `/api/images/${sha}`
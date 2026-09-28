import { EvidenceRecord, PO, RecordSummary } from './types'

const TOKEN_KEY = 'rcv_org_token'
export const ORGS = [
  { id: 'org_demo_alpha', label: 'Alpha', token: 'alpha-demo-token' },
  { id: 'org_demo_bravo', label: 'Bravo', token: 'bravo-demo-token' },
]
export function currentOrgToken(): string {
  return localStorage.getItem(TOKEN_KEY) || ORGS[0].token
}
export function currentOrgId(): string {
  return currentOrgToken() === ORGS[1].token ? ORGS[1].id : ORGS[0].id
}
export function setOrg(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
  window.location.reload()
}
const authHeaders = (json = false): Record<string, string> => {
  const h: Record<string, string> = { Authorization: `Bearer ${currentOrgToken()}` }
  if (json) h['Content-Type'] = 'application/json'
  return h
}

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText
    try { const b = await res.json(); detail = (b as any).detail || JSON.stringify(b) } catch { /* keep */ }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export const createRecord = (po: PO) =>
  fetch('/api/records', { method: 'POST', headers: authHeaders(true), body: JSON.stringify(po) })
    .then(r => j<{ record_id: string }>(r))

export async function uploadImages(rid: string, files: File[]) {
  const fd = new FormData()
  files.forEach(f => fd.append('files', f))
  return j<{ uploaded: { image_id: string; sha256: string }[] }>(
    await fetch(`/api/records/${rid}/images`, { method: 'POST', headers: authHeaders(), body: fd }))
}

export const inspect = (rid: string) =>
  fetch(`/api/records/${rid}/inspect`, { method: 'POST', headers: authHeaders() })
    .then(r => j<EvidenceRecord>(r))

export const overrideRecord = (rid: string, o: { override_by: string; override_reason: string; new_decision: string }) =>
  fetch(`/api/records/${rid}/override`, { method: 'POST', headers: authHeaders(true), body: JSON.stringify(o) })
    .then(r => j<EvidenceRecord>(r))

export const listRecords = () =>
  fetch('/api/records', { headers: authHeaders() }).then(r => j<RecordSummary[]>(r))

export async function getRecord(rid: string): Promise<EvidenceRecord | { status: string }> {
  return j(await fetch(`/api/records/${rid}`, { headers: authHeaders() }))
}

export async function fetchImageUrl(sha: string): Promise<string> {
  const res = await fetch(`/api/images/${sha}`, { headers: authHeaders() })
  if (!res.ok) throw new Error('image unavailable')
  return URL.createObjectURL(await res.blob())
}
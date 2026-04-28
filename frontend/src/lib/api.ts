import type {
  UploadResponse, InspectResponse, AuditResponse,
  NarrativeResponse, ColumnMapping, ProxyFinding,
  BiasMetrics, MitigationMetrics
} from './types'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Wraps fetch to catch network errors (backend not running) and produce
 * actionable error messages instead of the cryptic "Failed to fetch".
 */
async function safeFetch(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init)
  } catch (err) {
    // TypeError: Failed to fetch — means the backend is unreachable
    if (err instanceof TypeError && err.message.includes('Failed to fetch')) {
      throw new Error(
        `Cannot connect to backend server at ${BASE_URL}. ` +
        `Please make sure the backend is running: cd backend && python -m uvicorn main:app --port 8000`
      )
    }
    throw err
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    try { const d = await res.json(); msg = d.detail || msg } catch (_) {}
    throw new Error(msg)
  }
  return res.json()
}

/** Check if the backend is reachable */
export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000),
    })
    return res.ok
  } catch {
    return false
  }
}

export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  const res = await safeFetch(`${BASE_URL}/upload`, { method: 'POST', body: form })
  return handleResponse(res)
}

export async function inspectDataset(file_id: string, mapping: ColumnMapping): Promise<InspectResponse> {
  const res = await safeFetch(`${BASE_URL}/inspect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id, ...mapping }),
  })
  return handleResponse(res)
}

export async function runAudit(file_id: string, mapping: ColumnMapping): Promise<AuditResponse> {
  const res = await safeFetch(`${BASE_URL}/audit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id, ...mapping }),
  })
  return handleResponse(res)
}

export async function generateNarrative(
  file_id: string,
  proxy_findings: ProxyFinding[],
  bias_metrics: BiasMetrics,
  mitigation_metrics: MitigationMetrics,
  company_name: string
): Promise<NarrativeResponse> {
  const res = await safeFetch(`${BASE_URL}/narrative`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id, proxy_findings, bias_metrics, mitigation_metrics, company_name }),
  })
  return handleResponse(res)
}

export async function downloadReport(payload: object): Promise<void> {
  const res = await safeFetch(`${BASE_URL}/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Report generation failed')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `nishpaksh_audit_${new Date().toISOString().split('T')[0]}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

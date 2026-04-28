import { useState, useCallback, useEffect } from 'react'
import type { AuditState, AuditStep, ColumnMapping } from '../lib/types'
import * as api from '../lib/api'

const INITIAL_STATE: AuditState = {
  step: 'upload',
  file_id: null,
  upload_response: null,
  column_mapping: null,
  inspect_response: null,
  audit_response: null,
  narrative_response: null,
  company_name: 'the company',
  loading: false,
  error: null,
}

export function useAudit() {
  const [state, setState] = useState<AuditState>(INITIAL_STATE)
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null) // null = checking

  const setLoading = (loading: boolean) => setState(s => ({ ...s, loading, error: null }))
  const setError = (error: string) => setState(s => ({ ...s, loading: false, error }))
  const goTo = (step: AuditStep) => setState(s => ({ ...s, step }))

  /** Check backend connectivity on mount and periodically while offline */
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null

    const check = async () => {
      const ok = await api.checkHealth()
      setBackendOnline(ok)
      // If online, stop polling; if offline, keep checking every 5s
      if (ok && interval) {
        clearInterval(interval)
        interval = null
      } else if (!ok && !interval) {
        interval = setInterval(check, 5000)
      }
    }

    check()
    return () => { if (interval) clearInterval(interval) }
  }, [])

  /** Step 1: Upload CSV */
  const uploadFile = useCallback(async (file: File) => {
    setLoading(true)
    try {
      const res = await api.uploadFile(file)
      setState(s => ({ ...s, loading: false, upload_response: res, file_id: res.file_id }))
      setBackendOnline(true)
    } catch (e: unknown) {
      const msg = (e as Error).message
      if (msg.includes('Cannot connect to backend')) setBackendOnline(false)
      setError(msg)
    }
  }, [])

  /** Step 2: Set column mapping & run inspect */
  const runInspect = useCallback(async (mapping: ColumnMapping, companyName: string) => {
    if (!state.file_id) return
    setState(s => ({ ...s, loading: true, error: null, column_mapping: mapping, company_name: companyName, step: 'inspect' }))
    try {
      const res = await api.inspectDataset(state.file_id, mapping)
      setState(s => ({ ...s, loading: false, inspect_response: res }))
    } catch (e: unknown) {
      const msg = (e as Error).message
      if (msg.includes('Cannot connect to backend')) setBackendOnline(false)
      setError(msg)
    }
  }, [state.file_id])

  /** Step 3: Run audit (proxy detection + bias metrics) then narrative */
  const runAudit = useCallback(async () => {
    if (!state.file_id || !state.column_mapping) return
    setState(s => ({ ...s, loading: true, error: null, step: 'audit' }))
    try {
      const auditRes = await api.runAudit(state.file_id, state.column_mapping)
      setState(s => ({ ...s, audit_response: auditRes }))

      // Auto-generate narrative
      const narRes = await api.generateNarrative(
        state.file_id!,
        auditRes.proxy_findings,
        auditRes.bias_metrics,
        auditRes.mitigation_metrics,
        state.company_name
      )
      setState(s => ({ ...s, loading: false, narrative_response: narRes, step: 'report' }))
    } catch (e: unknown) {
      // If narrative fails (no API key), still go to report with audit data
      const msg = (e as Error).message
      if (msg.includes('Cannot connect to backend')) setBackendOnline(false)
      setState(s => ({ ...s, loading: false, step: 'report', error: msg }))
    }
  }, [state.file_id, state.column_mapping, state.company_name])

  /** Step 4: Download PDF */
  const downloadPdf = useCallback(async () => {
    if (!state.audit_response) return
    setLoading(true)
    try {
      await api.downloadReport({
        company_name: state.company_name,
        proxy_findings: state.audit_response.proxy_findings,
        bias_metrics: state.audit_response.bias_metrics,
        mitigation_metrics: state.audit_response.mitigation_metrics,
        narrative_paragraphs: state.narrative_response?.narrative_paragraphs ?? [],
        dpdp_checklist: state.narrative_response?.dpdp_checklist ?? [
          { article: 'DPDP Act Section 4(1)(b)', description: 'Automated decision processing must not discriminate', status: 'review_required' },
          { article: 'Article 16 — Equal opportunity', description: 'No discrimination in employment', status: 'review_required' },
        ],
      })
      setState(s => ({ ...s, loading: false }))
    } catch (e: unknown) {
      const msg = (e as Error).message
      if (msg.includes('Cannot connect to backend')) setBackendOnline(false)
      setError(msg)
    }
  }, [state])

  const reset = useCallback(() => setState(INITIAL_STATE), [])

  /** Retry backend connection manually */
  const retryConnection = useCallback(async () => {
    setBackendOnline(null) // show "checking" state
    const ok = await api.checkHealth()
    setBackendOnline(ok)
    if (ok) setState(s => ({ ...s, error: null }))
  }, [])

  return { state, backendOnline, uploadFile, runInspect, runAudit, downloadPdf, reset, goTo, retryConnection }
}

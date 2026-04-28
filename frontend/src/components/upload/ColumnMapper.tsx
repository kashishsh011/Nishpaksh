import { useState, useEffect } from 'react'
import type { ColumnInfo, ColumnMapping, UploadResponse } from '../../lib/types'
import Button from '../ui/Button'

interface Props {
  upload: UploadResponse
  onConfirm: (mapping: ColumnMapping, companyName: string) => void
  loading: boolean
}

const TYPE_ICON: Record<string, string> = {
  name: '👤', binary: '⚡', categorical: '🏷️', numeric: '🔢', pincode: '📍', unknown: '❓'
}

/** Use backend smart suggestions to initialize the mapper */
function getInitialMapping(upload: UploadResponse): { outcome: string; positiveVal: string; sensitive: string[] } {
  let outcome = ''
  let positiveVal = '1'
  
  if (upload.suggested_outcome) {
    outcome = upload.suggested_outcome.column
    positiveVal = upload.suggested_outcome.positive_value
  }

  const sensitive = upload.suggested_sensitive ? upload.suggested_sensitive.map(s => s.column) : []

  return { outcome, positiveVal, sensitive }
}

export default function ColumnMapper({ upload, onConfirm, loading }: Props) {
  const detected = getInitialMapping(upload)
  const [outcome, setOutcome] = useState(detected.outcome)
  const [positiveVal, setPositiveVal] = useState(detected.positiveVal)
  const [sensitive, setSensitive] = useState<string[]>(detected.sensitive)
  const [company, setCompany] = useState('')
  const [autoDetected, setAutoDetected] = useState(true)

  // Show auto-detect banner only once
  useEffect(() => {
    if (detected.outcome || detected.sensitive.length > 0) {
      setAutoDetected(true)
    }
  }, [])

  const toggleSensitive = (col: string) => {
    setSensitive(prev => prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col])
    setAutoDetected(false)
  }

  const canSubmit = outcome && sensitive.length > 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Auto-detect banner */}
      {autoDetected && (detected.outcome || detected.sensitive.length > 0) && (
        <div id="auto-detect-banner" role="status" style={{
          padding: '12px 16px', background: 'var(--color-primary-light)',
          border: '1px solid var(--color-primary)', borderRadius: 10,
          fontSize: 13, color: 'var(--color-primary)', fontWeight: 500,
          display: 'flex', alignItems: 'center', gap: 10,
          animation: 'fadeIn 0.3s ease both',
        }}>
          <span style={{ fontSize: 18 }}>🧠</span>
          <span>
            <strong>Auto-detected:</strong>{' '}
            {detected.outcome && <>Outcome → <code style={{ fontFamily: 'var(--font-mono)', fontSize: 12, background: 'rgba(55,48,163,0.1)', padding: '1px 6px', borderRadius: 4 }}>{detected.outcome}</code></>}
            {detected.sensitive.length > 0 && <> · {detected.sensitive.length} sensitive column{detected.sensitive.length > 1 ? 's' : ''}</>}
            {' '}— review & adjust below.
          </span>
        </div>
      )}

      {/* Company name */}
      <div>
        <label htmlFor="company-name-input" style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>
          Company Name (for report)
        </label>
        <input
          id="company-name-input"
          type="text" placeholder="e.g. Acme Corp"
          value={company} onChange={e => setCompany(e.target.value)}
          aria-label="Company name for the audit report"
          style={{ width: '100%', padding: '9px 12px', border: '1.5px solid var(--color-border)', borderRadius: 8, fontSize: 14, fontFamily: 'var(--font-body)', background: 'var(--color-surface)', outline: 'none', boxSizing: 'border-box' }}
        />
      </div>

      {/* Outcome column */}
      <div>
        <label htmlFor="outcome-select" style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>
          Outcome Column <span style={{ color: 'var(--color-danger)' }}>*</span>
        </label>
        <select id="outcome-select" value={outcome} onChange={e => { setOutcome(e.target.value); setAutoDetected(false) }}
          aria-label="Select the column that contains the hiring outcome"
          style={{ width: '100%', padding: '9px 12px', border: '1.5px solid var(--color-border)', borderRadius: 8, fontSize: 14, fontFamily: 'var(--font-body)', background: 'var(--color-surface)' }}>
          <option value="">Select outcome column…</option>
          {upload.columns.map(c => (
            <option key={c.name} value={c.name}>{c.name} ({c.detected_type})</option>
          ))}
        </select>
        {outcome && (
          <div style={{ marginTop: 8 }}>
            <label htmlFor="positive-value-input" style={{ fontSize: 12, color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>
              Positive value (what counts as "hired"):
            </label>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input id="positive-value-input" type="text" value={positiveVal} onChange={e => setPositiveVal(e.target.value)}
                aria-label="Value that represents a positive hiring outcome"
                style={{ padding: '7px 12px', border: '1.5px solid var(--color-border)', borderRadius: 8, fontSize: 13, fontFamily: 'var(--font-mono)', background: 'var(--color-surface)' }} />
              {upload.suggested_outcome?.column === outcome && (
                <span style={{ fontSize: 11, color: 'var(--color-text-faint)', background: 'var(--color-surface-2)', padding: '2px 8px', borderRadius: 4 }}>
                  Auto-detected ({Math.round(upload.suggested_outcome.confidence * 100)}% confidence)
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Sensitive columns */}
      <div>
        <label style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--color-text-muted)', display: 'block', marginBottom: 10 }}>
          Columns to audit for bias <span style={{ color: 'var(--color-danger)' }}>*</span>
        </label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }} role="group" aria-label="Select columns to audit for bias">
          {upload.columns.filter(c => c.name !== outcome).map((col: ColumnInfo) => {
            const checked = sensitive.includes(col.name)
            return (
              <label key={col.name} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 14px', borderRadius: 8, cursor: 'pointer',
                border: `1.5px solid ${checked ? 'var(--color-primary)' : 'var(--color-border)'}`,
                background: checked ? 'var(--color-primary-light)' : 'var(--color-surface)',
                transition: 'all 0.15s',
              }}>
                <input type="checkbox" checked={checked} onChange={() => toggleSensitive(col.name)}
                  aria-label={`Audit column ${col.name} for bias`}
                  style={{ accentColor: 'var(--color-primary)', width: 16, height: 16 }} />
                <span style={{ fontSize: 18 }}>{TYPE_ICON[col.detected_type] ?? '❓'}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--color-text-primary)' }}>{col.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                    {col.detected_type} · sample: {col.sample_values.slice(0, 2).join(', ')}
                    {col.null_pct > 0 && ` · ${(col.null_pct * 100).toFixed(0)}% null`}
                  </div>
                  {upload.suggested_sensitive?.find(s => s.column === col.name) && (
                    <div style={{ fontSize: 10, color: 'var(--color-primary)', marginTop: 4, opacity: 0.8 }}>
                      ↳ {upload.suggested_sensitive.find(s => s.column === col.name)?.reason}
                    </div>
                  )}
                </div>
              </label>
            )
          })}
        </div>
      </div>

      <Button id="run-audit-button" variant="primary" disabled={!canSubmit} loading={loading}
        onClick={() => onConfirm({ outcome_column: outcome, outcome_positive_value: positiveVal, sensitive_columns: sensitive }, company || 'the company')}
        style={{ alignSelf: 'flex-start', padding: '12px 32px', fontSize: 15 }}>
        Run Audit →
      </Button>
    </div>
  )
}

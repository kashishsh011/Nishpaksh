import { useState } from 'react'
import type { BiasMetrics, MitigationMetrics } from '../../lib/types'
import { fixed } from '../../lib/utils'

interface Props { before: BiasMetrics; after: MitigationMetrics }

export default function MitigationToggle({ before, after }: Props) {
  const [show, setShow] = useState<'before' | 'after'>('before')

  const rows = [
    { label: 'Demographic Parity Difference', before: before.demographic_parity_difference, after: after.demographic_parity_difference_after, good: 'lower' },
    { label: 'Equalized Odds Difference',      before: before.equalized_odds_difference,      after: after.equalized_odds_difference_after, good: 'lower' },
    { label: 'Disparate Impact Ratio',          before: before.disparate_impact_ratio,          after: after.disparate_impact_ratio_after, good: 'higher' },
    { label: 'Model Accuracy',                  before: before.model_accuracy,                  after: after.accuracy_after, good: 'higher' },
  ]

  return (
    <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 10, overflow: 'hidden' }}>
      {/* Toggle tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--color-border)' }}>
        {(['before', 'after'] as const).map(t => (
          <button key={t} onClick={() => setShow(t)} style={{
            flex: 1, padding: '12px', fontSize: 13, fontWeight: 600,
            background: show === t ? 'var(--color-primary-light)' : 'transparent',
            color: show === t ? 'var(--color-primary)' : 'var(--color-text-muted)',
            border: 'none', cursor: 'pointer', fontFamily: 'var(--font-body)',
            borderBottom: show === t ? '2px solid var(--color-primary)' : '2px solid transparent',
            transition: 'all 0.15s',
          }}>
            {t === 'before' ? '📊 Before Mitigation' : `✅ After (${after.method ?? 'reweighing'})`}
          </button>
        ))}
      </div>

      {/* Table */}
      <div style={{ padding: '4px 0' }}>
        {rows.map(r => {
          const val = show === 'before' ? r.before : r.after
          const cmp = show === 'after' ? r.before : r.after
          const improved = val != null && cmp != null && (r.good === 'lower' ? val < cmp : val > cmp)
          return (
            <div key={r.label} style={{ display: 'flex', alignItems: 'center', padding: '10px 16px', borderBottom: '1px solid var(--color-border)' }}>
              <span style={{ flex: 1, fontSize: 13, color: 'var(--color-text-primary)' }}>{r.label}</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 15, fontWeight: 500, color: 'var(--color-text-primary)', minWidth: 60, textAlign: 'right' }}>
                {fixed(val, 3)}
              </span>
              {show === 'after' && val != null && cmp != null && (
                <span style={{ marginLeft: 8, fontSize: 11, color: improved ? 'var(--color-safe)' : 'var(--color-danger)', fontWeight: 600 }}>
                  {improved ? '▼' : '▲'} {Math.abs((val - cmp)).toFixed(3)}
                </span>
              )}
            </div>
          )
        })}
      </div>

      <div style={{ padding: '10px 16px', background: 'var(--color-surface-2)', fontSize: 12, color: 'var(--color-text-muted)' }}>
        Mitigation via <strong>{after.method ?? 'reweighing'}</strong> — adjusts group weights during training to reduce disparity.
        Accuracy change: <span style={{ fontFamily: 'var(--font-mono)', color: (after.accuracy_delta ?? 0) >= 0 ? 'var(--color-safe)' : 'var(--color-danger)' }}>
          {after.accuracy_delta != null ? `${after.accuracy_delta > 0 ? '+' : ''}${after.accuracy_delta.toFixed(3)}` : '—'}
        </span>
      </div>
    </div>
  )
}

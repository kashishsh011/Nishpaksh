import DatasetSummary from '../components/inspect/DatasetSummary'
import DistributionGrid from '../components/inspect/DistributionGrid'
import Spinner from '../components/ui/Spinner'
import Button from '../components/ui/Button'
import type { InspectResponse } from '../lib/types'

interface Props {
  inspect: InspectResponse | null
  loading: boolean
  error: string | null
  onContinue: () => void
  onBack: () => void
}

export default function InspectPage({ inspect, loading, error, onContinue, onBack }: Props) {
  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, padding: '60px 0' }} role="status">
      <Spinner size={48} />
      <div style={{ fontSize: 15, color: 'var(--color-text-muted)' }}>Analysing dataset distributions…</div>
    </div>
  )

  if (error) return (
    <div>
      <div role="alert" style={{ padding: '12px 16px', background: 'var(--color-danger-bg)', border: '1px solid var(--color-danger-border)', borderRadius: 8, fontSize: 13, color: 'var(--color-danger)', marginBottom: 16 }}>
        ⚠ {error}
      </div>
      <button onClick={onBack} style={{
        padding: '10px 20px', fontSize: 13, fontWeight: 600, borderRadius: 8,
        border: '1.5px solid var(--color-border)', background: 'var(--color-surface)',
        color: 'var(--color-text-muted)', cursor: 'pointer', fontFamily: 'var(--font-body)',
      }}>
        ← Back to Upload
      </button>
    </div>
  )

  if (!inspect) return null

  const hasDistributions = inspect.column_distributions &&
    inspect.column_distributions.some(d => d.distribution && d.distribution.length > 0)

  return (
    <div>
      {/* Back button */}
      <button onClick={onBack} style={{
        padding: '6px 14px', fontSize: 12, fontWeight: 600, borderRadius: 6,
        border: '1.5px solid var(--color-border)', background: 'var(--color-surface)',
        color: 'var(--color-text-muted)', cursor: 'pointer', fontFamily: 'var(--font-body)',
        marginBottom: 20, transition: 'all 0.15s',
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--color-primary)'; e.currentTarget.style.color = 'var(--color-primary)' }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.color = 'var(--color-text-muted)' }}
      >
        ← Back to Upload
      </button>

      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 28, color: 'var(--color-text-primary)', margin: '0 0 8px' }}>
          Dataset Inspection
        </h1>
        <p style={{ fontSize: 14, color: 'var(--color-text-muted)', margin: 0, lineHeight: 1.6 }}>
          Hire rate distribution across each sensitive column. Bars coloured <span style={{ color: 'var(--color-safe)', fontWeight: 600 }}>teal</span> are above average, <span style={{ color: '#D97706', fontWeight: 600 }}>amber</span> are moderate, and <span style={{ color: 'var(--color-danger)', fontWeight: 600 }}>coral</span> are significantly below average.
        </p>
      </div>

      <DatasetSummary health={inspect.dataset_health} />

      {hasDistributions ? (
        <>
          <div style={{ margin: '28px 0 20px', fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            Hire Rate by Group
          </div>
          <DistributionGrid distributions={inspect.column_distributions} overallRate={inspect.dataset_health.hire_rate_overall} />
        </>
      ) : (
        <div style={{
          margin: '28px 0 20px', padding: '16px 20px',
          background: 'var(--color-warning-bg)', border: '1px solid var(--color-warning-border)',
          borderRadius: 10, fontSize: 13, color: 'var(--color-warning)', lineHeight: 1.6,
        }}>
          <strong>📊 No group distributions to display.</strong> The selected sensitive columns have too many unique values (e.g. names) for a meaningful group breakdown.
          This is normal — proceed to the full audit for proxy detection and bias metrics analysis.
        </div>
      )}

      <div style={{ marginTop: 28, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <Button variant="primary" onClick={onContinue} style={{ padding: '12px 32px', fontSize: 15 }}>
          Run Full Bias Audit →
        </Button>
        <button onClick={onBack} style={{
          padding: '12px 20px', fontSize: 13, fontWeight: 600, borderRadius: 8,
          border: '1.5px solid var(--color-border)', background: 'var(--color-surface)',
          color: 'var(--color-text-muted)', cursor: 'pointer', fontFamily: 'var(--font-body)',
        }}>
          ← Re-map Columns
        </button>
      </div>
    </div>
  )
}

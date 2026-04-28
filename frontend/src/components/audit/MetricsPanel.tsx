import MetricCard from '../ui/MetricCard'
import type { BiasMetrics, Severity } from '../../lib/types'
import { pct } from '../../lib/utils'

interface Props { metrics: BiasMetrics }

function getSeverityDPD(v: number | null): Severity {
  if (v == null) return 'compliant'
  return v > 0.2 ? 'high' : v > 0.1 ? 'medium' : 'compliant'
}
function getSeverityDIR(v: number | null): Severity {
  if (v == null) return 'compliant'
  return v < 0.6 ? 'high' : v < 0.8 ? 'medium' : 'compliant'
}

export default function MetricsPanel({ metrics }: Props) {
  // Check if we actually have any computed metrics
  const hasData = metrics.demographic_parity_difference != null ||
    metrics.equalized_odds_difference != null ||
    metrics.disparate_impact_ratio != null

  if (!hasData) {
    return (
      <div style={{
        textAlign: 'center', padding: '32px 24px',
        background: 'var(--color-surface)', border: '1px solid var(--color-border)',
        borderRadius: 10, color: 'var(--color-text-muted)',
      }}>
        <div style={{ fontSize: 32, marginBottom: 10 }}>📊</div>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 6 }}>Insufficient group data for bias metrics</div>
        <div style={{ fontSize: 12, lineHeight: 1.6 }}>
          The selected sensitive columns don't have enough members per group to compute
          statistically meaningful metrics. Try selecting columns with fewer unique values (e.g. gender, category).
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: 14 }}>
        <MetricCard
          label="Demographic Parity Difference"
          value={metrics.demographic_parity_difference}
          severity={getSeverityDPD(metrics.demographic_parity_difference)}
          threshold="< 0.10"
          description="Gap between highest and lowest group selection rates. Higher = more disparity."
        />
        <MetricCard
          label="Equalized Odds Difference"
          value={metrics.equalized_odds_difference}
          severity={getSeverityDPD(metrics.equalized_odds_difference)}
          threshold="< 0.10"
          description="Spread in true positive rates across groups. Measures whether qualified candidates are treated equally."
        />
        <MetricCard
          label="Disparate Impact Ratio"
          value={metrics.disparate_impact_ratio}
          severity={getSeverityDIR(metrics.disparate_impact_ratio)}
          threshold="> 0.80 (4/5ths rule)"
          description="Ratio of least-selected to most-selected group. Below 0.80 is prima facie adverse impact."
        />
      </div>

      {/* By-group breakdown */}
      {Object.entries(metrics.by_group ?? {}).map(([attr, groups]) => (
        <div key={attr}>
          <div style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: 10 }}>
            By group: {attr}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {Object.entries(groups).map(([grp, vals]) => (
              <div key={grp} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 14px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 8 }}>
                <span style={{ flex: 1, fontSize: 13, fontWeight: 500, color: 'var(--color-text-primary)' }}>{grp}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--color-text-primary)' }}>
                  {pct(vals.selection_rate)} selected
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-text-muted)' }}>
                  TPR {pct(vals.true_positive_rate)}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}

      {metrics.disparate_impact_flag && (
        <div style={{ padding: '12px 16px', background: 'var(--color-danger-bg)', border: '1px solid var(--color-danger-border)', borderRadius: 8 }}>
          <span style={{ fontWeight: 700, color: 'var(--color-danger)', fontSize: 13 }}>
            ⚠ Disparate Impact Threshold Breached
          </span>
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)', marginLeft: 10 }}>
            DIR {metrics.disparate_impact_ratio?.toFixed(2)} is below the legal reference of {metrics.disparate_impact_legal_threshold}
          </span>
        </div>
      )}
    </div>
  )
}

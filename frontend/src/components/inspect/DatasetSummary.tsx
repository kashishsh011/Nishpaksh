import type { InspectResponse } from '../../lib/types'
import { pct } from '../../lib/utils'

interface Props { health: InspectResponse['dataset_health'] }

export default function DatasetSummary({ health }: Props) {
  const stats = [
    { label: 'Total Rows',    value: health.total_rows.toLocaleString() },
    { label: 'Usable Rows',   value: health.usable_rows.toLocaleString() },
    { label: 'Dropped Rows',  value: (health.total_rows - health.usable_rows).toLocaleString() },
    { label: 'Overall Hire Rate', value: pct(health.hire_rate_overall) },
  ]
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px,1fr))', gap: 16 }}>
      {stats.map(s => (
        <div key={s.label} style={{
          background: 'var(--color-surface)', border: '1px solid var(--color-border)',
          borderRadius: 10, padding: '16px 20px',
        }}>
          <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: 6 }}>
            {s.label}
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 28, fontWeight: 500, color: 'var(--color-text-primary)' }}>
            {s.value}
          </div>
        </div>
      ))}
    </div>
  )
}

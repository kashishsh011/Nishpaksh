import Badge from './Badge'
import type { Severity } from '../../lib/types'
import { fixed } from '../../lib/utils'

interface Props {
  label: string
  value: number | null
  severity: Severity | 'neutral'
  threshold?: string
  description: string
}

export default function MetricCard({ label, value, severity, threshold, description }: Props) {
  const borderColors: Record<string, string> = {
    high: 'var(--color-danger)', medium: 'var(--color-warning)',
    compliant: 'var(--color-safe)', neutral: 'var(--color-border)',
  }
  const accent = borderColors[severity] ?? 'var(--color-border)'

  return (
    <div style={{
      background: 'var(--color-surface)',
      border: `1px solid var(--color-border)`,
      borderLeft: `4px solid ${accent}`,
      borderRadius: 10, padding: '16px 20px',
      display: 'flex', flexDirection: 'column', gap: 6,
      position: 'relative', minWidth: 180,
    }}>
      <div style={{ position: 'absolute', top: 12, right: 12 }}>
        <Badge severity={severity} />
      </div>
      <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginRight: 80 }}>
        {label}
      </div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 36, fontWeight: 500, color: 'var(--color-text-primary)', lineHeight: 1.1 }}>
        {value != null ? fixed(value, 3) : '—'}
      </div>
      {threshold && (
        <div style={{ fontSize: 11, color: 'var(--color-text-faint)', fontFamily: 'var(--font-mono)' }}>
          Legal threshold: {threshold}
        </div>
      )}
      <div style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.5, marginTop: 2 }}>
        {description}
      </div>
    </div>
  )
}

import type { Severity } from '../../lib/types'
import { severityLabel } from '../../lib/utils'

const MAP: Record<string, { bg: string; text: string; border: string }> = {
  high:      { bg: 'var(--color-danger-bg)',  text: 'var(--color-danger)',      border: 'var(--color-danger-border)' },
  medium:    { bg: 'var(--color-warning-bg)', text: 'var(--color-warning)',     border: 'var(--color-warning-border)' },
  compliant: { bg: 'var(--color-safe-bg)',    text: 'var(--color-safe)',        border: 'var(--color-safe-border)' },
  neutral:   { bg: 'var(--color-surface-2)',  text: 'var(--color-text-muted)', border: 'var(--color-border)' },
}

export default function Badge({ severity }: { severity: Severity | 'neutral' }) {
  const c = MAP[severity] ?? MAP.neutral
  return (
    <span style={{
      background: c.bg, color: c.text, border: `1px solid ${c.border}`,
      borderRadius: 999, padding: '2px 10px', fontSize: 11,
      fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase',
      fontFamily: 'var(--font-body)', whiteSpace: 'nowrap',
    }}>
      {severityLabel(severity)}
    </span>
  )
}

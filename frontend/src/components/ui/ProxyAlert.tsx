import Badge from '../ui/Badge'
import type { ProxyFinding } from '../../lib/types'
import { pct, proxyTypeLabel } from '../../lib/utils'

interface Props { finding: ProxyFinding }

const BORDER: Record<string, string> = {
  high: 'var(--color-danger)', medium: 'var(--color-warning)', compliant: 'var(--color-safe)',
}
const BG: Record<string, string> = {
  high: 'var(--color-danger-bg)', medium: 'var(--color-warning-bg)', compliant: 'var(--color-safe-bg)',
}

export default function ProxyAlert({ finding }: Props) {
  const accent = BORDER[finding.severity] ?? 'var(--color-border)'
  const bg     = BG[finding.severity]    ?? 'var(--color-surface)'
  return (
    <div style={{
      background: bg, borderLeft: `6px solid ${accent}`,
      borderRadius: '0 10px 10px 0', padding: '16px 20px',
      display: 'flex', gap: 16, alignItems: 'flex-start',
    }}>
      {/* Icon */}
      <div style={{ color: accent, marginTop: 2, flexShrink: 0 }}>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 3L2 19h20L12 3z"/><line x1="12" y1="9" x2="12" y2="13"/><circle cx="12" cy="17" r="0.5" fill="currentColor"/>
        </svg>
      </div>
      {/* Content */}
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
          <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--color-text-primary)' }}>
            {finding.column}
          </span>
          <Badge severity={finding.severity} />
          <span style={{
            fontSize: 11, fontWeight: 500, color: accent,
            background: 'rgba(0,0,0,0.05)', borderRadius: 4, padding: '2px 7px',
          }}>
            {proxyTypeLabel(finding.proxy_type)}
          </span>
        </div>
        <div style={{ fontSize: 13, color: 'var(--color-text-primary)', marginBottom: 6, lineHeight: 1.6 }}>
          <strong>{finding.affected_group}</strong>: {pct(finding.affected_hire_rate)} hire rate
          {' vs '}
          <strong>{finding.comparison_group}</strong>: {pct(finding.comparison_hire_rate)} hire rate
          {' '}(n={finding.sample_size_affected})
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 8 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 28, fontWeight: 500, color: accent }}>
            {finding.disparity_ratio}×
          </span>
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>disparity ratio</span>
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontStyle: 'italic', lineHeight: 1.5 }}>
          {finding.legal_note}
        </div>
      </div>
    </div>
  )
}

import ProxyAlert from '../ui/ProxyAlert'
import type { ProxyFinding } from '../../lib/types'

interface Props { findings: ProxyFinding[] }

export default function ProxyPanel({ findings }: Props) {
  if (!findings.length) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 24px', color: 'var(--color-text-muted)' }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>✅</div>
        <div style={{ fontSize: 15, fontWeight: 600 }}>No proxy discrimination patterns detected.</div>
        <div style={{ fontSize: 13, marginTop: 6 }}>The selected columns show no statistically significant bias signals.</div>
      </div>
    )
  }

  const highCount = findings.filter(f => f.severity === 'high').length
  const midCount  = findings.filter(f => f.severity === 'medium').length

  return (
    <div>
      <div style={{ marginBottom: 20, padding: '12px 16px', background: highCount ? 'var(--color-danger-bg)' : 'var(--color-warning-bg)', borderRadius: 8, border: `1px solid ${highCount ? 'var(--color-danger-border)' : 'var(--color-warning-border)'}` }}>
        <span style={{ fontWeight: 700, fontSize: 14, color: highCount ? 'var(--color-danger)' : 'var(--color-warning)' }}>
          {findings.length} proxy finding{findings.length > 1 ? 's' : ''} detected
        </span>
        <span style={{ fontSize: 13, color: 'var(--color-text-muted)', marginLeft: 12 }}>
          {highCount > 0 && `${highCount} HIGH RISK`}{highCount > 0 && midCount > 0 && ', '}{midCount > 0 && `${midCount} MEDIUM`}
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {findings.map(f => <ProxyAlert key={f.id} finding={f} />)}
      </div>
    </div>
  )
}

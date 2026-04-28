import ProxyPanel from '../components/audit/ProxyPanel'
import MetricsPanel from '../components/audit/MetricsPanel'
import MitigationToggle from '../components/audit/MitigationToggle'
import Spinner from '../components/ui/Spinner'
import type { AuditResponse } from '../lib/types'

interface Props {
  audit: AuditResponse | null
  loading: boolean
  error: string | null
  onBack: () => void
}

/** Explanation content for the reweighing mitigation technique */
const REWEIGHING_EXPLANATION = {
  what: 'Reweighing is a pre-processing fairness technique that adjusts the importance (weight) of individual data points to reduce bias without modifying the data itself.',
  how: 'For each group, we compute: weight = overall_selection_rate / group_selection_rate. This gives disadvantaged groups higher weights and advantaged groups lower weights, equalizing effective selection rates.',
  why: 'Unlike post-hoc fixes, reweighing addresses the root cause — systemic over/under-representation — making it the gold standard recommended by IBM AIF360 and Fairlearn.',
  legal: 'Reweighing is consistent with DPDP Act Section 4(1)(b) which requires automated decision systems to not discriminate. It demonstrates proactive bias mitigation as recommended by India\'s proposed AI governance framework.',
}

export default function AuditPage({ audit, loading, error, onBack }: Props) {
  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20, padding: '60px 0' }} role="status" aria-label="Running bias audit">
      <Spinner size={52} />
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 6 }}>Running bias audit…</div>
        <div style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>Detecting proxy patterns · Computing fairness metrics · Generating AI narrative</div>
      </div>
    </div>
  )

  if (!audit) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 40 }}>
      {/* Back button */}
      <button onClick={onBack} style={{
        padding: '6px 14px', fontSize: 12, fontWeight: 600, borderRadius: 6,
        border: '1.5px solid var(--color-border)', background: 'var(--color-surface)',
        color: 'var(--color-text-muted)', cursor: 'pointer', fontFamily: 'var(--font-body)',
        alignSelf: 'flex-start', transition: 'all 0.15s',
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--color-primary)'; e.currentTarget.style.color = 'var(--color-primary)' }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.color = 'var(--color-text-muted)' }}
      >
        ← Back to Inspect
      </button>

      <div>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 28, color: 'var(--color-text-primary)', margin: '0 0 6px' }}>
          Proxy Discrimination Findings
        </h1>
        <p style={{ fontSize: 14, color: 'var(--color-text-muted)', margin: 0, lineHeight: 1.6 }}>
          Columns acting as proxies for protected characteristics — caste, socioeconomic status, and class — detected via surname analysis, pin code SES mapping, and college tier classification.
        </p>
      </div>

      <section aria-label="Proxy detection results">
        <ProxyPanel findings={audit.proxy_findings} />
      </section>

      <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 36 }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 22, color: 'var(--color-text-primary)', margin: '0 0 20px' }}>
          Fairness Metrics
        </h2>
        <section aria-label="Bias metrics results">
          <MetricsPanel metrics={audit.bias_metrics} />
        </section>
      </div>

      {audit.mitigation_metrics?.method && (
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, color: 'var(--color-text-primary)', margin: '0 0 14px' }}>
            Mitigation Comparison
          </h2>
          <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 14, lineHeight: 1.6 }}>
            Impact of applying <strong>real statistical reweighing</strong> — a pre-processing technique that corrects for group imbalance by computing inverse-disparity weights per group.
          </p>
          <section aria-label="Before and after mitigation comparison">
            <MitigationToggle before={audit.bias_metrics} after={audit.mitigation_metrics} />
          </section>

          {/* Mitigation Explanation Panel — Section 9 */}
          <details style={{
            marginTop: 20, background: 'var(--color-surface)',
            border: '1px solid var(--color-border)', borderRadius: 10,
            overflow: 'hidden',
          }}>
            <summary style={{
              padding: '14px 18px', cursor: 'pointer',
              fontSize: 14, fontWeight: 600, color: 'var(--color-primary)',
              display: 'flex', alignItems: 'center', gap: 10,
              listStyle: 'none', userSelect: 'none',
            }}>
              <span style={{
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                width: 24, height: 24, borderRadius: '50%',
                background: 'var(--color-primary-light)', fontSize: 14,
              }}>🔬</span>
              How does reweighing work? — Technical explanation
            </summary>
            <div style={{ padding: '0 18px 18px', display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* What */}
              <div style={{ display: 'flex', gap: 12 }}>
                <span style={{
                  flexShrink: 0, width: 28, height: 28, borderRadius: 6,
                  background: 'var(--color-primary-light)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', fontSize: 14,
                  color: 'var(--color-primary)', fontWeight: 700,
                }}>W</span>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>What</div>
                  <div style={{ fontSize: 13, color: 'var(--color-text-primary)', lineHeight: 1.6 }}>{REWEIGHING_EXPLANATION.what}</div>
                </div>
              </div>

              {/* How */}
              <div style={{ display: 'flex', gap: 12 }}>
                <span style={{
                  flexShrink: 0, width: 28, height: 28, borderRadius: 6,
                  background: 'var(--color-safe-bg)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', fontSize: 14,
                  color: 'var(--color-safe)', fontWeight: 700,
                }}>H</span>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>How</div>
                  <div style={{ fontSize: 13, color: 'var(--color-text-primary)', lineHeight: 1.6 }}>{REWEIGHING_EXPLANATION.how}</div>
                  <code style={{
                    display: 'block', marginTop: 8, padding: '8px 12px',
                    background: 'var(--color-surface-2)', borderRadius: 6,
                    fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--color-text-primary)',
                    lineHeight: 1.5,
                  }}>
                    w(positive, group) = P(outcome=1) / P(outcome=1 | group)<br />
                    w(negative, group) = P(outcome=0) / P(outcome=0 | group)
                  </code>
                </div>
              </div>

              {/* Why */}
              <div style={{ display: 'flex', gap: 12 }}>
                <span style={{
                  flexShrink: 0, width: 28, height: 28, borderRadius: 6,
                  background: 'var(--color-warning-bg)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', fontSize: 14,
                  color: 'var(--color-warning)', fontWeight: 700,
                }}>Y</span>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>Why this method</div>
                  <div style={{ fontSize: 13, color: 'var(--color-text-primary)', lineHeight: 1.6 }}>{REWEIGHING_EXPLANATION.why}</div>
                </div>
              </div>

              {/* Legal */}
              <div style={{ display: 'flex', gap: 12 }}>
                <span style={{
                  flexShrink: 0, width: 28, height: 28, borderRadius: 6,
                  background: 'var(--color-danger-bg)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', fontSize: 14,
                  color: 'var(--color-danger)', fontWeight: 700,
                }}>⚖</span>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>Legal alignment</div>
                  <div style={{ fontSize: 13, color: 'var(--color-text-primary)', lineHeight: 1.6 }}>{REWEIGHING_EXPLANATION.legal}</div>
                </div>
              </div>
            </div>
          </details>
        </div>
      )}

      {error && (
        <div role="alert" style={{ padding: '12px 16px', background: 'var(--color-warning-bg)', border: '1px solid var(--color-warning-border)', borderRadius: 8, fontSize: 13, color: 'var(--color-warning)' }}>
          ⚠ Narrative generation: {error}
        </div>
      )}
    </div>
  )
}

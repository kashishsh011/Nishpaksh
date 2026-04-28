import type { NarrativeResponse } from '../../lib/types'

const STATUS_STYLE: Record<string, { color: string; bg: string; label: string }> = {
  non_compliant:   { color: 'var(--color-danger)',  bg: 'var(--color-danger-bg)',  label: 'NON-COMPLIANT' },
  at_risk:         { color: 'var(--color-warning)', bg: 'var(--color-warning-bg)', label: 'AT RISK' },
  review_required: { color: '#6366F1',              bg: '#EEF2FF',                 label: 'REVIEW REQUIRED' },
  compliant:       { color: 'var(--color-safe)',    bg: 'var(--color-safe-bg)',    label: 'COMPLIANT' },
}

interface Props { narrative: NarrativeResponse }

export default function NarrativeViewer({ narrative }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* Narrative sections */}
      {narrative.narrative_paragraphs.map((p, i) => (
        <div key={i} style={{ paddingBottom: 24, borderBottom: i < narrative.narrative_paragraphs.length - 1 ? '1px solid var(--color-border)' : 'none' }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 20, color: 'var(--color-primary)', margin: '0 0 12px' }}>
            {p.heading}
          </h3>
          <div style={{ fontSize: 14, lineHeight: 1.8, color: 'var(--color-text-primary)', whiteSpace: 'pre-wrap' }}>
            {p.text}
          </div>
        </div>
      ))}

      {/* DPDP Checklist */}
      {narrative.dpdp_checklist.length > 0 && (
        <div>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 18, color: 'var(--color-text-primary)', margin: '0 0 14px' }}>
            Legal Compliance Checklist
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {narrative.dpdp_checklist.map((item, i) => {
              const s = STATUS_STYLE[item.status] ?? STATUS_STYLE.review_required
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 14,
                  padding: '12px 16px', borderRadius: 8,
                  borderLeft: `4px solid ${s.color}`, background: s.bg,
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--color-text-primary)', marginBottom: 3 }}>{item.article}</div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.5 }}>{item.description}</div>
                  </div>
                  <span style={{ fontSize: 10, fontWeight: 700, color: s.color, background: 'rgba(255,255,255,0.7)', borderRadius: 4, padding: '3px 8px', whiteSpace: 'nowrap', letterSpacing: '0.04em' }}>
                    {s.label}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

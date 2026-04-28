import type { AuditStep } from '../../lib/types'

const STEPS: { key: AuditStep; label: string }[] = [
  { key: 'upload',  label: 'Upload' },
  { key: 'inspect', label: 'Inspect' },
  { key: 'audit',   label: 'Audit' },
  { key: 'report',  label: 'Report' },
]
const ORDER: AuditStep[] = ['upload', 'inspect', 'audit', 'report']

interface Props {
  current: AuditStep
  onStepClick?: (step: AuditStep) => void
}

export default function Stepper({ current, onStepClick }: Props) {
  const idx = ORDER.indexOf(current)
  return (
    <nav aria-label="Audit progress" style={{ display: 'flex', alignItems: 'flex-start', width: '100%' }}>
      {STEPS.map((step, i) => {
        const done   = i < idx
        const active = i === idx
        const canClick = done && onStepClick  // Can only click completed steps
        const clr    = done || active ? 'var(--color-primary)' : 'var(--color-border-strong)'
        const textClr = active ? 'var(--color-primary)' : done ? 'var(--color-text-muted)' : 'var(--color-text-faint)'
        return (
          <div key={step.key} style={{ display: 'flex', alignItems: 'flex-start', flex: i < STEPS.length - 1 ? 1 : 'none' }}>
            <div
              role={canClick ? 'button' : undefined}
              tabIndex={canClick ? 0 : undefined}
              aria-label={canClick ? `Go back to ${step.label}` : `Step ${i + 1}: ${step.label}`}
              aria-current={active ? 'step' : undefined}
              onClick={() => canClick && onStepClick(step.key)}
              onKeyDown={(e) => { if (canClick && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onStepClick(step.key) } }}
              style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                cursor: canClick ? 'pointer' : 'default',
              }}
            >
              <div style={{
                width: 34, height: 34, borderRadius: '50%',
                background: done ? 'var(--color-primary)' : active ? 'var(--color-primary-light)' : 'var(--color-surface-2)',
                border: `2px solid ${clr}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: done ? '#fff' : active ? 'var(--color-primary)' : 'var(--color-text-faint)',
                fontWeight: 700, fontSize: 13, transition: 'all 0.25s',
                boxShadow: active ? '0 0 0 4px var(--color-primary-light)' : 'none',
                transform: canClick ? 'scale(1)' : undefined,
              }}
              onMouseEnter={e => { if (canClick) e.currentTarget.style.transform = 'scale(1.12)' }}
              onMouseLeave={e => { if (canClick) e.currentTarget.style.transform = 'scale(1)' }}
              >
                {done ? '✓' : i + 1}
              </div>
              <span style={{ fontSize: 11, fontWeight: active ? 600 : 400, color: textClr, whiteSpace: 'nowrap', fontFamily: 'var(--font-body)' }}>
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div style={{
                flex: 1, height: 2, marginTop: 16,
                background: i < idx ? 'var(--color-primary)' : 'var(--color-border)',
                margin: '16px 8px 0',
                transition: 'background 0.3s',
              }} />
            )}
          </div>
        )
      })}
    </nav>
  )
}

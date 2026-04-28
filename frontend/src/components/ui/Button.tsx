import React from 'react'

interface Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost' | 'danger'
  loading?: boolean
}

export default function Button({ variant = 'primary', loading, children, disabled, style, ...rest }: Props) {
  const base: React.CSSProperties = {
    fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: 14,
    padding: '10px 24px', borderRadius: 8,
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    transition: 'all 0.15s', border: '1.5px solid transparent',
    display: 'inline-flex', alignItems: 'center', gap: 8,
    opacity: disabled || loading ? 0.6 : 1,
  }
  const variants: Record<string, React.CSSProperties> = {
    primary: { background: 'var(--color-primary)', color: '#fff', borderColor: 'var(--color-primary)' },
    ghost:   { background: 'transparent', color: 'var(--color-primary)', borderColor: 'var(--color-primary)' },
    danger:  { background: 'var(--color-danger)', color: '#fff', borderColor: 'var(--color-danger)' },
  }
  return (
    <button disabled={disabled || loading} style={{ ...base, ...variants[variant], ...style }} {...rest}>
      {loading && (
        <span style={{
          width: 15, height: 15, borderRadius: '50%',
          border: '2px solid rgba(255,255,255,0.35)',
          borderTopColor: '#fff',
          animation: 'spin 0.8s linear infinite',
          display: 'inline-block', flexShrink: 0,
        }} />
      )}
      {children}
    </button>
  )
}

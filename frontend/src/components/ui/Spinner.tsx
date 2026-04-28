export default function Spinner({ size = 32 }: { size?: number }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      border: `3px solid var(--color-primary-light)`,
      borderTopColor: 'var(--color-primary)',
      animation: 'spin 0.8s linear infinite',
      flexShrink: 0,
    }} />
  )
}

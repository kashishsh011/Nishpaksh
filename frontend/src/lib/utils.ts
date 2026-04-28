export function pct(n: number | null | undefined): string {
  if (n == null) return '—'
  return `${(n * 100).toFixed(1)}%`
}

export function fixed(n: number | null | undefined, decimals = 2): string {
  if (n == null) return '—'
  return n.toFixed(decimals)
}

export function severityLabel(s: string): string {
  return { high: 'HIGH RISK', medium: 'MEDIUM', compliant: 'COMPLIANT' }[s] ?? s.toUpperCase()
}

export function proxyTypeLabel(t: string): string {
  return { caste: 'Caste Proxy', socioeconomic: 'SES Proxy', class: 'Class Proxy' }[t] ?? t
}

export function clsx(...classes: (string | false | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ')
}

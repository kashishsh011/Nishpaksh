import { BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer, Cell, LabelList } from 'recharts'
import type { ColumnDistribution } from '../../lib/types'

interface Props { distributions: ColumnDistribution[]; overallRate: number }

function rateColor(rate: number, overall: number): string {
  const r = rate / Math.max(overall, 0.01)
  if (r < 0.6) return '#DC2626'
  if (r < 0.85) return '#D97706'
  return '#0D9488'
}

function DistChart({ dist, overall }: { dist: ColumnDistribution; overall: number }) {
  const data = dist.distribution.map(d => ({ name: d.label, rate: d.hire_rate, count: d.count }))
  // Skip rendering if there's no data to display
  if (!data.length) return null
  const height = Math.max(140, 50 + data.length * 40)
  return (
    <div style={{
      background: 'var(--color-surface)', border: `1px solid ${dist.skew_flag ? 'var(--color-warning-border)' : 'var(--color-border)'}`,
      borderRadius: 10, padding: '16px 20px', marginBottom: 16,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--color-text-primary)' }}>{dist.column}</span>
        {dist.skew_flag && (
          <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-warning)', background: 'var(--color-warning-bg)', border: '1px solid var(--color-warning-border)', borderRadius: 999, padding: '2px 10px', letterSpacing: '0.04em' }}>
            SKEW DETECTED
          </span>
        )}
      </div>
      {dist.skew_reason && (
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 10, fontStyle: 'italic' }}>{dist.skew_reason}</div>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} layout="vertical" margin={{ left: 0, right: 40, top: 4, bottom: 4 }}>
          <XAxis type="number" domain={[0, 1]} tickFormatter={v => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} />
          <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 12, fill: 'var(--color-text-primary)' }} />
          <Tooltip formatter={(v: any) => `${(Number(v) * 100).toFixed(1)}%`} />
          <ReferenceLine x={overall} stroke="var(--color-primary)" strokeDasharray="4 3" label={{ value: 'Overall', position: 'top', fontSize: 10, fill: 'var(--color-primary)' }} />
          <Bar dataKey="rate" radius={[0, 4, 4, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={rateColor(entry.rate, overall)} />
            ))}
            <LabelList dataKey="count" position="right" formatter={(v: any) => `n=${v}`} style={{ fontSize: 10, fill: 'var(--color-text-muted)' }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function DistributionGrid({ distributions, overallRate }: Props) {
  if (!distributions.length) return (
    <div style={{ color: 'var(--color-text-muted)', fontSize: 14, padding: 24, textAlign: 'center' }}>
      No column distributions available.
    </div>
  )
  return (
    <div>
      {distributions.map(d => <DistChart key={d.column} dist={d} overall={overallRate} />)}
    </div>
  )
}

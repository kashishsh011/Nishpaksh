import Button from '../ui/Button'

interface Props { onDownload: () => void; loading: boolean }

export default function DownloadButton({ onDownload, loading }: Props) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 16, padding: '20px 24px',
      background: 'var(--color-primary-light)', borderRadius: 12,
      border: '1px solid var(--color-primary)', flexWrap: 'wrap',
    }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--color-primary)', marginBottom: 2 }}>
          Audit Report Ready
        </div>
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
          PDF includes proxy findings, bias metrics, legal narrative, and DPDP checklist
        </div>
      </div>
      <Button variant="primary" loading={loading} onClick={onDownload} style={{ padding: '12px 28px', fontSize: 14 }}>
        ⬇ Download PDF Report
      </Button>
    </div>
  )
}

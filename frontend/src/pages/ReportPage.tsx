import NarrativeViewer from '../components/report/NarrativeViewer'
import DownloadButton from '../components/report/DownloadButton'
import type { NarrativeResponse } from '../lib/types'

interface Props {
  narrative: NarrativeResponse | null
  onDownload: () => void
  loading: boolean
  error: string | null
  onReset: () => void
}

export default function ReportPage({ narrative, onDownload, loading, error, onReset }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      <div>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 28, color: 'var(--color-text-primary)', margin: '0 0 8px' }}>
          Audit Report
        </h1>
        <p style={{ fontSize: 14, color: 'var(--color-text-muted)', margin: 0, lineHeight: 1.6 }}>
          Plain-language findings aligned to India's DPDP Act and Articles 14, 15, and 16 of the Constitution.
        </p>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', background: 'var(--color-warning-bg)', border: '1px solid var(--color-warning-border)', borderRadius: 8, fontSize: 13, color: 'var(--color-warning)' }}>
          ⚠ AI narrative unavailable: {error}. You can still download the PDF with metrics only.
        </div>
      )}

      <DownloadButton onDownload={onDownload} loading={loading} />

      {narrative && <NarrativeViewer narrative={narrative} />}

      <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 24, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <button onClick={onReset} style={{
          padding: '10px 20px', fontSize: 13, fontWeight: 600, borderRadius: 8,
          border: '1.5px solid var(--color-border)', background: 'var(--color-surface)',
          color: 'var(--color-text-muted)', cursor: 'pointer', fontFamily: 'var(--font-body)',
        }}>
          ← Start New Audit
        </button>
      </div>
    </div>
  )
}

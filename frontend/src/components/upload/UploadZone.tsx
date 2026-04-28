import { useRef, useState } from 'react'
import Button from '../ui/Button'

interface Props { onFile: (f: File) => void; loading: boolean }

export default function UploadZone({ onFile, loading }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [fileName, setFileName] = useState<string | null>(null)

  const handle = (file: File) => {
    if (!file.name.endsWith('.csv')) { alert('Please upload a .csv file'); return }
    setFileName(file.name)
    onFile(file)
  }

  return (
    <div
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handle(f) }}
      onClick={() => inputRef.current?.click()}
      style={{
        border: `2px dashed ${dragging ? 'var(--color-primary)' : 'var(--color-border-strong)'}`,
        borderRadius: 16, padding: '56px 32px', textAlign: 'center',
        background: dragging ? 'var(--color-primary-light)' : 'var(--color-surface)',
        cursor: 'pointer', transition: 'all 0.2s',
      }}
    >
      <input ref={inputRef} type="file" accept=".csv" style={{ display: 'none' }}
        onChange={e => { const f = e.target.files?.[0]; if (f) handle(f) }} />

      <div style={{ fontSize: 48, marginBottom: 16 }}>📋</div>
      <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 8 }}>
        {fileName ? fileName : 'Drop your hiring CSV here'}
      </div>
      <div style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 24 }}>
        {fileName ? 'Uploading…' : 'or click to browse — CSV files only, max 10 MB'}
      </div>
      <Button variant="primary" loading={loading} onClick={e => e.stopPropagation()}>
        {loading ? 'Parsing…' : 'Select File'}
      </Button>
    </div>
  )
}

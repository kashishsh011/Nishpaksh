import UploadZone from '../components/upload/UploadZone'
import ColumnMapper from '../components/upload/ColumnMapper'
import type { ColumnMapping, UploadResponse } from '../lib/types'

interface Props {
  onFile: (f: File) => void
  uploadResponse: UploadResponse | null
  onConfirm: (m: ColumnMapping, company: string) => void
  loading: boolean
  error: string | null
}

/** SDG badges for the Solution Challenge */
const SDG_BADGES = [
  { num: 8, title: 'Decent Work & Economic Growth', color: '#A21942', icon: '📈' },
  { num: 10, title: 'Reduced Inequalities', color: '#DD1367', icon: '🤝' },
  { num: 16, title: 'Peace, Justice & Strong Institutions', color: '#00689D', icon: '⚖️' },
]

export default function UploadPage({ onFile, uploadResponse, onConfirm, loading, error }: Props) {
  /** Demo mode — generate and upload a synthetic CSV */
  const handleDemo = async () => {
    const headers = ['candidate_name', 'gender', 'college', 'pincode', 'skill_score', 'outcome']
    const names = [
      ['Rahul Sharma', 'Male', 'IIT Delhi', '110001', '88', 'hired'],
      ['Priya Iyer', 'Female', 'IIT Bombay', '400076', '91', 'hired'],
      ['Amit Yadav', 'Male', 'Pune University', '411001', '72', 'not_hired'],
      ['Sneha Gupta', 'Female', 'Delhi University', '110007', '65', 'not_hired'],
      ['Vikram Singh', 'Male', 'IIT Madras', '600036', '90', 'hired'],
      ['Anjali Patel', 'Female', 'Gujarat University', '380009', '70', 'not_hired'],
      ['Rajesh Chauhan', 'Male', 'State College', '452001', '55', 'not_hired'],
      ['Deepa Nair', 'Female', 'NIT Trichy', '620015', '82', 'hired'],
      ['Suresh Reddy', 'Male', 'BITS Pilani', '333031', '85', 'hired'],
      ['Kavita Das', 'Female', 'Calcutta University', '700073', '60', 'not_hired'],
      ['Mohan Jha', 'Male', 'BHU', '221005', '78', 'hired'],
      ['Ritu Bansal', 'Female', 'SRCC', '110007', '83', 'hired'],
      ['Arjun Mishra', 'Male', 'Patna University', '800001', '58', 'not_hired'],
      ['Pooja Agarwal', 'Female', 'IIM Ahmedabad', '380015', '95', 'hired'],
      ['Sanjay Paswan', 'Male', 'Regional College', '843301', '62', 'not_hired'],
      ['Anita Kumari', 'Female', 'IGNOU', '110068', '50', 'not_hired'],
      ['Karan Mehta', 'Male', 'NIT Surathkal', '575025', '81', 'hired'],
      ['Divya Joshi', 'Female', 'Symbiosis', '411014', '74', 'not_hired'],
      ['Ramesh Thakur', 'Male', 'HP University', '171005', '67', 'not_hired'],
      ['Neha Verma', 'Female', 'Christ University', '560029', '79', 'hired'],
    ]
    const csv = [headers.join(','), ...names.map(r => r.join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const file = new File([blob], 'nishpaksh_demo_data.csv', { type: 'text/csv' })
    onFile(file)
  }

  return (
    <div style={{ maxWidth: 680, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 32, color: 'var(--color-text-primary)', margin: '0 0 10px' }}>
          Upload Hiring Data
        </h1>
        <p style={{ fontSize: 14, color: 'var(--color-text-muted)', lineHeight: 1.6, margin: 0 }}>
          Upload a CSV file containing your hiring pipeline data. Nishpaksh will detect India-specific proxy discrimination patterns — caste via surnames, socioeconomic status via pin codes, and class via college tier.
        </p>
      </div>

      {/* SDG Alignment Badges */}
      <div style={{
        display: 'flex', gap: 10, marginBottom: 24, flexWrap: 'wrap',
      }} role="list" aria-label="UN Sustainable Development Goals alignment">
        {SDG_BADGES.map(sdg => (
          <div key={sdg.num} role="listitem" style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '8px 14px', borderRadius: 8,
            background: `${sdg.color}12`, border: `1px solid ${sdg.color}30`,
            fontSize: 12, fontWeight: 600, color: sdg.color,
            transition: 'transform 0.15s',
            cursor: 'default',
          }}
          onMouseEnter={e => (e.currentTarget.style.transform = 'scale(1.04)')}
          onMouseLeave={e => (e.currentTarget.style.transform = 'scale(1)')}
          >
            <span style={{ fontSize: 16 }}>{sdg.icon}</span>
            <span>SDG {sdg.num}</span>
            <span style={{ fontWeight: 400, opacity: 0.85 }}>{sdg.title}</span>
          </div>
        ))}
      </div>

      {error && (
        <div role="alert" style={{ padding: '14px 18px', background: 'var(--color-danger-bg)', border: '1px solid var(--color-danger-border)', borderRadius: 10, marginBottom: 20, fontSize: 13, color: 'var(--color-danger)', fontWeight: 500, lineHeight: 1.6 }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
            <span style={{ fontSize: 18, lineHeight: 1 }}>⚠</span>
            <div>
              {error.includes('Cannot connect to backend') ? (
                <>
                  <div style={{ fontWeight: 700, marginBottom: 4 }}>Backend Server Unreachable</div>
                  <div style={{ fontSize: 12, opacity: 0.85 }}>
                    The API server at <code style={{ fontSize: 11, padding: '1px 5px', background: 'rgba(0,0,0,0.06)', borderRadius: 3 }}>localhost:8000</code> is not responding. Start it with:
                  </div>
                  <code style={{ display: 'block', marginTop: 6, fontSize: 11, padding: '6px 10px', background: 'rgba(0,0,0,0.06)', borderRadius: 5, fontFamily: 'var(--font-mono)' }}>
                    cd backend && python -m uvicorn main:app --port 8000
                  </code>
                </>
              ) : (
                <div>{error}</div>
              )}
            </div>
          </div>
        </div>
      )}

      {!uploadResponse ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <UploadZone onFile={onFile} loading={loading} />

          {/* Demo mode button */}
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 12, color: 'var(--color-text-faint)', marginBottom: 8 }}>
              or try with sample data
            </div>
            <button
              id="demo-mode-button"
              onClick={handleDemo}
              disabled={loading}
              style={{
                padding: '10px 24px', fontSize: 13, fontWeight: 600,
                borderRadius: 8, cursor: 'pointer',
                background: 'linear-gradient(135deg, var(--color-primary-light), #e0e7ff)',
                border: '1.5px solid var(--color-primary)',
                color: 'var(--color-primary)',
                fontFamily: 'var(--font-body)',
                transition: 'all 0.2s',
                boxShadow: '0 1px 4px rgba(55,48,163,0.12)',
              }}
              onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = '0 4px 12px rgba(55,48,163,0.2)' }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 1px 4px rgba(55,48,163,0.12)' }}
            >
              🎯 Try Demo Dataset (20 candidates)
            </button>
          </div>

          {/* Privacy notice */}
          <div role="note" style={{
            padding: '12px 16px', background: 'var(--color-surface-2)',
            borderRadius: 8, fontSize: 11, color: 'var(--color-text-muted)',
            lineHeight: 1.7, borderLeft: '3px solid var(--color-primary)',
          }}>
            <strong style={{ fontSize: 12 }}>🔒 Privacy Notice</strong>
            <br />
            Your data is processed <strong>entirely in-memory</strong> on the server and is never persisted to disk or sent to external services.
            AI narrative generation uses Google Gemini with your API key only — no data is retained.
            Aligned to DPDP Act Section 4(1) data processing principles.
          </div>
        </div>
      ) : (
        <div>
          <div role="status" style={{ padding: '12px 16px', background: 'var(--color-safe-bg)', border: '1px solid var(--color-safe-border)', borderRadius: 8, marginBottom: 24, fontSize: 13, color: 'var(--color-safe)', fontWeight: 600 }}>
            ✓ {uploadResponse.row_count.toLocaleString()} rows · {uploadResponse.column_count} columns detected
          </div>
          {/* Preview table */}
          {uploadResponse.preview_rows.length > 0 && (
            <div style={{ marginBottom: 28, overflowX: 'auto' }}>
              <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: 8 }}>
                Data Preview (first 5 rows)
              </div>
              <table role="table" aria-label="Preview of uploaded data" style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, fontFamily: 'var(--font-mono)' }}>
                <thead>
                  <tr>
                    {Object.keys(uploadResponse.preview_rows[0]).map(k => (
                      <th key={k} scope="col" style={{ padding: '6px 10px', background: 'var(--color-surface-2)', border: '1px solid var(--color-border)', textAlign: 'left', fontWeight: 600, color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>{k}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {uploadResponse.preview_rows.map((row, i) => (
                    <tr key={i} style={{ background: i % 2 === 0 ? 'var(--color-surface)' : 'var(--color-surface-2)' }}>
                      {Object.values(row).map((v, j) => (
                        <td key={j} style={{ padding: '5px 10px', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)', maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {String(v)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 16 }}>
            Map Your Columns
          </div>
          <ColumnMapper upload={uploadResponse} onConfirm={onConfirm} loading={loading} />
        </div>
      )}
    </div>
  )
}

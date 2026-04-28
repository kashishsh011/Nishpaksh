import { useAudit } from './hooks/useAudit'
import Stepper from './components/ui/Stepper'
import UploadPage from './pages/UploadPage'
import InspectPage from './pages/InspectPage'
import AuditPage from './pages/AuditPage'
import ReportPage from './pages/ReportPage'

export default function App() {
  const { state, backendOnline, uploadFile, runInspect, runAudit, downloadPdf, reset, goTo, retryConnection } = useAudit()

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-canvas)' }}>
      {/* Backend connection banner */}
      {backendOnline === false && (
        <div style={{
          background: 'linear-gradient(90deg, #7f1d1d, #991b1b)',
          color: '#fecaca',
          padding: '10px 32px',
          fontSize: 13,
          fontWeight: 500,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 16,
          fontFamily: 'var(--font-body)',
        }}>
          <span style={{ fontSize: 16 }}>⚠</span>
          <span>
            <strong>Backend server is offline.</strong>{' '}
            Start it with: <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 8px', borderRadius: 4, fontSize: 12, fontFamily: 'var(--font-mono)' }}>
              cd backend &amp;&amp; python -m uvicorn main:app --port 8000
            </code>
          </span>
          <button
            onClick={retryConnection}
            style={{
              background: 'rgba(255,255,255,0.15)',
              border: '1px solid rgba(255,255,255,0.3)',
              color: '#fecaca',
              padding: '4px 14px',
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              flexShrink: 0,
            }}
          >
            Retry
          </button>
        </div>
      )}

      {backendOnline === null && (
        <div style={{
          background: 'linear-gradient(90deg, #78350f, #92400e)',
          color: '#fde68a',
          padding: '8px 32px',
          fontSize: 12,
          fontWeight: 500,
          textAlign: 'center',
          fontFamily: 'var(--font-body)',
        }}>
          Checking backend connection…
        </div>
      )}

      {/* Top nav */}
      <header role="banner" aria-label="Nishpaksh navigation" style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(247,246,241,0.92)', backdropFilter: 'blur(12px)',
        borderBottom: '1px solid var(--color-border)',
        padding: '0 32px',
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', alignItems: 'center', gap: 24, height: 60 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexShrink: 0 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 20, color: 'var(--color-primary)', letterSpacing: '-0.01em' }}>
              Nishpaksh
            </span>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--color-text-faint)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              निष्पक्ष
            </span>
          </div>
          <div style={{ flex: 1, maxWidth: 520 }}>
            <Stepper current={state.step} onStepClick={goTo} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
            {backendOnline === true && (
              <span style={{
                width: 8, height: 8, borderRadius: '50%',
                background: '#22c55e', boxShadow: '0 0 6px rgba(34,197,94,0.5)',
                display: 'inline-block',
              }} title="Backend connected" />
            )}
            {backendOnline === false && (
              <span style={{
                width: 8, height: 8, borderRadius: '50%',
                background: '#ef4444', boxShadow: '0 0 6px rgba(239,68,68,0.5)',
                display: 'inline-block',
              }} title="Backend offline" />
            )}
            <span style={{ fontSize: 11, color: 'var(--color-text-faint)' }}>
              India's Hiring Bias Auditor
            </span>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main id="main-content" role="main" aria-label="Audit workflow" style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 32px 80px' }}>
        {state.step === 'upload' && (
          <UploadPage
            onFile={uploadFile}
            uploadResponse={state.upload_response}
            onConfirm={runInspect}
            loading={state.loading}
            error={state.error}
          />
        )}

        {state.step === 'inspect' && (
          <InspectPage
            inspect={state.inspect_response}
            loading={state.loading}
            error={state.error}
            onContinue={runAudit}
            onBack={() => goTo('upload')}
          />
        )}

        {state.step === 'audit' && (
          <AuditPage
            audit={state.audit_response}
            loading={state.loading}
            error={state.error}
            onBack={() => goTo('inspect')}
          />
        )}

        {state.step === 'report' && (
          <ReportPage
            narrative={state.narrative_response}
            onDownload={downloadPdf}
            loading={state.loading}
            error={state.error}
            onReset={reset}
          />
        )}
      </main>
    </div>
  )
}

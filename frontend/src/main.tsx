import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import LegalPage from './legal/LegalPage.tsx'
import { aplicarMetadatosSeo } from './seo/routeMetadata.ts'
import { trackPageView } from './analytics.ts'
import { initializePostHog } from './posthog.ts'
import { PostHogProvider } from '@posthog/react'

const posthogClient = initializePostHog()

const pathname = window.location.pathname
const legalKind = pathname === '/terminos'
  ? 'terminos'
  : pathname === '/privacidad'
    ? 'privacidad'
    : null

if (legalKind) {
  aplicarMetadatosSeo(pathname)
  trackPageView(pathname)
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <PostHogProvider client={posthogClient}>
      {legalKind ? <LegalPage kind={legalKind} /> : <App />}
    </PostHogProvider>
  </StrictMode>,
)

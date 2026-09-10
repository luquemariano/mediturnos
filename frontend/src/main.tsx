import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import LegalPage from './legal/LegalPage.tsx'
import { aplicarMetadatosSeo } from './seo/routeMetadata.ts'

const pathname = window.location.pathname
const legalKind = pathname === '/terminos'
  ? 'terminos'
  : pathname === '/privacidad'
    ? 'privacidad'
    : null

if (legalKind) aplicarMetadatosSeo(pathname)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {legalKind ? <LegalPage kind={legalKind} /> : <App />}
  </StrictMode>,
)

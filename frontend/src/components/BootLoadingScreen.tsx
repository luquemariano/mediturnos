import "./BootLoadingScreen.css";

export type BootStep = {
  id: string;
  label: string;
  status: "pending" | "loading" | "complete";
};

type Props = {
  steps: BootStep[];
  prolonged: boolean;
  error?: string;
  onRetry?: () => void;
};

export default function BootLoadingScreen({ steps, prolonged, error, onRetry }: Props) {
  return (
    <main className="boot-loading" aria-live="polite">
      <section className="boot-loading-card" aria-label="Preparando tu espacio">
        <div className="boot-loading-brand">Turnelia</div>
        <h1>{error ? "No pudimos completar el ingreso." : "Preparando tu espacio..."}</h1>
        {error ? <p>{error}</p> : prolonged && <p>Estamos tardando un poco más de lo habitual. Turnelia continúa preparando tu espacio.</p>}
        {!error && <ol className="boot-loading-steps">
          {steps.map((step) => (
            <li key={step.id} className={`boot-loading-step boot-loading-step-${step.status}`}>
              <span aria-hidden="true">{step.status === "complete" ? "✓" : step.status === "loading" ? <i /> : ""}</span>
              <strong>{step.label}</strong>
            </li>
          ))}
        </ol>}
        {error && onRetry && <button type="button" onClick={onRetry}>Intentar nuevamente</button>}
      </section>
    </main>
  );
}

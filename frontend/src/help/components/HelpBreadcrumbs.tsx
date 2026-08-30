type Props = { title?: string; onHome: () => void };
export default function HelpBreadcrumbs({ title, onHome }: Props) { return <nav className="help-breadcrumbs" aria-label="Migas de pan"><button type="button" onClick={onHome}>Centro de Ayuda</button>{title && <><span aria-hidden="true">›</span><span aria-current="page">{title}</span></>}</nav>; }

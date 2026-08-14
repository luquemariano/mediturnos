type AuthBrandProps = {
  subtitulo?: string;
};

export default function AuthBrand({ subtitulo }: AuthBrandProps) {
  return <div className="marca autenticacion-marca">
    <img
      className="marca-icono"
      src="/brand/mediturnos-symbol.svg"
      alt=""
      aria-hidden="true"
    />
    <div>
      <h1>MediTurnos</h1>
      {subtitulo && <p>{subtitulo}</p>}
    </div>
  </div>;
}

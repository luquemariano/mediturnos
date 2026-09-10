import "./LegalPage.css";

type LegalKind = "terminos" | "privacidad";

type Section = {
  title: string;
  paragraphs?: string[];
  bullets?: string[];
};

const termsSections: Section[] = [
  {
    title: "1. Sobre Turnelia",
    paragraphs: [
      "Turnelia es una plataforma tecnológica de gestión que proporciona herramientas para organizar agendas, administrar pacientes, registrar turnos, gestionar disponibilidad, enviar recordatorios y utilizar otras funcionalidades vinculadas con la actividad profesional.",
      "Turnelia actúa como proveedor de la herramienta tecnológica y no presta servicios médicos, psicológicos, psicopedagógicos ni otros servicios profesionales de salud, ni interviene en las decisiones, diagnósticos, tratamientos o prestaciones realizadas por los profesionales que utilizan la plataforma. Cada profesional es responsable del ejercicio de su actividad y del cumplimiento de las normas profesionales que resulten aplicables.",
    ],
  },
  {
    title: "2. Registro y cuenta de usuario",
    paragraphs: ["Para utilizar determinadas funcionalidades de Turnelia es necesario crear una cuenta. El usuario se compromete a proporcionar información verdadera, actualizada y completa durante el registro y a mantenerla actualizada mientras utilice el servicio."],
    bullets: [
      "Mantener la confidencialidad de sus credenciales.",
      "Evitar el acceso no autorizado a su cuenta.",
      "Informar a Turnelia ante cualquier sospecha de uso indebido.",
      "Mantener actualizada su dirección de correo electrónico.",
    ],
  },
  {
    title: "3. Uso de la plataforma",
    paragraphs: ["El usuario se compromete a utilizar Turnelia exclusivamente para fines lícitos y vinculados con las funcionalidades ofrecidas por el servicio."],
    bullets: [
      "No realizar actividades ilegales ni acceder a cuentas o información de terceros sin autorización.",
      "No introducir código malicioso ni intentar alterar el funcionamiento del sistema.",
      "No realizar ataques o pruebas de intrusión no autorizizadas ni acciones destinadas a comprometer la seguridad de Turnelia.",
      "No cargar o tratar información respecto de la cual el usuario no posea autorización o fundamento suficiente para hacerlo.",
    ],
  },
  {
    title: "4. Pacientes y datos cargados por los profesionales",
    paragraphs: [
      "Los profesionales pueden registrar información relacionada con sus pacientes para utilizar las herramientas de gestión disponibles en Turnelia. El profesional es responsable de determinar qué información incorpora a la plataforma y de contar con las autorizaciones o fundamentos necesarios para su tratamiento de acuerdo con la normativa aplicable.",
      "La información de pacientes cargada por un profesional no será utilizada por Turnelia como base de datos comercial propia ni para realizar publicidad directa a dichos pacientes, salvo consentimiento específico cuando legalmente corresponda. El tratamiento de datos personales se regula adicionalmente en nuestra Política de Privacidad.",
    ],
  },
  {
    title: "5. Agenda, disponibilidad y turnos",
    paragraphs: ["Turnelia permite definir franjas horarias de disponibilidad, crear y administrar turnos, reprogramarlos, cancelarlos y consultar diferentes vistas de agenda. El profesional es responsable de mantener actualizada su disponibilidad. Turnelia facilita la gestión tecnológica de los turnos, pero no garantiza la asistencia del paciente ni responde por cancelaciones, ausencias, retrasos o modificaciones realizadas entre profesionales y pacientes."],
  },
  {
    title: "6. Información y evolución clínica",
    paragraphs: ["Cuando la funcionalidad se encuentre habilitada, determinados usuarios podrán registrar información vinculada con la atención o evolución de un paciente. El contenido de dichos registros es responsabilidad del profesional que los incorpora. Turnelia no interpreta, modifica ni valida desde el punto de vista médico o profesional el contenido registrado, ni reemplaza los registros o requisitos documentales que puedan resultar exigibles según la profesión, especialidad o jurisdicción correspondiente."],
  },
  {
    title: "7. Recordatorios y comunicaciones",
    paragraphs: ["Turnelia puede enviar comunicaciones relacionadas con el funcionamiento del servicio, tales como verificaciones de cuenta, recuperación de contraseña, avisos relacionados con turnos, recordatorios, comunicaciones administrativas e información de suscripciones. La entrega efectiva puede depender de proveedores externos, conectividad y configuraciones del destinatario."],
  },
  {
    title: "8. Planes y suscripciones",
    paragraphs: ["Turnelia puede ofrecer funcionalidades gratuitas, períodos promocionales y planes pagos. Las características, precios y condiciones correspondientes a cada plan serán informadas antes de la contratación. Cuando exista una suscripción periódica, el precio, moneda, frecuencia de cobro y demás condiciones relevantes serán indicados antes de confirmar la operación."],
  },
  {
    title: "9. Pagos",
    paragraphs: ["Los pagos electrónicos podrán ser procesados mediante proveedores externos, como Mercado Pago. Turnelia no almacena los datos completos de tarjetas de crédito o débito cuando la operación es procesada directamente por el proveedor de pagos. La utilización de esos servicios también puede estar sujeta a los términos y políticas del proveedor correspondiente."],
  },
  {
    title: "10. Cancelación de la suscripción",
    paragraphs: ["El usuario podrá solicitar la cancelación de su suscripción mediante los mecanismos electrónicos habilitados por Turnelia. La cancelación no eliminará automáticamente la cuenta ni la información almacenada cuando existan motivos legítimos o requisitos legales que justifiquen su conservación."],
  },
  {
    title: "11. Disponibilidad y mantenimiento",
    paragraphs: ["Turnelia procura mantener la plataforma operativa y disponible de forma continua. Sin embargo, pueden producirse interrupciones temporales por mantenimiento, actualizaciones, fallos de infraestructura, conectividad, servicios de terceros, incidentes de seguridad o causas de fuerza mayor. Cuando sea razonablemente posible, Turnelia procurará reducir su impacto y duración."],
  },
  {
    title: "12. Seguridad",
    paragraphs: ["Turnelia implementa medidas técnicas y organizativas destinadas a proteger la información almacenada. Ningún sistema conectado a Internet puede garantizar seguridad absoluta. Los usuarios también son responsables de utilizar contraseñas seguras, proteger sus dispositivos y evitar compartir sus credenciales."],
  },
  {
    title: "13. Propiedad intelectual",
    paragraphs: ["El software, diseño, marca, logotipos, estructura y contenidos propios que integran Turnelia se encuentran protegidos por las normas aplicables de propiedad intelectual. El uso de la plataforma no otorga derechos de propiedad sobre dichos elementos. El usuario conserva los derechos que pudieran corresponderle sobre la información que incorpora legítimamente a Turnelia."],
  },
  {
    title: "14. Servicios de terceros",
    paragraphs: ["Turnelia puede utilizar servicios tecnológicos de terceros para operar determinadas funcionalidades, incluyendo infraestructura, correo electrónico, análisis de uso y procesamiento de pagos. La disponibilidad de algunas funciones puede depender parcialmente de dichos proveedores."],
  },
  {
    title: "15. Responsabilidad del profesional",
    paragraphs: ["Turnelia es una herramienta de gestión y no sustituye el criterio profesional. Las decisiones relacionadas con diagnóstico, tratamiento, indicaciones, atención, seguimiento y cualquier otra actuación profesional corresponden exclusivamente al profesional responsable. Turnelia tampoco garantiza resultados económicos, incremento de pacientes o resultados profesionales derivados de la utilización de la plataforma."],
  },
  {
    title: "16. Limitación de responsabilidad",
    paragraphs: ["Dentro de los límites permitidos por la normativa aplicable, Turnelia no será responsable por consecuencias derivadas de información incorrectamente cargada por usuarios, decisiones profesionales, incumplimientos entre profesionales y pacientes, credenciales comprometidas por el usuario o interrupciones originadas en servicios externos fuera del control razonable de Turnelia. Nada de lo establecido en estos términos tiene por finalidad excluir o limitar derechos que legalmente correspondan a consumidores o usuarios."],
  },
  {
    title: "17. Suspensión o cierre de cuentas",
    paragraphs: ["Turnelia podrá suspender temporalmente una cuenta ante incumplimientos graves de estos términos, actividad fraudulenta, riesgos para la seguridad de la plataforma, utilización abusiva del servicio u obligación legal. Cuando resulte razonablemente posible, el usuario será informado de la situación."],
  },
  {
    title: "18. Baja de la cuenta",
    paragraphs: ["El usuario podrá solicitar la baja de su cuenta. La eliminación o conservación posterior de determinada información dependerá de su naturaleza, las obligaciones legales aplicables, la relación con terceros y los períodos de conservación establecidos en la Política de Privacidad. La baja no implica necesariamente la eliminación inmediata de todas las copias de respaldo."],
  },
  {
    title: "19. Modificaciones de estos términos",
    paragraphs: ["Turnelia podrá actualizar estos Términos y Condiciones como consecuencia de cambios funcionales, comerciales, tecnológicos o legales. La versión vigente estará disponible en esta página e indicará la fecha de su última actualización. Cuando una modificación sea sustancial, Turnelia procurará comunicarla previamente mediante la plataforma o por correo electrónico."],
  },
  {
    title: "20. Legislación aplicable",
    paragraphs: ["Estos Términos y Condiciones se regirán por las leyes de la República Argentina. Cuando resulte aplicable la normativa de defensa del consumidor, cualquier disposición deberá interpretarse respetando los derechos establecidos por dicha legislación."],
  },
  {
    title: "21. Contacto",
    paragraphs: ["Ante consultas relacionadas con estos Términos y Condiciones puede comunicarse con Turnelia a info@turnelia.com.ar."],
  },
];

const privacySections: Section[] = [
  { title: "1. Alcance de esta política", paragraphs: ["Esta Política se aplica a los datos personales tratados mediante turnelia.com.ar y a los servicios, aplicaciones, formularios y funcionalidades asociados a Turnelia. Comprende tanto a usuarios registrados como a personas cuyos datos puedan ser incorporados por dichos usuarios, por ejemplo pacientes registrados por un profesional."] },
  { title: "2. Qué es Turnelia", paragraphs: ["Turnelia es una plataforma tecnológica destinada a facilitar tareas de gestión profesional, incluyendo administración de agendas, pacientes, turnos, disponibilidad, recordatorios y otras funcionalidades relacionadas. Cuando un profesional incorpora información relativa a sus pacientes, debe hacerlo dentro de la finalidad profesional correspondiente y conforme a las obligaciones legales aplicables."] },
  {
    title: "3. Datos que podemos tratar",
    paragraphs: ["Dependiendo de la utilización de Turnelia, podremos tratar diferentes categorías de información."],
    bullets: [
      "Datos de usuarios: nombre y apellido, correo electrónico, teléfono, información profesional, especialidad o actividad, datos de cuenta y suscripción.",
      "Datos de pacientes: nombre y apellido, teléfono, correo electrónico, datos identificatorios, turnos, historial de citas e información vinculada con la atención profesional.",
      "Datos técnicos: información necesaria para seguridad, funcionamiento, diagnóstico de errores y métricas generales del servicio.",
    ],
  },
  { title: "4. Datos relativos a la salud", paragraphs: ["Algunas funcionalidades pueden permitir que profesionales autorizados registren información relacionada con la evolución o atención de un paciente. Los datos relativos a la salud son datos sensibles y reciben protección especial conforme a la normativa argentina. Turnelia no utiliza información clínica de pacientes con fines publicitarios ni para crear perfiles comerciales propios."] },
  {
    title: "5. Finalidades del tratamiento",
    bullets: [
      "Crear, verificar y administrar cuentas de usuario.",
      "Autenticar usuarios y gestionar recuperación de contraseñas.",
      "Permitir el funcionamiento de agendas, pacientes, turnos, prestaciones y disponibilidad.",
      "Registrar información profesional cuando corresponda.",
      "Enviar recordatorios y comunicaciones relacionadas con el servicio.",
      "Gestionar suscripciones y pagos.",
      "Proporcionar soporte técnico y mejorar la seguridad de la plataforma.",
      "Obtener métricas generales de funcionamiento y cumplir obligaciones legales.",
    ],
  },
  { title: "6. Datos proporcionados por profesionales", paragraphs: ["Los profesionales pueden incorporar datos de sus pacientes. En estos casos, el profesional es responsable de contar con el fundamento correspondiente para recopilar y utilizar esa información. Turnelia procesa dichos datos para proporcionar las funcionalidades del servicio. Los datos de pacientes no pasan a formar parte de una base comercial de Turnelia, no se venden y la información clínica no se utiliza para publicidad dirigida."] },
  { title: "7. Comunicaciones por correo electrónico", paragraphs: ["Turnelia puede utilizar el correo electrónico para verificaciones de cuenta, recuperación de contraseña, recordatorios, avisos de seguridad, información de suscripciones y otras comunicaciones administrativas. Para dichos envíos puede utilizar proveedores externos especializados en correo electrónico transaccional, que reciben la información necesaria para prestar ese servicio."] },
  { title: "8. Pagos y Mercado Pago", paragraphs: ["Cuando un usuario contrata un servicio pago, determinadas operaciones pueden ser procesadas mediante Mercado Pago. Turnelia puede recibir el estado del pago, identificadores de operación, importe, moneda y referencias necesarias para vincular el pago con la cuenta. Los datos completos de tarjetas son procesados por el proveedor de pagos y Turnelia no necesita almacenarlos cuando la operación se realiza directamente mediante dicha infraestructura."] },
  { title: "9. Google Analytics y métricas", paragraphs: ["Turnelia puede utilizar herramientas de análisis, incluyendo Google Analytics, para comprender de manera general cómo se utiliza el sitio. Estas herramientas pueden recopilar páginas visitadas, dispositivo y navegador, eventos de navegación, origen aproximado del tráfico e interacciones con determinadas funciones. No utilizamos Google Analytics para incorporar información clínica de pacientes ni contenidos de evoluciones profesionales."] },
  { title: "10. Información técnica y seguridad", paragraphs: ["Determinados datos técnicos pueden procesarse automáticamente para garantizar el funcionamiento y seguridad del servicio, como dirección IP, fecha y hora de acceso, navegador, sistema operativo, registros técnicos, errores de aplicación y eventos relacionados con autenticación o seguridad."] },
  { title: "11. Cookies y tecnologías similares", paragraphs: ["Turnelia puede utilizar cookies y tecnologías similares necesarias para mantener sesiones, autenticar usuarios, recordar preferencias, preservar la seguridad y obtener métricas de uso. Cuando legalmente corresponda, se proporcionarán mecanismos para gestionar cookies no esenciales."] },
  { title: "12. Proveedores tecnológicos", paragraphs: ["Para operar la plataforma, Turnelia puede recurrir a proveedores de infraestructura y alojamiento, bases de datos, correo electrónico, procesamiento de pagos, análisis estadístico, seguridad y monitoreo. Estos proveedores reciben únicamente la información razonablemente necesaria para prestar el servicio correspondiente."] },
  { title: "13. Transferencias internacionales", paragraphs: ["Algunos proveedores tecnológicos pueden almacenar o procesar información utilizando infraestructura ubicada fuera de Argentina. Cuando corresponda, Turnelia procurará utilizar mecanismos y proveedores compatibles con las exigencias establecidas por la normativa argentina para la transferencia internacional de datos personales."] },
  {
    title: "14. Seguridad de la información",
    paragraphs: ["Turnelia adopta medidas técnicas y organizativas orientadas a proteger los datos personales. Entre ellas pueden incluirse mecanismos de autenticación, controles de acceso, comunicaciones cifradas, separación de servicios, copias de seguridad y otras medidas de protección de infraestructura. Ningún sistema conectado a Internet puede garantizar un riesgo de seguridad igual a cero."],
    bullets: ["Protección frente a accesos no autorizados.", "Prevención de pérdida, alteración o destrucción indebida.", "Controles orientados a evitar divulgación y uso no autorizados."],
  },
  { title: "15. Confidencialidad", paragraphs: ["Las personas que intervengan en el tratamiento de datos personales deben mantener la confidencialidad correspondiente, incluso después de finalizar su relación con Turnelia cuando así lo exija la normativa aplicable."] },
  { title: "16. Conservación de los datos", paragraphs: ["Turnelia conservará los datos durante el tiempo necesario para proporcionar el servicio, mantener la cuenta activa, cumplir las finalidades informadas, atender obligaciones legales o reclamos y preservar la seguridad e integridad de los sistemas. Cuando ya no resulten necesarios y no exista una obligación o justificación válida para conservarlos, podrán ser eliminados o anonimizados. Las copias de seguridad pueden conservar determinados datos durante un período adicional hasta completar sus ciclos normales de rotación."] },
  {
    title: "17. Derechos de los titulares",
    paragraphs: ["Los titulares de datos personales pueden ejercer, cuando corresponda, sus derechos de acceso, actualización, rectificación y supresión. Para realizar una solicitud puede escribirse a info@turnelia.com.ar. Turnelia podrá solicitar información razonable para verificar la identidad del solicitante antes de proporcionar, modificar o eliminar información."],
  },
  { title: "18. Datos de pacientes y ejercicio de derechos", paragraphs: ["Cuando una solicitud se refiera a información de un paciente incorporada por un profesional, puede ser necesario identificar qué profesional o cuenta administra dichos datos. Turnelia colaborará con el usuario profesional correspondiente cuando resulte necesario y legalmente procedente. Determinados datos pueden no ser eliminables inmediatamente cuando exista una obligación legal de conservación o cuando sean necesarios para preservar derechos legítimos de terceros."] },
  { title: "19. Autoridad de control", paragraphs: ["La Agencia de Acceso a la Información Pública (AAIP) es la autoridad de aplicación de la Ley N.º 25.326 y recibe consultas y denuncias relacionadas con la protección de datos personales."] },
  { title: "20. Menores de edad", paragraphs: ["Turnelia está destinada principalmente a profesionales y personas adultas que administran sus propias cuentas. Cuando un profesional registre información correspondiente a una persona menor de edad, deberá hacerlo dentro del marco de su actividad profesional y respetando las normas aplicables sobre representación, responsabilidad parental, consentimiento y confidencialidad."] },
  { title: "21. Decisiones automatizadas", paragraphs: ["Turnelia no adopta actualmente decisiones médicas, diagnósticas o profesionales automatizadas sobre pacientes. Las automatizaciones disponibles se destinan principalmente a tareas operativas, como recordatorios, notificaciones o procesos técnicos. Las decisiones relativas a la atención corresponden al profesional responsable."] },
  { title: "22. Cambios en esta política", paragraphs: ["Turnelia puede actualizar esta Política de Privacidad como consecuencia de cambios legales, tecnológicos, funcionales, operativos o comerciales. La versión vigente estará publicada en esta página e indicará su fecha de actualización. Cuando una modificación sea sustancial, Turnelia podrá informarla por correo electrónico o mediante un aviso dentro de la plataforma."] },
  { title: "23. Contacto", paragraphs: ["Para consultas sobre privacidad, protección de datos personales o ejercicio de derechos puede comunicarse con Turnelia a info@turnelia.com.ar."] },
];

const configs = {
  terminos: {
    eyebrow: "Información legal",
    title: "Términos y Condiciones de Uso de Turnelia",
    intro: "Estos Términos y Condiciones regulan el acceso y uso de Turnelia. Al registrarse, acceder o utilizar la plataforma, el usuario declara haber leído, comprendido y aceptado estas condiciones.",
    sections: termsSections,
  },
  privacidad: {
    eyebrow: "Privacidad y datos",
    title: "Política de Privacidad de Turnelia",
    intro: "Esta Política explica qué datos personales pueden ser tratados al utilizar Turnelia, con qué finalidad se utilizan, cómo se protegen y qué derechos pueden ejercer sus titulares, conforme a la normativa aplicable de la República Argentina, incluida la Ley N.º 25.326 de Protección de los Datos Personales.",
    sections: privacySections,
  },
} satisfies Record<LegalKind, { eyebrow: string; title: string; intro: string; sections: Section[] }>;

export default function LegalPage({ kind }: { kind: LegalKind }) {
  const config = configs[kind];

  return (
    <div className="legal-page">
      <header className="legal-header">
        <div className="legal-container legal-header__inner">
          <a href="/" aria-label="Turnelia, inicio" className="legal-logo">
            <img src="/brand/mediturnos-logo-horizontal.svg" alt="Turnelia" />
          </a>
          <a href="/" className="legal-back">Volver a Turnelia</a>
        </div>
      </header>

      <main className="legal-main">
        <article className="legal-container legal-document">
          <div className="legal-title">
            <p className="legal-eyebrow">{config.eyebrow}</p>
            <h1>{config.title}</h1>
            <p className="legal-updated">Última actualización: septiembre de 2026</p>
            <p className="legal-intro">{config.intro}</p>
          </div>

          <div className="legal-content">
            {config.sections.map((section) => (
              <section key={section.title}>
                <h2>{section.title}</h2>
                {section.paragraphs?.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
                {section.bullets && <ul>{section.bullets.map((bullet) => <li key={bullet}>{bullet}</li>)}</ul>}
              </section>
            ))}
          </div>
        </article>
      </main>

      <footer className="legal-footer">
        <div className="legal-container legal-footer__inner">
          <span>© 2026 Turnelia. Todos los derechos reservados.</span>
          <nav aria-label="Información legal">
            <a href="/privacidad">Privacidad</a>
            <a href="/terminos">Términos</a>
            <a href="mailto:info@turnelia.com.ar">info@turnelia.com.ar</a>
          </nav>
        </div>
      </footer>
    </div>
  );
}

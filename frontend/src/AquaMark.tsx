export default function AquaMark({ idPrefix }: { idPrefix: string }) {
  const gradient = `${idPrefix}-fill`;
  return <svg className="aqua-mark" viewBox="0 0 80 96" aria-hidden="true">
    <defs>
      <radialGradient id={gradient} cx="34%" cy="28%" r="78%">
        <stop offset="0%" stopColor="#F4FFFE" />
        <stop offset="42%" stopColor="#3CCBC0" />
        <stop offset="100%" stopColor="#0B6E68" />
      </radialGradient>
    </defs>
    <ellipse cx="40" cy="90" rx="18" ry="4.5" fill="#0B1B2B" opacity="0.16" />
    <path d="M40 4 C42 22 70 38 70 60 A30 30 0 1 1 10 60 C10 38 38 22 40 4Z" fill={`url(#${gradient})`} />
    <path d="M40 16 C44 30 58 42 58 58 A16 20 0 0 1 36 24Z" fill="#ffffff" opacity="0.38" />
    <g className="aqua-eyes">
      <ellipse cx="32" cy="58" rx="4.2" ry="5" fill="#10253C" />
      <ellipse cx="49" cy="58" rx="4.2" ry="5" fill="#10253C" />
      <circle cx="33.5" cy="56.5" r="1.3" fill="#ffffff" />
      <circle cx="50.5" cy="56.5" r="1.3" fill="#ffffff" />
    </g>
    <path d="M33 69 Q40.5 75 48 69" fill="none" stroke="#0B1B2B" strokeWidth="1.7" strokeLinecap="round" />
  </svg>;
}

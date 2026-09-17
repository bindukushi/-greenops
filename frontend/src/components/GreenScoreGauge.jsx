export default function GreenScoreGauge({ score = 0 }) {
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  const color = score >= 75 ? '#3DDC84' : score >= 45 ? '#F5A623' : '#F2664B'

  return (
    <div className="relative w-32 h-32">
      <svg width="128" height="128" viewBox="0 0 128 128" className="-rotate-90">
        <circle cx="64" cy="64" r={radius} fill="none" stroke="#26332D" strokeWidth="10" />
        <circle
          cx="64"
          cy="64"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-3xl font-semibold text-white">{score}</span>
        <span className="text-[10px] font-mono text-graphite-500 uppercase tracking-wide">/ 100 score</span>
      </div>
    </div>
  )
}

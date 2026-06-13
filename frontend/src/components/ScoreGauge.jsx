export default function ScoreGauge({ score = 0, target = 85, size = 180 }) {
  const r = (size / 2) * 0.78
  const cx = size / 2
  const cy = size / 2
  const circumference = 2 * Math.PI * r
  const progress = Math.min(score / 100, 1)
  const offset = circumference * (1 - progress)

  const colour = score >= target ? '#10b981' : score >= 60 ? '#f59e0b' : '#6366f1'

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#27272a" strokeWidth={size * 0.07} />
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={colour}
          strokeWidth={size * 0.07}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.8s ease, stroke 0.4s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-extrabold text-white" style={{ color: colour }}>
          {score.toFixed(1)}
        </span>
        <span className="text-xs text-zinc-500 mt-0.5">/ 100</span>
      </div>
    </div>
  )
}

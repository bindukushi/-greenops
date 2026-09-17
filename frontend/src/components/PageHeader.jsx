export default function PageHeader({ eyebrow, title, description, action }) {
  return (
    <div className="flex items-start justify-between gap-6 mb-8">
      <div>
        {eyebrow && (
          <p className="font-mono text-xs text-energy-500 uppercase tracking-widest mb-2">{eyebrow}</p>
        )}
        <h1 className="font-display text-2xl font-semibold text-white">{title}</h1>
        {description && <p className="text-sm text-graphite-500 mt-1 max-w-xl">{description}</p>}
      </div>
      {action}
    </div>
  )
}

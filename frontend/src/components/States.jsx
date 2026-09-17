export function EmptyState({ icon = '◌', title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6 bg-graphite-900 border border-dashed border-graphite-700 rounded-2xl animate-fade-in">
      <span className="text-3xl text-graphite-600 mb-3">{icon}</span>
      <h3 className="text-sm font-display font-semibold text-white mb-1">{title}</h3>
      {description && <p className="text-sm text-graphite-500 max-w-sm mb-4">{description}</p>}
      {action}
    </div>
  )
}

export function ErrorBanner({ message, onRetry }) {
  return (
    <div className="flex items-center justify-between gap-4 bg-alert-500/10 border border-alert-500/30 rounded-xl px-4 py-3 text-sm text-alert-500 animate-fade-in">
      <span>⚠ {message || 'Something went wrong. Please try again.'}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="focus-ring text-xs font-medium underline hover:no-underline shrink-0"
        >
          Retry
        </button>
      )}
    </div>
  )
}

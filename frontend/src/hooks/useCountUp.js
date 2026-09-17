import { useEffect, useRef, useState } from 'react'

/**
 * Animates a numeric value counting up from its previous value to `target`
 * whenever `target` changes. Falls back to displaying `target` immediately
 * if it isn't a finite number (e.g. '—' placeholders while loading).
 */
export function useCountUp(target, duration = 700) {
  const [display, setDisplay] = useState(0)
  const fromRef = useRef(0)
  const rafRef = useRef(null)

  useEffect(() => {
    const isNumber = typeof target === 'number' && Number.isFinite(target)
    if (!isNumber) {
      setDisplay(target)
      return
    }

    const from = typeof fromRef.current === 'number' ? fromRef.current : 0
    const start = performance.now()

    const step = (now) => {
      const progress = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - progress, 3)
      const value = from + (target - from) * eased
      setDisplay(value)
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(step)
      } else {
        fromRef.current = target
      }
    }

    rafRef.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(rafRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target])

  if (typeof display === 'number') {
    const decimals = target % 1 !== 0 ? 2 : 0
    return display.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  }
  return display
}

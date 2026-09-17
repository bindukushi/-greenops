import { useEffect, useRef, useState } from 'react'
import * as api from '../services/api'
import PageHeader from '../components/PageHeader'

const SUGGESTIONS = [
  'Why is my carbon emission increasing?',
  'How can I reduce emissions?',
  'What is my sustainability score?',
  'Forecast my emissions for next month',
]

export default function Assistant() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Hi, I'm the GreenOps AI Assistant. Ask me about your carbon emissions, "
        + 'sustainability score, or how to reduce your cloud footprint.',
    },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const question = text ?? input
    if (!question.trim() || busy) return
    setMessages((m) => [...m, { role: 'user', text: question }])
    setInput('')
    setBusy(true)
    try {
      const res = await api.askAssistant(question)
      setMessages((m) => [...m, { role: 'assistant', text: res.data.answer }])
    } catch {
      setMessages((m) => [...m, { role: 'assistant', text: 'Something went wrong reaching the assistant. Please try again.' }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="px-8 py-8 max-w-3xl flex flex-col h-screen">
      <PageHeader
        eyebrow="RAG-grounded"
        title="GreenOps AI Assistant"
        description="Answers are grounded in your actual telemetry — not generic advice."
      />

      <div
        ref={scrollRef}
        className="flex-1 bg-graphite-900 border border-graphite-800 rounded-2xl p-5 overflow-y-auto space-y-4 mb-4"
      >
        {messages.map((m, i) => (
          <div key={i} className={`flex animate-fade-in-up ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
                m.role === 'user'
                  ? 'bg-carbon-500 text-graphite-950 font-medium'
                  : 'bg-graphite-800 text-graphite-200 border border-graphite-700'
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex justify-start animate-fade-in">
            <div className="bg-graphite-800 border border-graphite-700 rounded-xl px-4 py-2.5 text-sm text-graphite-500 font-mono animate-pulse-dot">
              analyzing telemetry...
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => send(s)}
            className="focus-ring text-xs bg-graphite-900 hover:bg-graphite-800 active:scale-95 border border-graphite-700 text-graphite-400 hover:text-carbon-400 px-3 py-1.5 rounded-full transition-all"
          >
            {s}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); send() }}
        className="flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your emissions, score, or optimizations..."
          className="focus-ring flex-1 bg-graphite-900 border border-graphite-800 rounded-lg px-4 py-3 text-sm text-white placeholder-graphite-600"
        />
        <button
          type="submit"
          disabled={busy}
          className="focus-ring bg-carbon-500 hover:bg-carbon-400 active:scale-95 disabled:opacity-60 text-graphite-950 font-semibold text-sm px-5 rounded-lg transition-all"
        >
          Send
        </button>
      </form>
    </div>
  )
}

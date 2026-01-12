import React, { useEffect, useRef, useState } from 'react'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.min.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export default function App() {
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('python')
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [filePath, setFilePath] = useState('')

  const fileInputRef = useRef(null)

  const onDrop = async (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (!file) return
    const text = await file.text()
    setCode(text)
  }

  const onUploadClick = () => fileInputRef.current?.click()

  const onFileChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const text = await file.text()
    setCode(text)
  }

  const readLocalFile = async () => {
    if (!filePath.trim()) return
    setError(null)
    setIsLoading(true)
    try {
      const r = await fetch(`${API_URL}/read-file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: filePath })
      })
      if (!r.ok) throw new Error(await r.text())
      const data = await r.json()
      setCode(data.content || '')
    } catch (e) {
      setError(e.message || 'Failed to read file')
    } finally {
      setIsLoading(false)
    }
  }

  const submitReview = async () => {
    if (!code.trim()) return
    setIsLoading(true)
    setError(null)
    setResults(null)
    try {
      const r = await fetch(`${API_URL}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language })
      })
      if (!r.ok) throw new Error(await r.text())
      const data = await r.json()
      setResults(data)
    } catch (e) {
      setError(e.message || 'Request failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="container">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold">Local Code Reviewer (MCP)</h1>
        <p className="text-gray-400">All on your machine via Ollama</p>
      </header>

      <div className="grid md:grid-cols-2 gap-4">
        <section className="card space-y-3" onDrop={onDrop} onDragOver={(e)=>e.preventDefault()}>
          <div className="flex items-center justify-between">
            <label className="label">Paste code or drop a file</label>
            <div className="flex gap-2">
              <select className="input w-auto" value={language} onChange={(e)=>setLanguage(e.target.value)}>
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
                <option value="java">Java</option>
                <option value="go">Go</option>
                <option value="csharp">C#</option>
              </select>
              <button className="btn" onClick={onUploadClick}>Upload</button>
              <input type="file" ref={fileInputRef} onChange={onFileChange} className="hidden" />
            </div>
          </div>
          <textarea className="input h-64 font-mono" value={code} onChange={(e)=>setCode(e.target.value)} placeholder="// Paste your code here" />

          <div className="space-y-2">
            <label className="label">Or read local file by path</label>
            <div className="flex gap-2">
              <input className="input flex-1" value={filePath} onChange={(e)=>setFilePath(e.target.value)} placeholder="C:\\path\\to\\file.py" />
              <button className="btn" disabled={isLoading || !filePath.trim()} onClick={readLocalFile}>Read</button>
            </div>
          </div>

          <div className="flex justify-end">
            <button className="btn" disabled={isLoading || !code.trim()} onClick={submitReview}>Review</button>
          </div>
        </section>

        <section className="card space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Results</h2>
            {isLoading && <span className="text-blue-400 animate-pulse">Reviewing…</span>}
          </div>

          {error && (
            <div className="text-red-400 whitespace-pre-wrap text-sm border border-red-900 bg-red-950/30 p-2 rounded">{String(error)}</div>
          )}

          {results?.review ? (
            <article className="prose prose-invert max-w-none">
              <div className="flex justify-end mb-2">
                <button className="btn" onClick={() => navigator.clipboard.writeText(results.review)}>Copy</button>
              </div>
              <Markdown text={results.review} />
              <div className="text-xs text-gray-500 mt-2">Model: {results.model} · {new Date(results.timestamp).toLocaleString()}</div>
            </article>
          ) : (
            <p className="text-gray-500">No results yet.</p>
          )}
        </section>
      </div>
    </div>
  )
}

function Markdown({ text }) {
  // Very tiny markdown to HTML converter for headings and code blocks (no XSS protection, local usage)
  const html = text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br />')
  const ref = useRef(null)
  useEffect(() => {
    if (!ref.current) return
    ref.current.querySelectorAll('pre code').forEach((el) => {
      try { hljs.highlightElement(el) } catch {}
    })
  }, [text])
  return <div ref={ref} dangerouslySetInnerHTML={{ __html: html }} />
}

import { useState } from 'react'
import { motion } from 'framer-motion'
import Container from '@mui/material/Container'
import Grid from '@mui/material/Grid'
import Button from '@mui/material/Button'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'
import toast from 'react-hot-toast'

import Editor from '../components/Editor'
import AnalysisViewer from '../components/AnalysisViewer'
import DraftPreview from '../components/DraftPreview'
import Sidebar from '../components/Sidebar'
import ThemeToggle from '../components/ThemeToggle'
import CompareDrafts from '../components/CompareDrafts'
import LoadingOverlay from '../components/LoadingOverlay'
import { useLocalStorage } from '../hooks/useLocalStorage'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function Home({ themeMode, setThemeMode }) {
  const [emailText, setEmailText] = useLocalStorage('emailText', '')
  const [contractSnippet, setContractSnippet] = useLocalStorage('contractSnippet', '')
  const [analysis, setAnalysis] = useState(null)
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)

  const analyze = async () => {
    if (!emailText.trim()) return toast.error('Please paste an email first')
    setLoading(true)
    try {
      const r = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST', headers: { 'Content-Type':'application/json' },
        body: JSON.stringify({ email_text: emailText, contract_snippet: contractSnippet })
      })
      if (!r.ok) {
        const text = await r.text()
        try { const j = JSON.parse(text); throw new Error(j.detail || text) } catch { throw new Error(text) }
      }
      const data = await r.json()
      setAnalysis(data)
      toast.success('Analyzed')
    } catch (e) {
      console.error(e)
      toast.error(e?.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const processAll = async () => {
    if (!emailText.trim()) return toast.error('Please paste an email first')
    setLoading(true)
    try {
      const r = await fetch(`${API_BASE}/api/process`, {
        method: 'POST', headers: { 'Content-Type':'application/json' },
        body: JSON.stringify({ email_text: emailText, contract_snippet: contractSnippet })
      })
      if (!r.ok) {
        const text = await r.text()
        try { const j = JSON.parse(text); throw new Error(j.detail || text) } catch { throw new Error(text) }
      }
      const data = await r.json()
      setAnalysis(data.analysis)
      setDraft(data.draft)
      toast.success('Analysis + Draft ready')
    } catch (e) {
      console.error(e)
      toast.error('Processing failed')
    } finally {
      setLoading(false)
    }
  }

  const draftOnly = async () => {
    if (!emailText.trim()) return toast.error('Please paste an email first')
    if (!analysis) return toast.error('Run analysis first or use Process')
    setLoading(true)
    try {
      const r = await fetch(`${API_BASE}/api/draft`, {
        method: 'POST', headers: { 'Content-Type':'application/json' },
        body: JSON.stringify({ email_text: emailText, analysis, contract_snippet: contractSnippet })
      })
      if (!r.ok) {
        const text = await r.text()
        try { const j = JSON.parse(text); throw new Error(j.detail || text) } catch { throw new Error(text) }
      }
      const data = await r.json()
      setDraft(data.draft)
      toast.success('Draft generated')
    } catch (e) {
      console.error(e)
      toast.error('Draft failed')
    } finally { setLoading(false) }
  }

  return (
    <Container maxWidth="xl" className="container-max py-6">
      <LoadingOverlay open={loading} label={analysis ? 'Generating draft…' : 'Analyzing…'} />
      <div className="flex items-center justify-between mb-6">
        <Typography variant="h4" className="font-bold">Legal Email Assistant</Typography>
        <ThemeToggle themeMode={themeMode} setThemeMode={setThemeMode} />
      </div>

      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <Sidebar setEmailText={setEmailText} setContractSnippet={setContractSnippet} />
        </Grid>
        <Grid item xs={12} md={9}>
          <div className="card p-4">
            <Editor value={emailText} onChange={setEmailText} contractValue={contractSnippet} onContractChange={setContractSnippet} loading={loading} />
            <div className="flex gap-3 mt-4">
              <Button variant="contained" className="btn-primary" onClick={analyze} disabled={loading}>Analyze</Button>
              <Button variant="outlined" className="btn-secondary" onClick={draftOnly} disabled={loading}>Draft</Button>
              <Button variant="contained" color="secondary" onClick={processAll} disabled={loading}>Process</Button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
            <motion.div className="card p-4" initial={{opacity:0, y:10}} animate={{opacity:1, y:0}}>
              <Typography variant="h6" className="mb-2">Analysis JSON</Typography>
              <AnalysisViewer data={analysis} />
            </motion.div>
            <motion.div className="card p-4" initial={{opacity:0, y:10}} animate={{opacity:1, y:0}}>
              <Typography variant="h6" className="mb-2">Draft Preview</Typography>
              <DraftPreview draft={draft} />
            </motion.div>
          </div>

          <div className="mt-4">
            <CompareDrafts emailText={emailText} analysis={analysis} contractSnippet={contractSnippet} apiBase={API_BASE} />
          </div>
        </Grid>
      </Grid>
    </Container>
  )
}

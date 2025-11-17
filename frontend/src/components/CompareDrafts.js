import { useState } from 'react'
import Button from '@mui/material/Button'
import Grid from '@mui/material/Grid'
import Typography from '@mui/material/Typography'
import toast from 'react-hot-toast'

export default function CompareDrafts({ emailText, analysis, contractSnippet, apiBase }) {
  const [left, setLeft] = useState('')
  const [right, setRight] = useState('')
  const [loading, setLoading] = useState(false)

  const go = async () => {
    if (!emailText.trim()) return toast.error('Please paste an email first')
    setLoading(true)
    try {
      const bodyA = JSON.stringify({ email_text: emailText, analysis, contract_snippet: contractSnippet, variant: 'A' })
      const bodyB = JSON.stringify({ email_text: emailText, analysis, contract_snippet: contractSnippet, variant: 'B' })
      const [a, b] = await Promise.all([
        fetch(`${apiBase}/api/draft`, { method: 'POST', headers: { 'Content-Type':'application/json' }, body: bodyA }),
        fetch(`${apiBase}/api/draft`, { method: 'POST', headers: { 'Content-Type':'application/json' }, body: bodyB }),
      ])
      const leftJson = await a.json()
      const rightJson = await b.json()
      setLeft(leftJson.draft || '')
      setRight(rightJson.draft || '')
    } catch (e) {
      console.error(e)
      toast.error('Compare failed')
    } finally { setLoading(false) }
  }

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-2">
        <Typography variant="h6">Compare Drafts</Typography>
        <Button variant="outlined" onClick={go} disabled={loading}>Generate Two Versions</Button>
      </div>
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <div className="text-xs text-gray-500 mb-1">Version A</div>
          <div className="whitespace-pre-wrap text-sm min-h-[160px] border border-gray-200 dark:border-gray-800 rounded-lg p-3">{left || '—'}</div>
        </Grid>
        <Grid item xs={12} md={6}>
          <div className="text-xs text-gray-500 mb-1">Version B</div>
          <div className="whitespace-pre-wrap text-sm min-h-[160px] border border-gray-200 dark:border-gray-800 rounded-lg p-3">{right || '—'}</div>
        </Grid>
      </Grid>
    </div>
  )
}

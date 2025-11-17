import Button from '@mui/material/Button'
import { saveAs } from 'file-saver'
import { jsPDF } from 'jspdf'

export default function DraftPreview({ draft }) {
  const download = () => {
    const blob = new Blob([draft || ''], { type: 'text/plain;charset=utf-8' })
    saveAs(blob, 'draft.txt')
  }

  const exportPdf = () => {
    const doc = new jsPDF({ unit: 'pt', format: 'a4' })
    const margin = 40
    const maxWidth = 515
    const text = draft || ''
    const lines = doc.splitTextToSize(text, maxWidth)
    doc.text(lines, margin, margin)
    doc.save('draft.pdf')
  }

  return (
    <div>
      <div className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 min-h-[200px] border border-gray-200 dark:border-gray-800 rounded-lg p-3">
        {draft || 'No draft yet.'}
      </div>
      <div className="mt-3 flex gap-2">
        <Button variant="outlined" onClick={download} disabled={!draft}>Export TXT</Button>
        <Button variant="outlined" onClick={exportPdf} disabled={!draft}>Export PDF</Button>
      </div>
    </div>
  )
}

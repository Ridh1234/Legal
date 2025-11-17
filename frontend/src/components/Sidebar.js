import Button from '@mui/material/Button'
import Typography from '@mui/material/Typography'

const sampleEmail = `Hello Team,\n\nPlease approve the proposed changes to the MSA. This is fairly urgent, ideally by end of week. Also, could you clarify the liability limits?\n\nThanks,\nBuyer`

const sampleContract = `Refer to Clause 9.1 (Confidentiality) and Clause 10.2 (Limitation of Liability).`

export default function Sidebar({ setEmailText, setContractSnippet }) {
  return (
    <div className="card p-4 sticky top-4 space-y-3">
      <Typography variant="h6">Quick Actions</Typography>
      <Button variant="outlined" onClick={() => setEmailText(sampleEmail)}>Load Sample Email</Button>
      <Button variant="outlined" onClick={() => setContractSnippet(sampleContract)}>Load Sample Clause</Button>
      <div className="text-xs text-gray-500">
        Roadmap: attachments, thread history, firm style guides.
      </div>
    </div>
  )
}

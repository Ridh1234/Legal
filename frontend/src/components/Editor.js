import TextField from '@mui/material/TextField'
import Grid from '@mui/material/Grid'
import Skeleton from '@mui/material/Skeleton'

export default function Editor({ value, onChange, contractValue, onContractChange, loading }) {
  return (
    <div>
      <Grid container spacing={2}>
        <Grid item xs={12} md={8}>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Email Text</label>
          <TextField
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder="Paste the legal email here..."
            fullWidth
            minRows={10}
            multiline
            sx={{ mt: 1 }}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Contract Clause (Playground)</label>
          <TextField
            value={contractValue}
            onChange={e => onContractChange(e.target.value)}
            placeholder="Optional: paste or modify relevant clause(s)"
            fullWidth
            minRows={10}
            multiline
            sx={{ mt: 1 }}
          />
        </Grid>
      </Grid>
      {loading ? (
        <div className="mt-3">
          <Skeleton variant="rectangular" height={24} />
        </div>
      ) : null}
    </div>
  )
}

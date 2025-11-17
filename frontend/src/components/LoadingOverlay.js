import Backdrop from '@mui/material/Backdrop'
import CircularProgress from '@mui/material/CircularProgress'
import Typography from '@mui/material/Typography'

export default function LoadingOverlay({ open, label = 'Working...' }) {
  return (
    <Backdrop open={open} sx={{ color: '#fff', zIndex: theme => theme.zIndex.modal + 1 }}>
      <div className="flex flex-col items-center gap-3">
        <CircularProgress color="inherit" thickness={5} size={64} />
        <Typography variant="subtitle1">{label}</Typography>
      </div>
    </Backdrop>
  )
}

import IconButton from '@mui/material/IconButton'
import DarkModeIcon from '@mui/icons-material/DarkMode'
import LightModeIcon from '@mui/icons-material/LightMode'

export default function ThemeToggle({ themeMode, setThemeMode }) {
  const toggle = () => {
    const next = themeMode === 'dark' ? 'light' : 'dark'
    setThemeMode(next)
    if (typeof window !== 'undefined') localStorage.setItem('theme-mode', next)
    document.documentElement.classList.toggle('dark', next === 'dark')
  }
  return (
    <IconButton onClick={toggle} aria-label="Toggle theme">
      {themeMode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
    </IconButton>
  )
}

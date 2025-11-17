import * as React from 'react'
import Head from 'next/head'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { useEffect, useMemo, useState } from 'react'
import '../styles/globals.css'
import { Toaster } from 'react-hot-toast'

export default function MyApp({ Component, pageProps }) {
  const [mode, setMode] = useState('light')

  useEffect(() => {
    const stored = typeof window !== 'undefined' && localStorage.getItem('theme-mode')
    if (stored) setMode(stored)
    document.documentElement.classList.toggle('dark', (stored || 'light') === 'dark')
  }, [])

  const theme = useMemo(() => createTheme({ palette: { mode }}), [mode])

  return (
    <>
      <Head>
        <title>Legal Email Assistant</title>
        <meta name="viewport" content="initial-scale=1, width=device-width" />
      </Head>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Toaster position="top-right" />
        <Component {...pageProps} themeMode={mode} setThemeMode={setMode} />
      </ThemeProvider>
    </>
  )
}

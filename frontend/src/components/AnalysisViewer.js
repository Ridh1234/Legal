import Box from '@mui/material/Box'

export default function AnalysisViewer({ data }) {
  return (
    <Box sx={{ minHeight: 200 }}>
      {data ? (
        <pre className="text-xs bg-gray-50 dark:bg-gray-900 p-3 rounded-lg overflow-auto border border-gray-200 dark:border-gray-800">
          {JSON.stringify(data, null, 2)}
        </pre>
      ) : (
        <div className="text-gray-500">No analysis yet.</div>
      )}
    </Box>
  )
}

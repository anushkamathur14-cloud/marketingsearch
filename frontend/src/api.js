const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, '') || ''

export function apiUrl(path) {
  return `${API_BASE}${path}`
}

export async function apiFetch(path, options) {
  const res = await fetch(apiUrl(path), options)
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`)
  }
  return res.json()
}

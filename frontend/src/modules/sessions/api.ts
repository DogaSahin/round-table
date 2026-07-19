import { apiFetch } from '@/api/client'

export interface SessionLogEntry {
  id: number
  text: string
  tag: string
  logged_at: string
  resolved_at: string | null
}

export interface SessionListItem {
  id: number
  number: number
  date: string
  title: string
  status: string
}

export interface SessionDetail {
  id: number
  number: number
  date: string
  title: string
  summary: string | null
  status: string
  logs: SessionLogEntry[]
}

export function listSessions(): Promise<SessionListItem[]> {
  return apiFetch<SessionListItem[]>('/api/sessions')
}

export function createSession(title: string): Promise<SessionDetail> {
  return apiFetch<SessionDetail>('/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
}

export function fetchSession(sessionId: number): Promise<SessionDetail> {
  return apiFetch<SessionDetail>(`/api/sessions/${sessionId}`)
}

export function deleteSession(sessionId: number): Promise<void> {
  return apiFetch<void>(`/api/sessions/${sessionId}`, { method: 'DELETE' })
}

export function activateSession(sessionId: number): Promise<SessionDetail> {
  return apiFetch<SessionDetail>(`/api/sessions/${sessionId}/activate`, { method: 'POST' })
}

export function addLog(sessionId: number, text: string, tag: string): Promise<SessionLogEntry> {
  return apiFetch<SessionLogEntry>(`/api/sessions/${sessionId}/logs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, tag }),
  })
}

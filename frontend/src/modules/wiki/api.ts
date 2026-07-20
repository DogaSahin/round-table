import { apiFetch } from '@/api/client'

export interface WikiTag {
  id: number
  name: string
}

export interface WikiLinkEntry {
  target_title: string
  target_type: string
  target_id: number | null
  resolved: boolean
}

export interface WikiPageListItem {
  id: number
  title: string
  slug: string
  category: string | null
  player_visible: boolean
}

export interface WikiPageDetail {
  id: number
  title: string
  slug: string
  category: string | null
  body_md: string | null
  body_html: string
  player_visible: boolean
  updated_at: string
  tags: WikiTag[]
  links: WikiLinkEntry[]
  backlinks: WikiPageListItem[]
}

export interface WikiPagePatch {
  title?: string
  category?: string | null
  body_md?: string | null
  player_visible?: boolean
}

export function listPages(): Promise<WikiPageListItem[]> {
  return apiFetch<WikiPageListItem[]>('/api/wiki')
}

export function searchPages(query: string): Promise<WikiPageListItem[]> {
  return apiFetch<WikiPageListItem[]>(`/api/wiki/search?q=${encodeURIComponent(query)}`)
}

export function createPage(
  title: string,
  category: string | null,
  bodyMd: string | null,
  playerVisible: boolean,
): Promise<WikiPageDetail> {
  return apiFetch<WikiPageDetail>('/api/wiki', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title,
      category,
      body_md: bodyMd,
      player_visible: playerVisible,
    }),
  })
}

export function fetchPage(slug: string): Promise<WikiPageDetail> {
  return apiFetch<WikiPageDetail>(`/api/wiki/${slug}`)
}

export function updatePage(slug: string, patch: WikiPagePatch): Promise<WikiPageDetail> {
  return apiFetch<WikiPageDetail>(`/api/wiki/${slug}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
}

export function deletePage(slug: string): Promise<void> {
  return apiFetch<void>(`/api/wiki/${slug}`, { method: 'DELETE' })
}

export function addTag(slug: string, name: string): Promise<WikiTag> {
  return apiFetch<WikiTag>(`/api/wiki/${slug}/tags`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export function removeTag(slug: string, tagId: number): Promise<void> {
  return apiFetch<void>(`/api/wiki/${slug}/tags/${tagId}`, { method: 'DELETE' })
}

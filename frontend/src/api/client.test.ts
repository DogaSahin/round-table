import { afterEach, describe, expect, it, vi } from 'vitest'
// ApiError is imported to document that client.ts exports it alongside apiFetch (every
// future module will import both), even though these tests assert shape via toMatchObject
// rather than instanceof.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { ApiError, apiFetch } from './client'

describe('apiFetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns parsed JSON on a successful response', async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', mockFetch)

    const result = await apiFetch<{ status: string }>('/health')

    expect(result).toEqual({ status: 'ok' })
    expect(mockFetch).toHaveBeenCalledWith('/health', undefined)
  })

  it('throws ApiError with code/message/details from the error envelope', async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { code: 'not_found', message: 'campaign 7 does not exist', details: { id: 7 } },
        }),
        { status: 404, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', mockFetch)

    await expect(apiFetch('/campaigns/7')).rejects.toMatchObject({
      code: 'not_found',
      message: 'campaign 7 does not exist',
      details: { id: 7 },
      status: 404,
    })
  })

  it('throws a generic ApiError when the error body is not the expected envelope shape', async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValue(new Response('Internal Server Error', { status: 500 }))
    vi.stubGlobal('fetch', mockFetch)

    await expect(apiFetch('/boom')).rejects.toMatchObject({
      code: 'unknown_error',
      status: 500,
    })
  })

  it('passes through the init argument (method, body, headers)', async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', mockFetch)

    await apiFetch('/thing', { method: 'POST', body: JSON.stringify({ a: 1 }) })

    expect(mockFetch).toHaveBeenCalledWith('/thing', {
      method: 'POST',
      body: JSON.stringify({ a: 1 }),
    })
  })
})

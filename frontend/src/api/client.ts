interface ErrorEnvelope {
  error: {
    code: string
    message: string
    details: Record<string, unknown>
  }
}

function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  if (typeof value !== 'object' || value === null || !('error' in value)) return false
  const err = (value as { error: unknown }).error
  return (
    typeof err === 'object' && err !== null && 'code' in err && 'message' in err && 'details' in err
  )
}

export class ApiError extends Error {
  code: string
  details: Record<string, unknown>
  status: number

  constructor(code: string, message: string, details: Record<string, unknown>, status: number) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.details = details
    this.status = status
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)

  if (!response.ok) {
    let body: unknown = null
    try {
      body = await response.json()
    } catch {
      body = null
    }
    if (isErrorEnvelope(body)) {
      throw new ApiError(body.error.code, body.error.message, body.error.details, response.status)
    }
    throw new ApiError(
      'unknown_error',
      response.statusText || 'Request failed',
      {},
      response.status,
    )
  }

  const text = await response.text()
  if (text.length === 0) {
    return undefined as T
  }
  try {
    return JSON.parse(text) as T
  } catch {
    throw new ApiError('unknown_error', 'Invalid JSON response', {}, response.status)
  }
}

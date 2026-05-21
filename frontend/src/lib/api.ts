import { storage } from '@/lib/storage'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = storage.getToken()
  const saasAgentId = storage.getSaaSAgentId()

  const isFormData = options.body instanceof FormData

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  }

  if (!isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  if (token && token !== 'undefined' && token !== 'null') {
    headers.Authorization = `Bearer ${token}`
  }

  if (saasAgentId) {
    headers['X-SaaSAgent-ID'] = saasAgentId
  }

  const response = await fetch(`/api${path}`, {
    ...options,
    credentials: 'same-origin',
    headers,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }))
    throw new ApiError(body.detail || response.statusText, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
  upload: <T>(path: string, file: File, fieldName: string = 'file') => {
    const fd = new FormData()
    fd.append(fieldName, file)
    return request<T>(path, { method: 'POST', body: fd })
  },
  postStream: (
    path: string,
    onEvent: (eventType: string, data: Record<string, unknown>) => void,
  ) =>
    new Promise<void>((resolve, reject) => {
      const token = storage.getToken()
      const saasAgentId = storage.getSaaSAgentId()
      const xhr = new XMLHttpRequest()
      let cursor = 0
      let buffer = ''
      xhr.open('POST', `/api${path}`)
      xhr.setRequestHeader('Content-Type', 'application/json')
      if (token && token !== 'undefined' && token !== 'null') {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      }
      if (saasAgentId) {
        xhr.setRequestHeader('X-SaaSAgent-ID', saasAgentId)
      }
      xhr.onprogress = () => {
        const chunk = xhr.responseText.slice(cursor)
        cursor = xhr.responseText.length
        buffer += chunk
        const events = buffer.split('\n\n')
        buffer = events.pop() || ''
        for (const eventText of events) {
          const lines = eventText.split('\n')
          const eventLine = lines.find((line) => line.startsWith('event: '))
          const dataLine = lines.find((line) => line.startsWith('data: '))
          if (!eventLine || !dataLine) continue
          try {
            onEvent(eventLine.slice(7).trim(), JSON.parse(dataLine.slice(6)))
          } catch {
            // Wait for the next progress chunk if JSON is incomplete.
          }
        }
      }
      xhr.onloadend = () => {
        if (buffer.trim()) {
          const lines = buffer.split('\n')
          const eventLine = lines.find((line) => line.startsWith('event: '))
          const dataLine = lines.find((line) => line.startsWith('data: '))
          if (eventLine && dataLine) {
            try {
              onEvent(eventLine.slice(7).trim(), JSON.parse(dataLine.slice(6)))
            } catch {
              // Ignore an incomplete final event.
            }
          }
        }
        if (xhr.status >= 400) reject(new ApiError(`Request failed (${xhr.status})`, xhr.status))
        else resolve()
      }
      xhr.onerror = () => reject(new ApiError('Connection failed', 0))
      xhr.send()
    }),
  getStream: (
    path: string,
    onEvent: (eventType: string, data: Record<string, unknown>) => void,
  ) =>
    new Promise<void>((resolve, reject) => {
      const token = storage.getToken()
      const saasAgentId = storage.getSaaSAgentId()
      const xhr = new XMLHttpRequest()
      let cursor = 0
      let buffer = ''
      xhr.open('GET', `/api${path}`)
      if (token && token !== 'undefined' && token !== 'null') {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      }
      if (saasAgentId) {
        xhr.setRequestHeader('X-SaaSAgent-ID', saasAgentId)
      }
      xhr.onprogress = () => {
        const chunk = xhr.responseText.slice(cursor)
        cursor = xhr.responseText.length
        buffer += chunk
        const events = buffer.split('\n\n')
        buffer = events.pop() || ''
        for (const eventText of events) {
          const lines = eventText.split('\n')
          const eventLine = lines.find((line) => line.startsWith('event: '))
          const dataLine = lines.find((line) => line.startsWith('data: '))
          if (!eventLine || !dataLine) continue
          try {
            onEvent(eventLine.slice(7).trim(), JSON.parse(dataLine.slice(6)))
          } catch {
            // Wait for the next progress chunk if JSON is incomplete.
          }
        }
      }
      xhr.onloadend = () => {
        if (xhr.status >= 400) reject(new ApiError(`Request failed (${xhr.status})`, xhr.status))
        else resolve()
      }
      xhr.onerror = () => reject(new ApiError('Connection failed', 0))
      xhr.send()
    }),
}

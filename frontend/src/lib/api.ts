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
  const workspaceId = storage.getWorkspaceId()

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

  if (workspaceId) {
    headers['X-Workspace-ID'] = workspaceId
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
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
  upload: <T>(path: string, file: File, fieldName: string = 'file') => {
    const fd = new FormData()
    fd.append(fieldName, file)
    return request<T>(path, { method: 'POST', body: fd })
  },
}

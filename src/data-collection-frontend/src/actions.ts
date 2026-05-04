const API_BASE_URL = 'http://localhost:5000'

export type Dataset = {
  id: number
  name: string
  description: string
}

export type DatasetPayload = {
  name: string
  description: string
}

async function requestJson<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options)

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function getDatasets() {
  return requestJson<Dataset[]>('/api/v1/datasets/')
}

export function createDataset(payload: DatasetPayload) {
  return requestJson<Dataset>('/api/v1/datasets/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

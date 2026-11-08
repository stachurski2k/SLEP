const modelServiceUrl = import.meta.env.VITE_MODEL_SERVICE_URL ?? 'http://localhost:5001'

export type GesturePrediction = {
  label: string
  score: number
  margin: number
}

type ApiErrorResponse = {
  detail?: string
}

export async function predictGesture(video: Blob, signal?: AbortSignal): Promise<GesturePrediction> {
  const formData = new FormData()
  formData.append('video', video, 'gesture.webm')

  const response = await fetch(`${modelServiceUrl}/api/v1/predict`, {
    method: 'POST',
    body: formData,
    signal,
  })

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorResponse | null
    throw new Error(body?.detail ?? 'The gesture could not be recognized. Please try again.')
  }

  return response.json() as Promise<GesturePrediction>
}

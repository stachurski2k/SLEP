import type { GesturePrediction } from '../types/lesson'
import { modelServiceUrl, parseApiError } from './client'

export async function predictGesture(video: Blob, signal?: AbortSignal): Promise<GesturePrediction> {
  const formData = new FormData()
  formData.append('video', video, 'gesture.webm')

  const response = await fetch(`${modelServiceUrl}/api/v1/predict`, {
    method: 'POST',
    body: formData,
    signal,
  })

  if (!response.ok) {
    throw new Error(
      await parseApiError(response, 'The gesture could not be recognized. Please try again.'),
    )
  }

  return response.json() as Promise<GesturePrediction>
}

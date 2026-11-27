import type { GesturePrediction } from '../types/lesson'
import { modelServiceUrl, parseApiError } from './client'

export async function predictGesture(video: Blob, signal?: AbortSignal): Promise<GesturePrediction> {
  const formData = new FormData()
  formData.append('video', video, 'gesture.webm')

  let response: Response
  try {
    response = await fetch(`${modelServiceUrl}/api/v1/predict`, {
      method: 'POST',
      body: formData,
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    throw new Error(
      `Model service (${modelServiceUrl}) is unreachable. Make sure model-service is running on port 5001.`,
      { cause: error },
    )
  }

  if (!response.ok) {
    throw new Error(
      await parseApiError(response, 'The gesture could not be recognized. Please try again.'),
    )
  }

  return response.json() as Promise<GesturePrediction>
}

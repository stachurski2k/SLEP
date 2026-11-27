import type {
  LessonCompletionResult,
  LessonProgress,
  ProgressSummary,
  UserProgress,
} from '../types/progress'
import { authenticatedFetch, parseApiError } from './client'

export async function fetchProgressSummary(): Promise<ProgressSummary> {
  const response = await authenticatedFetch('/api/v1/progress/summary')
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to fetch progress summary.'))
  }
  return response.json() as Promise<ProgressSummary>
}

export async function fetchUserProgress(): Promise<UserProgress> {
  const response = await authenticatedFetch('/api/v1/progress')
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to fetch user progress.'))
  }
  return response.json() as Promise<UserProgress>
}

export async function fetchLessonProgress(lessonId: string): Promise<LessonProgress> {
  const response = await authenticatedFetch(`/api/v1/progress/lessons/${lessonId}`)
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to fetch lesson progress.'))
  }
  return response.json() as Promise<LessonProgress>
}

export async function startLessonProgress(lessonId: string): Promise<LessonProgress> {
  const response = await authenticatedFetch(`/api/v1/progress/lessons/${lessonId}/start`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to start lesson progress.'))
  }
  return response.json() as Promise<LessonProgress>
}

export async function completeLessonProgress(
  lessonId: string,
  xpReward?: number,
): Promise<LessonCompletionResult> {
  const response = await authenticatedFetch(`/api/v1/progress/lessons/${lessonId}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(xpReward !== undefined ? { xpReward } : {}),
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to complete lesson progress.'))
  }
  return response.json() as Promise<LessonCompletionResult>
}

export async function resetLessonProgress(lessonId: string): Promise<LessonProgress> {
  const response = await authenticatedFetch(`/api/v1/progress/lessons/${lessonId}/reset`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to reset lesson progress.'))
  }
  return response.json() as Promise<LessonProgress>
}

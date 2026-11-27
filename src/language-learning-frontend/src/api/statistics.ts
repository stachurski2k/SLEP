import type {
  DailyActivity,
  LearningStatistics,
  RecordActivityInput,
  WeeklyReport,
} from '../types/progress'
import { authenticatedFetch, parseApiError } from './client'

export async function fetchLearningStatistics(): Promise<LearningStatistics> {
  const response = await authenticatedFetch('/api/v1/statistics')
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to fetch learning statistics.'))
  }
  return response.json() as Promise<LearningStatistics>
}

export async function fetchWeeklyReport(referenceDate?: string): Promise<WeeklyReport> {
  const query = referenceDate ? `?date=${encodeURIComponent(referenceDate)}` : ''
  const response = await authenticatedFetch(`/api/v1/statistics/weekly${query}`)
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to fetch weekly activity report.'))
  }
  return response.json() as Promise<WeeklyReport>
}

export async function fetchUserAccuracy(): Promise<{ accuracy: number }> {
  const response = await authenticatedFetch('/api/v1/statistics/accuracy')
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to fetch accuracy score.'))
  }
  return response.json() as Promise<{ accuracy: number }>
}

export async function recordDailyActivity(
  payload: RecordActivityInput,
): Promise<DailyActivity | null> {
  const response = await authenticatedFetch('/api/v1/statistics/record', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to record daily activity.'))
  }
  return response.json() as Promise<DailyActivity | null>
}

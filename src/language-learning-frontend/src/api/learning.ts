import { lessons } from '../data/lessons'
import type {
  AvailablePosesResponse,
  ExerciseCreateInput,
  ExerciseEntity,
  ExerciseUpdateInput,
  LessonCreateInput,
  LessonEntity,
  LessonUpdateInput,
  UnitCreateInput,
  UnitEntity,
  UnitUpdateInput,
  ValidationResultResponse,
} from '../types/learning'
import { authenticatedFetch, modelServiceUrl, parseApiError } from './client'

export async function getAvailablePoses(): Promise<AvailablePosesResponse> {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 2500)

    const response = await fetch(`${modelServiceUrl}/api/v1/classes`, {
      method: 'GET',
      signal: controller.signal,
    }).finally(() => clearTimeout(timeoutId))

    if (response.ok) {
      const data = (await response.json()) as string[]
      if (Array.isArray(data) && data.length > 0) {
        return {
          poses: data,
          source: 'model-service',
        }
      }
    }
  } catch {
    // Model service is offline or unreachable - fallback to lessons.ts
  }

  const fallbackPoses = Array.from(new Set(lessons.flatMap((l) => l.signs)))
  return {
    poses: fallbackPoses,
    source: 'lessons.ts',
  }
}

export async function fetchUnits(): Promise<UnitEntity[]> {
  const response = await authenticatedFetch('/api/v1/units')
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to fetch units.'))
  }
  return response.json() as Promise<UnitEntity[]>
}

export async function fetchUnitDetails(unitId: string): Promise<UnitEntity> {
  const response = await authenticatedFetch(`/api/v1/units/${unitId}`)
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to fetch unit details.'))
  }
  return response.json() as Promise<UnitEntity>
}

export async function createUnit(data: UnitCreateInput): Promise<UnitEntity> {
  const response = await authenticatedFetch('/api/v1/units', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to create unit.'))
  }
  return response.json() as Promise<UnitEntity>
}

export async function updateUnit(unitId: string, data: UnitUpdateInput): Promise<UnitEntity> {
  const response = await authenticatedFetch(`/api/v1/units/${unitId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to update unit.'))
  }
  return response.json() as Promise<UnitEntity>
}

export async function deleteUnit(unitId: string): Promise<void> {
  const response = await authenticatedFetch(`/api/v1/units/${unitId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to delete unit.'))
  }
}

export async function fetchLessonsByUnit(unitId: string): Promise<LessonEntity[]> {
  const response = await authenticatedFetch(`/api/v1/lessons/by-unit/${unitId}`)
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to fetch lessons.'))
  }
  return response.json() as Promise<LessonEntity[]>
}

export async function fetchLessonDetails(lessonId: string): Promise<LessonEntity> {
  const response = await authenticatedFetch(`/api/v1/lessons/${lessonId}`)
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to fetch lesson details.'))
  }
  return response.json() as Promise<LessonEntity>
}

export async function createLesson(unitId: string, data: LessonCreateInput): Promise<LessonEntity> {
  const response = await authenticatedFetch(`/api/v1/lessons/for-unit/${unitId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to create lesson.'))
  }
  return response.json() as Promise<LessonEntity>
}

export async function updateLesson(
  lessonId: string,
  data: LessonUpdateInput,
): Promise<LessonEntity> {
  const response = await authenticatedFetch(`/api/v1/lessons/${lessonId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to update lesson.'))
  }
  return response.json() as Promise<LessonEntity>
}

export async function publishLesson(lessonId: string): Promise<LessonEntity> {
  const response = await authenticatedFetch(`/api/v1/lessons/${lessonId}/publish`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to publish lesson.'))
  }
  return response.json() as Promise<LessonEntity>
}

export async function deleteLesson(lessonId: string): Promise<void> {
  const response = await authenticatedFetch(`/api/v1/lessons/${lessonId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to delete lesson.'))
  }
}

export async function fetchExercisesByLesson(lessonId: string): Promise<ExerciseEntity[]> {
  const response = await authenticatedFetch(`/api/v1/exercises/by-lesson/${lessonId}/full`)
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to fetch exercises for lesson.'))
  }
  return response.json() as Promise<ExerciseEntity[]>
}

export async function createExercise(
  lessonId: string,
  data: ExerciseCreateInput,
): Promise<ExerciseEntity> {
  const response = await authenticatedFetch(`/api/v1/exercises/for-lesson/${lessonId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to create exercise.'))
  }
  return response.json() as Promise<ExerciseEntity>
}

export async function updateExercise(
  exerciseId: string,
  data: ExerciseUpdateInput,
): Promise<ExerciseEntity> {
  const response = await authenticatedFetch(`/api/v1/exercises/${exerciseId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to update exercise.'))
  }
  return response.json() as Promise<ExerciseEntity>
}

export async function deleteExercise(exerciseId: string): Promise<void> {
  const response = await authenticatedFetch(`/api/v1/exercises/${exerciseId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to delete exercise.'))
  }
}

export async function validateExerciseAnswer(
  exerciseId: string,
  submittedAnswer: string,
): Promise<ValidationResultResponse> {
  const response = await authenticatedFetch(`/api/v1/exercises/${exerciseId}/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ submittedAnswer }),
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to validate answer.'))
  }
  return response.json() as Promise<ValidationResultResponse>
}

export type ExerciseType = 'single' | 'sentence'
export type Difficulty = 'beginner' | 'intermediate' | 'advanced'
export type ContentStatus = 'draft' | 'published' | 'archived'

export type MediaAsset = {
  id?: string
  exerciseId?: string
  type: 'video' | 'image'
  url: string
}

export type ExerciseEntity = {
  id: string
  lessonId: string
  type: ExerciseType
  difficulty: Difficulty
  points: number
  content: string
  answer: string
  media?: MediaAsset[]
}

export type ExerciseCreateInput = {
  type: ExerciseType
  difficulty: Difficulty
  points: number
  content: string
  answer: string
  media?: Array<{ type: 'video' | 'image'; url: string }>
}

export type ExerciseUpdateInput = {
  type: ExerciseType
  difficulty: Difficulty
  points: number
  content: string
  answer: string
  media?: Array<{ type: 'video' | 'image'; url: string }>
}

export type ValidationResultResponse = {
  isCorrect: boolean
  earnedPoints: number
  expectedAnswer: string
  feedback: string
}

export type LessonEntity = {
  id: string
  unitId: string
  title: string
  description: string
  order: number
  status: ContentStatus
  exercises?: ExerciseEntity[]
}

export type LessonCreateInput = {
  title: string
  description?: string
  order?: number
}

export type LessonUpdateInput = {
  title: string
  description?: string
  order?: number
}

export type UnitEntity = {
  id: string
  title: string
  order: number
  lessons?: LessonEntity[]
}

export type UnitCreateInput = {
  title: string
  order?: number
}

export type UnitUpdateInput = {
  title: string
  order?: number
}

export type PosesSource = 'model-service' | 'lessons.ts'

export type AvailablePosesResponse = {
  poses: string[]
  source: PosesSource
}

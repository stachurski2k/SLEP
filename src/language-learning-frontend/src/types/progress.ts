export type UserProgress = {
  id: string
  userId: string
  xp: number
  createdAt: string
  updatedAt: string
}

export type LessonProgress = {
  id: string
  userId: string
  lessonId: string
  completed: boolean
  attempts: number
  completedAt?: string | null
  lastAttemptAt?: string | null
}

export type LessonCompletionResult = {
  lessonId: string
  isFirstCompletion: boolean
  earnedXp: number
  totalXp: number
  completedAt: string
}

export type ProgressSummary = {
  userId: string
  totalXp: number
  completedLessonsCount: number
  completedLessonIds: string[]
}

export type DailyActivity = {
  id: string
  userId: string
  date: string
  xpEarned: number
  lessonsCompleted: number
}

export type WeeklyDayActivity = {
  date: string
  xpEarned: number
  lessonsCompleted: number
  dayOfWeek: string
}

export type WeeklyReport = {
  userId: string
  startDate: string
  endDate: string
  totalXp: number
  lessonsCompleted: number
  activeDaysCount: number
  dailyBreakdown: WeeklyDayActivity[]
  averageDailyXp: number
}

export type LearningStatistics = {
  userId: string
  totalXp: number
  completedLessons: number
  completedUnits: number
  averageAccuracy: number
  activeDaysCount: number
}

export type RecordActivityInput = {
  xp?: number
  lessonsCompleted?: number
  activityDate?: string
}

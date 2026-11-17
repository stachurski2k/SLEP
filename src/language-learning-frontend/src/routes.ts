export const routes = {
  login: '/login',
  lessons: '/lessons',
  lesson: '/lessons/:lessonId',
} as const

export function getLessonPath(lessonId: string) {
  return `/lessons/${lessonId}`
}

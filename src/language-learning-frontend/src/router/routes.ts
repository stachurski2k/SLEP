export const routes = {
  login: '/login',
  register: '/register',
  lessons: '/lessons',
  lesson: '/lessons/:lessonId',
  statistics: '/statistics',
  admin: '/admin',
} as const

export function getLessonPath(lessonId: string) {
  return `/lessons/${lessonId}`
}

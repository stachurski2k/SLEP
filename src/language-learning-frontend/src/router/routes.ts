export const routes = {
  login: '/login',
  register: '/register',
  lessons: '/lessons',
  lesson: '/lessons/:lessonId',
} as const

export function getLessonPath(lessonId: string) {
  return `/lessons/${lessonId}`
}

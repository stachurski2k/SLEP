import { useNavigate } from 'react-router'
import { lessons } from '../lesson'
import { getLessonPath } from '../routes'
import { panelClass, primaryButtonClass } from '../ui/classes'

export default function LessonsPage() {
  const navigate = useNavigate()
  return (
    <section className="mx-auto w-full max-w-6xl py-2">
      <h2 className="m-0 text-3xl font-semibold tracking-tight text-white">Lessons</h2>
      <p className="mt-3 mb-0 text-[#a8b0c3]">
        {lessons.length} lessons · {lessons.reduce((total, lesson) => total + lesson.signs.length, 0)} signs to practice
      </p>
      <div className="mt-6 grid grid-cols-1 gap-4 sm:mt-8">
        {lessons.map((lesson) => (
          <article key={lesson.id} className={`${panelClass} flex flex-col gap-4 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6`}>
            <div className="min-w-0">
              <p className="m-0 text-sm font-medium text-[#64d7bd]">Lesson {lesson.id} · {lesson.signs.length} signs</p>
              <h3 className="mt-1 mb-0 text-xl font-semibold text-white">{lesson.title}</h3>
              <p className="mt-2 mb-0 text-sm leading-relaxed text-[#a8b0c3]">{lesson.signs.join(' · ')}</p>
            </div>
            <button
              type="button"
              className={`${primaryButtonClass} w-full shrink-0 sm:w-auto`}
              onClick={() => navigate(getLessonPath(lesson.id))}
              aria-label={`Start lesson ${lesson.id}: ${lesson.title}`}
            >
              Start lesson
            </button>
          </article>
        ))}
      </div>
    </section>
  )
}

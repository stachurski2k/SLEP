import { useNavigate } from 'react-router'
import { lessonSigns } from '../lesson'
import { routes } from '../routes'
import { panelClass, primaryButtonClass } from '../ui/classes'

export default function LessonsPage() {
  const navigate = useNavigate()
  return (
    <section className="mx-auto w-full max-w-6xl py-2">
      <h2 className="m-0 text-3xl font-semibold tracking-tight text-white">Lessons</h2>
      <article className={`${panelClass} mt-6 flex flex-col gap-6 p-6 sm:mt-8 sm:flex-row sm:items-center sm:justify-between sm:p-8`}>
        <div>
          <p className="m-0 text-sm font-medium text-[#a8b0c3]">Lesson 1 · Basics</p>
          <h3 className="mt-2 mb-0 text-2xl font-semibold text-white">{lessonSigns.join(' · ')}</h3>
        </div>
        <button
          type="button"
          className={`${primaryButtonClass} w-full shrink-0 sm:w-auto`}
          onClick={() => navigate(routes.lesson)}
        >
          Start lesson
        </button>
      </article>
    </section>
  )
}

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { fetchUnits } from '../../api/learning'
import { panelClass, primaryButtonClass } from '../../components/ui/classes'
import { lessons as staticLessons } from '../../data/lessons'
import { getLessonPath } from '../../router/routes'
import type { UnitEntity } from '../../types/learning'

export default function LessonsPage() {
  const navigate = useNavigate()
  const [units, setUnits] = useState<UnitEntity[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let isMounted = true

    const loadUnits = async () => {
      try {
        const data = await fetchUnits()
        if (isMounted) {
          setUnits(data)
        }
      } catch {
        // Fallback silently to static lessons
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void loadUnits()
    return () => {
      isMounted = false
    }
  }, [])

  const totalDynamicLessons = units.reduce(
    (total, unit) => total + (unit.lessons?.length || 0),
    0,
  )

  const hasDynamicContent = units.length > 0 && totalDynamicLessons > 0

  return (
    <section className="mx-auto w-full max-w-6xl py-2">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="m-0 text-3xl font-semibold tracking-tight text-white">
            Sign Language Lessons
          </h2>
          <p className="mt-1 mb-0 text-sm text-[#a8b0c3]">
            {hasDynamicContent
              ? `${units.length} units · ${totalDynamicLessons} lessons to practice`
              : `${staticLessons.length} lessons · ${staticLessons.reduce((total, lesson) => total + lesson.signs.length, 0)} demo signs to practice`}
          </p>
        </div>

        {hasDynamicContent && (
          <span className="inline-flex w-fit items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
            <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
            Active Course Units
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="flex min-h-[300px] items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <span className="size-10 animate-spin rounded-full border-4 border-emerald-400 border-t-transparent" />
            <p className="text-sm text-[#a8b0c3]">Loading units and lessons...</p>
          </div>
        </div>
      ) : hasDynamicContent ? (
        <div className="mt-6 flex flex-col gap-8 sm:mt-8">
          {units.map((unit) => (
            <div key={unit.id} className="flex flex-col gap-3">
              {/* Unit header */}
              <div className="flex items-center justify-between border-b border-slate-400/15 pb-2">
                <div className="flex items-center gap-2.5">
                  <span className="rounded-lg bg-emerald-500/20 px-2.5 py-0.5 text-xs font-bold text-emerald-300">
                    Unit {unit.order}
                  </span>
                  <h3 className="m-0 text-xl font-bold tracking-tight text-white">{unit.title}</h3>
                </div>
                <span className="text-xs font-medium text-[#738099]">
                  {unit.lessons?.length || 0} {unit.lessons?.length === 1 ? 'lesson' : 'lessons'}
                </span>
              </div>

              {/* Lessons grid in unit */}
              {(!unit.lessons || unit.lessons.length === 0) ? (
                <div className={`${panelClass} p-4 text-center text-sm text-[#738099]`}>
                  No lessons created in this unit yet.
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {unit.lessons.map((lesson) => (
                    <article
                      key={lesson.id}
                      className={`${panelClass} flex flex-col justify-between gap-4 p-5 transition hover:border-emerald-500/30`}
                    >
                      <div className="min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-semibold text-[#64d7bd]">
                            Lesson {lesson.order}
                          </span>
                          <span
                            className={`rounded-full px-2 py-0.5 text-[0.68rem] font-semibold tracking-wide uppercase ${
                              lesson.status === 'published'
                                ? 'bg-emerald-500/15 text-emerald-300'
                                : 'bg-amber-500/15 text-amber-300'
                            }`}
                          >
                            {lesson.status === 'published' ? 'Published' : 'Draft'}
                          </span>
                        </div>
                        <h4 className="mt-1.5 mb-0 text-lg font-semibold text-white">
                          {lesson.title}
                        </h4>
                        {lesson.description && (
                          <p className="mt-2 mb-0 line-clamp-2 text-xs leading-relaxed text-[#a8b0c3]">
                            {lesson.description}
                          </p>
                        )}
                      </div>

                      <div className="pt-2">
                        <button
                          type="button"
                          className={`${primaryButtonClass} w-full text-sm`}
                          onClick={() => navigate(getLessonPath(lesson.id))}
                          aria-label={`Start lesson ${lesson.order}: ${lesson.title}`}
                        >
                          Start lesson
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        /* Fallback to demo lessons when database has no units */
        <div className="mt-6 sm:mt-8">
          <div className="mb-4 rounded-xl border border-sky-400/20 bg-sky-500/10 px-4 py-3 text-xs text-sky-200">
            ℹ️ No custom units found in database. Displaying standard demo lessons.
          </div>
          <div className="grid grid-cols-1 gap-4">
            {staticLessons.map((lesson) => (
              <article
                key={lesson.id}
                className={`${panelClass} flex flex-col gap-4 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6`}
              >
                <div className="min-w-0">
                  <p className="m-0 text-sm font-medium text-[#64d7bd]">
                    Lesson {lesson.id} · {lesson.signs.length} signs
                  </p>
                  <h3 className="mt-1 mb-0 text-xl font-semibold text-white">{lesson.title}</h3>
                  <p className="mt-2 mb-0 text-sm leading-relaxed text-[#a8b0c3]">
                    {lesson.signs.join(' · ')}
                  </p>
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
        </div>
      )}
    </section>
  )
}

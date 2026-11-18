import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'
import { fetchUnits } from '../../api/learning'
import { fetchProgressSummary } from '../../api/progress'
import { panelClass, primaryButtonClass } from '../../components/ui/classes'
import { lessons as staticLessons } from '../../data/lessons'
import { getLessonPath, routes } from '../../router/routes'
import type { UnitEntity } from '../../types/learning'
import type { ProgressSummary } from '../../types/progress'

export default function LessonsPage() {
  const navigate = useNavigate()
  const [units, setUnits] = useState<UnitEntity[]>([])
  const [progress, setProgress] = useState<ProgressSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let isMounted = true

    const loadData = async () => {
      try {
        const [unitsData, progressData] = await Promise.all([
          fetchUnits().catch(() => [] as UnitEntity[]),
          fetchProgressSummary().catch(() => null),
        ])
        if (isMounted) {
          setUnits(unitsData)
          setProgress(progressData)
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void loadData()
    return () => {
      isMounted = false
    }
  }, [])

  const completedSet = useMemo(
    () => new Set(progress?.completedLessonIds || []),
    [progress?.completedLessonIds],
  )

  const totalDynamicLessons = units.reduce(
    (total, unit) => total + (unit.lessons?.length || 0),
    0,
  )

  const completedDynamicLessons = useMemo(() => {
    if (units.length === 0) return 0
    return units.reduce(
      (acc, unit) =>
        acc + (unit.lessons || []).filter((l) => completedSet.has(l.id)).length,
      0,
    )
  }, [units, completedSet])

  const hasDynamicContent = units.length > 0 && totalDynamicLessons > 0
  const overallPercent =
    totalDynamicLessons > 0
      ? Math.round((completedDynamicLessons / totalDynamicLessons) * 100)
      : 0

  return (
    <section className="mx-auto w-full max-w-6xl py-2">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
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

        <div className="flex flex-wrap items-center gap-2.5">
          {progress && (
            <div className="inline-flex items-center gap-2 rounded-xl border border-amber-400/30 bg-amber-500/10 px-3.5 py-1.5 text-xs font-bold text-amber-300">
              <span>⚡ {progress.totalXp} XP</span>
            </div>
          )}

          <button
            type="button"
            onClick={() => navigate(routes.statistics)}
            className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl border border-slate-400/20 bg-slate-400/5 px-3.5 py-1.5 text-xs font-semibold text-slate-200 transition hover:border-emerald-300/40 hover:text-white"
          >
            <span>📊 View Statistics</span>
          </button>

          {hasDynamicContent && (
            <span className="inline-flex w-fit items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300">
              <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
              Active Course Units
            </span>
          )}
        </div>
      </div>

      {/* Overall Course Progress Card */}
      {!isLoading && hasDynamicContent && (
        <div className={`${panelClass} mt-6 flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between`}>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between text-xs font-semibold">
              <span className="text-emerald-300 uppercase tracking-wider">Overall Course Progress</span>
              <span className="text-white">
                {completedDynamicLessons} / {totalDynamicLessons} lessons ({overallPercent}%)
              </span>
            </div>
            <div className="mt-2 h-2.5 w-full overflow-hidden rounded-full bg-slate-400/10">
              <div
                className="h-full rounded-full bg-[linear-gradient(90deg,#38c8a6,#4c78ff)] transition-[width] duration-500"
                style={{ width: `${overallPercent}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="flex min-h-[300px] items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <span className="size-10 animate-spin rounded-full border-4 border-emerald-400 border-t-transparent" />
            <p className="text-sm text-[#a8b0c3]">Loading units and lessons...</p>
          </div>
        </div>
      ) : hasDynamicContent ? (
        <div className="mt-6 flex flex-col gap-8 sm:mt-8">
          {units.map((unit) => {
            const unitLessons = unit.lessons || []
            const unitCompleted = unitLessons.filter((l) => completedSet.has(l.id)).length
            const isUnitDone = unitLessons.length > 0 && unitCompleted === unitLessons.length

            return (
              <div key={unit.id} className="flex flex-col gap-3">
                {/* Unit header */}
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-400/15 pb-2">
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`rounded-lg px-2.5 py-0.5 text-xs font-bold ${
                        isUnitDone
                          ? 'bg-emerald-400 text-black'
                          : 'bg-emerald-500/20 text-emerald-300'
                      }`}
                    >
                      {isUnitDone ? '✓ ' : ''}Unit {unit.order}
                    </span>
                    <h3 className="m-0 text-xl font-bold tracking-tight text-white">
                      {unit.title}
                    </h3>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-medium text-[#a8b0c3]">
                      {unitCompleted} / {unitLessons.length}{' '}
                      {unitLessons.length === 1 ? 'lesson' : 'lessons'} completed
                    </span>
                  </div>
                </div>

                {/* Lessons grid in unit */}
                {unitLessons.length === 0 ? (
                  <div className={`${panelClass} p-4 text-center text-sm text-[#738099]`}>
                    No lessons created in this unit yet.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {unitLessons.map((lesson) => {
                      const isCompleted = completedSet.has(lesson.id)
                      return (
                        <article
                          key={lesson.id}
                          className={`${panelClass} flex flex-col justify-between gap-4 p-5 transition hover:border-emerald-500/30 ${
                            isCompleted ? 'border-emerald-400/25' : ''
                          }`}
                        >
                          <div className="min-w-0">
                            <div className="flex items-center justify-between gap-2">
                              <span className="text-xs font-semibold text-[#64d7bd]">
                                Lesson {lesson.order}
                              </span>
                              <div className="flex items-center gap-1.5">
                                {isCompleted && (
                                  <span className="rounded-full border border-emerald-400/40 bg-emerald-500/20 px-2.5 py-0.5 text-[0.68rem] font-bold tracking-wide text-emerald-300 uppercase">
                                    ✓ Completed
                                  </span>
                                )}
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
                              aria-label={`${isCompleted ? 'Practice again' : 'Start'} lesson ${lesson.order}: ${lesson.title}`}
                            >
                              {isCompleted ? 'Practice again' : 'Start lesson'}
                            </button>
                          </div>
                        </article>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
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

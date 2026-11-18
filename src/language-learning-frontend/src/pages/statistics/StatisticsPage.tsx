import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { fetchLearningStatistics, fetchWeeklyReport } from '../../api/statistics'
import { panelClass } from '../../components/ui/classes'
import type { LearningStatistics, WeeklyReport } from '../../types/progress'

type ChartMetric = 'xp' | 'lessons'

function formatDateParam(d: Date): string {
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatReadableDateRange(startIso: string, endIso: string): string {
  try {
    const start = new Date(`${startIso}T00:00:00`)
    const end = new Date(`${endIso}T00:00:00`)
    const opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric', year: 'numeric' }
    return `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} – ${end.toLocaleDateString('en-US', opts)}`
  } catch {
    return `${startIso} – ${endIso}`
  }
}

export default function StatisticsPage() {
  const [stats, setStats] = useState<LearningStatistics | null>(null)
  const [weeklyReport, setWeeklyReport] = useState<WeeklyReport | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isWeekLoading, setIsWeekLoading] = useState(false)
  const [weekOffset, setWeekOffset] = useState(0)
  const [chartMetric, setChartMetric] = useState<ChartMetric>('xp')

  const todayIso = useMemo(() => formatDateParam(new Date()), [])

  const targetDateIso = useMemo(() => {
    const d = new Date()
    d.setDate(d.getDate() + weekOffset * 7)
    return formatDateParam(d)
  }, [weekOffset])

  useEffect(() => {
    let isMounted = true

    const loadStats = async () => {
      try {
        const statsData = await fetchLearningStatistics()
        if (isMounted) {
          setStats(statsData)
        }
      } catch (err) {
        if (isMounted) {
          toast.error(err instanceof Error ? err.message : 'Failed to load learning statistics.')
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void loadStats()
    return () => {
      isMounted = false
    }
  }, [])

  useEffect(() => {
    let isMounted = true

    const loadWeekly = async () => {
      try {
        const reportData = await fetchWeeklyReport(targetDateIso)
        if (isMounted) {
          setWeeklyReport(reportData)
        }
      } catch (err) {
        if (isMounted) {
          toast.error(err instanceof Error ? err.message : 'Failed to load weekly activity report.')
        }
      } finally {
        if (isMounted) {
          setIsWeekLoading(false)
        }
      }
    }

    void loadWeekly()
    return () => {
      isMounted = false
    }
  }, [targetDateIso])

  const handleChangeWeek = (nextOffset: number) => {
    setIsWeekLoading(true)
    setWeekOffset(nextOffset)
  }

  const breakdown = useMemo(
    () => weeklyReport?.dailyBreakdown || [],
    [weeklyReport?.dailyBreakdown],
  )

  const maxMetricValue = useMemo(() => {
    if (breakdown.length === 0) return 10
    const values = breakdown.map((day) =>
      chartMetric === 'xp' ? day.xpEarned : day.lessonsCompleted,
    )
    const maxVal = Math.max(...values, 0)
    return maxVal > 0 ? maxVal : chartMetric === 'xp' ? 20 : 3
  }, [breakdown, chartMetric])

  return (
    <section className="mx-auto w-full max-w-5xl py-2">
      <div>
        <h2 className="m-0 text-2xl font-semibold tracking-tight text-white">Statistics</h2>
        <p className="mt-1 mb-0 text-sm text-[#a8b0c3]">
          Weekly activity and overall learning metrics.
        </p>
      </div>

      {isLoading ? (
        <div className="flex min-h-[280px] items-center justify-center">
          <span className="size-8 animate-spin rounded-full border-3 border-emerald-400 border-t-transparent" />
        </div>
      ) : (
        <>
          {/* Weekly Activity Chart */}
          <div className={`${panelClass} mt-6 p-6`}>
            <div className="flex flex-col gap-4 border-b border-slate-400/15 pb-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="flex items-center gap-2.5">
                  <h3 className="m-0 text-base font-semibold text-white">Weekly Activity</h3>
                  {isWeekLoading && (
                    <span className="size-3.5 animate-spin rounded-full border-2 border-emerald-400 border-t-transparent" />
                  )}
                </div>
                <p className="mt-0.5 mb-0 text-xs text-[#738099]">
                  {weeklyReport
                    ? formatReadableDateRange(weeklyReport.startDate, weeklyReport.endDate)
                    : '7-day breakdown'}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2.5">
                <div className="inline-flex rounded-xl border border-slate-400/15 bg-[#080c12] p-1">
                  <button
                    type="button"
                    onClick={() => setChartMetric('xp')}
                    className={`cursor-pointer rounded-lg px-3 py-1 text-xs font-medium transition ${
                      chartMetric === 'xp'
                        ? 'bg-emerald-400/20 text-emerald-300'
                        : 'text-[#738099] hover:text-white'
                    }`}
                  >
                    XP
                  </button>
                  <button
                    type="button"
                    onClick={() => setChartMetric('lessons')}
                    className={`cursor-pointer rounded-lg px-3 py-1 text-xs font-medium transition ${
                      chartMetric === 'lessons'
                        ? 'bg-sky-400/20 text-sky-300'
                        : 'text-[#738099] hover:text-white'
                    }`}
                  >
                    Lessons
                  </button>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => handleChangeWeek(weekOffset - 1)}
                    className="cursor-pointer rounded-lg border border-slate-400/15 bg-slate-400/5 px-2.5 py-1 text-xs text-[#a8b0c3] transition hover:border-slate-400/30 hover:text-white"
                  >
                    Prev
                  </button>
                  <button
                    type="button"
                    disabled={weekOffset === 0}
                    onClick={() => handleChangeWeek(0)}
                    className="cursor-pointer rounded-lg border border-slate-400/15 bg-slate-400/5 px-2.5 py-1 text-xs text-[#a8b0c3] transition hover:border-slate-400/30 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Current
                  </button>
                  <button
                    type="button"
                    disabled={weekOffset >= 0}
                    onClick={() => handleChangeWeek(weekOffset + 1)}
                    className="cursor-pointer rounded-lg border border-slate-400/15 bg-slate-400/5 px-2.5 py-1 text-xs text-[#a8b0c3] transition hover:border-slate-400/30 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>

            {/* Bars Only */}
            <div className="mt-6 grid h-56 grid-cols-7 items-end gap-2 pt-6 sm:gap-4">
              {breakdown.map((day) => {
                const value = chartMetric === 'xp' ? day.xpEarned : day.lessonsCompleted
                const heightPercent = Math.round((value / maxMetricValue) * 100)
                const barHeight = value > 0 ? Math.max(heightPercent, 8) : 4
                const isToday = day.date === todayIso

                return (
                  <div
                    key={day.date}
                    className="flex h-full flex-col items-center justify-end"
                  >
                    <span
                      className={`mb-2 text-xs font-medium ${
                        value > 0 ? 'text-white' : 'text-slate-600'
                      }`}
                    >
                      {value}
                    </span>

                    <div className="relative flex h-40 w-full max-w-[44px] items-end justify-center rounded-t-lg bg-slate-800/30 p-1">
                      <div
                        className={`w-full rounded-t-md transition-all duration-500 ${
                          value > 0
                            ? chartMetric === 'xp'
                              ? 'bg-emerald-400/80'
                              : 'bg-sky-400/80'
                            : 'bg-slate-700/30'
                        }`}
                        style={{ height: `${barHeight}%` }}
                        title={`${day.dayOfWeek} (${day.date}): ${value}`}
                      />
                    </div>

                    <span
                      className={`mt-2 text-xs ${
                        isToday ? 'font-semibold text-emerald-300' : 'text-[#738099]'
                      }`}
                    >
                      {day.dayOfWeek.slice(0, 3)}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Minimalist Statistics Cards Below Chart */}
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className={`${panelClass} p-5`}>
              <span className="text-xs font-medium text-[#738099]">Total XP</span>
              <p className="mt-2 mb-0 text-2xl font-semibold text-white">
                {stats?.totalXp ?? 0}
              </p>
              <p className="mt-1.5 mb-0 text-xs text-[#a8b0c3]">
                Points earned from completed lessons.
              </p>
            </div>

            <div className={`${panelClass} p-5`}>
              <span className="text-xs font-medium text-[#738099]">Lessons Completed</span>
              <p className="mt-2 mb-0 text-2xl font-semibold text-white">
                {stats?.completedLessons ?? 0}
              </p>
              <p className="mt-1.5 mb-0 text-xs text-[#a8b0c3]">
                Finished lessons across all units.
              </p>
            </div>

            <div className={`${panelClass} p-5`}>
              <span className="text-xs font-medium text-[#738099]">Completion Rate</span>
              <p className="mt-2 mb-0 text-2xl font-semibold text-white">
                {stats?.averageAccuracy ?? 0}%
              </p>
              <p className="mt-1.5 mb-0 text-xs text-[#a8b0c3]">
                Ratio of completed lessons to attempts.
              </p>
            </div>

            <div className={`${panelClass} p-5`}>
              <span className="text-xs font-medium text-[#738099]">Active Days</span>
              <p className="mt-2 mb-0 text-2xl font-semibold text-white">
                {stats?.activeDaysCount ?? 0}
              </p>
              <p className="mt-1.5 mb-0 text-xs text-[#a8b0c3]">
                Days with recorded practice activity.
              </p>
            </div>
          </div>
        </>
      )}
    </section>
  )
}

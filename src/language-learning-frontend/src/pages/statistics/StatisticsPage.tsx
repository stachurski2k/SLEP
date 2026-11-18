import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { fetchLearningStatistics, fetchWeeklyReport } from '../../api/statistics'
import { panelClass, primaryButtonClass } from '../../components/ui/classes'
import { routes } from '../../router/routes'
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
  const navigate = useNavigate()
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

  // Load initial overall statistics
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

  // Load weekly report whenever targetDateIso changes
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
    <section className="mx-auto w-full max-w-6xl py-2">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="m-0 text-3xl font-semibold tracking-tight text-white">
            Learning Statistics & Activity
          </h2>
          <p className="mt-1 mb-0 text-sm text-[#a8b0c3]">
            Track your sign language progress, earned experience points, accuracy, and daily consistency.
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate(routes.lessons)}
          className={`${primaryButtonClass} !min-h-10 w-fit text-sm`}
        >
          Practice Lessons →
        </button>
      </div>

      {isLoading ? (
        <div className="flex min-h-[320px] items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <span className="size-10 animate-spin rounded-full border-4 border-emerald-400 border-t-transparent" />
            <p className="text-sm text-[#a8b0c3]">Loading your statistics...</p>
          </div>
        </div>
      ) : (
        <>
          {/* KPI Summary Cards */}
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {/* Total XP */}
            <div className={`${panelClass} flex flex-col justify-between p-5`}>
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold tracking-wider text-amber-300 uppercase">
                    Total XP
                  </span>
                  <span className="grid size-8 place-items-center rounded-lg bg-amber-400/15 text-base text-amber-300">
                    ⚡
                  </span>
                </div>
                <p className="mt-3 mb-0 text-3xl font-bold text-white">
                  {stats?.totalXp ?? 0}
                </p>
              </div>
              <p className="mt-2 mb-0 text-xs leading-relaxed text-[#738099]">
                Cumulative experience points earned from first-time lesson completions.
              </p>
            </div>

            {/* Completed Lessons */}
            <div className={`${panelClass} flex flex-col justify-between p-5`}>
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold tracking-wider text-emerald-300 uppercase">
                    Lessons Done
                  </span>
                  <span className="grid size-8 place-items-center rounded-lg bg-emerald-400/15 text-base text-emerald-300">
                    ✓
                  </span>
                </div>
                <p className="mt-3 mb-0 text-3xl font-bold text-white">
                  {stats?.completedLessons ?? 0}
                </p>
              </div>
              <p className="mt-2 mb-0 text-xs leading-relaxed text-[#738099]">
                Distinct sign language lessons completed across all course units.
              </p>
            </div>

            {/* Completed Units */}
            <div className={`${panelClass} flex flex-col justify-between p-5`}>
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold tracking-wider text-sky-300 uppercase">
                    Units Mastered
                  </span>
                  <span className="grid size-8 place-items-center rounded-lg bg-sky-400/15 text-base text-sky-300">
                    🏆
                  </span>
                </div>
                <p className="mt-3 mb-0 text-3xl font-bold text-white">
                  {stats?.completedUnits ?? 0}
                </p>
              </div>
              <p className="mt-2 mb-0 text-xs leading-relaxed text-[#738099]">
                Course modules where 100% of assigned lessons have been completed.
              </p>
            </div>

            {/* Average Accuracy */}
            <div className={`${panelClass} flex flex-col justify-between p-5`}>
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold tracking-wider text-purple-300 uppercase">
                    Completion Rate
                  </span>
                  <span className="grid size-8 place-items-center rounded-lg bg-purple-400/15 text-base text-purple-300">
                    🎯
                  </span>
                </div>
                <p className="mt-3 mb-0 text-3xl font-bold text-white">
                  {stats?.averageAccuracy ?? 0}%
                </p>
              </div>
              <p className="mt-2 mb-0 text-xs leading-relaxed text-[#738099]">
                Ratio of completed lessons to total started lesson attempts.
              </p>
            </div>

            {/* Active Days */}
            <div className={`${panelClass} flex flex-col justify-between p-5`}>
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold tracking-wider text-rose-300 uppercase">
                    Active Days
                  </span>
                  <span className="grid size-8 place-items-center rounded-lg bg-rose-400/15 text-base text-rose-300">
                    🔥
                  </span>
                </div>
                <p className="mt-3 mb-0 text-3xl font-bold text-white">
                  {stats?.activeDaysCount ?? 0}
                </p>
              </div>
              <p className="mt-2 mb-0 text-xs leading-relaxed text-[#738099]">
                Total calendar days on which you completed lessons and earned XP.
              </p>
            </div>
          </div>

          {/* Weekly Activity Chart Panel */}
          <div className={`${panelClass} mt-6 p-6`}>
            <div className="flex flex-col gap-4 border-b border-slate-400/15 pb-5 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div className="flex items-center gap-2.5">
                  <h3 className="m-0 text-xl font-bold text-white">Weekly Activity Breakdown</h3>
                  {isWeekLoading && (
                    <span className="size-4 animate-spin rounded-full border-2 border-emerald-400 border-t-transparent" />
                  )}
                </div>
                <p className="mt-1 mb-0 text-xs text-[#a8b0c3]">
                  {weeklyReport
                    ? `Week of ${formatReadableDateRange(weeklyReport.startDate, weeklyReport.endDate)}`
                    : '7-day learning performance'}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                {/* Metric Switcher */}
                <div className="inline-flex rounded-xl border border-slate-400/20 bg-[#080c12] p-1">
                  <button
                    type="button"
                    onClick={() => setChartMetric('xp')}
                    className={`cursor-pointer rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                      chartMetric === 'xp'
                        ? 'bg-emerald-400 text-black'
                        : 'text-[#a8b0c3] hover:text-white'
                    }`}
                  >
                    ⚡ XP Earned
                  </button>
                  <button
                    type="button"
                    onClick={() => setChartMetric('lessons')}
                    className={`cursor-pointer rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                      chartMetric === 'lessons'
                        ? 'bg-sky-400 text-black'
                        : 'text-[#a8b0c3] hover:text-white'
                    }`}
                  >
                    ✓ Lessons Completed
                  </button>
                </div>

                {/* Week Navigation */}
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => handleChangeWeek(weekOffset - 1)}
                    className="cursor-pointer rounded-xl border border-slate-400/20 bg-slate-400/5 px-3 py-1.5 text-xs font-semibold text-slate-200 transition hover:border-emerald-400/40 hover:text-white"
                    title="Previous week"
                  >
                    ← Prev
                  </button>
                  <button
                    type="button"
                    disabled={weekOffset === 0}
                    onClick={() => handleChangeWeek(0)}
                    className="cursor-pointer rounded-xl border border-slate-400/20 bg-slate-400/5 px-3 py-1.5 text-xs font-semibold text-slate-200 transition hover:border-emerald-400/40 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    This Week
                  </button>
                  <button
                    type="button"
                    disabled={weekOffset >= 0}
                    onClick={() => handleChangeWeek(weekOffset + 1)}
                    className="cursor-pointer rounded-xl border border-slate-400/20 bg-slate-400/5 px-3 py-1.5 text-xs font-semibold text-slate-200 transition hover:border-emerald-400/40 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                    title="Next week"
                  >
                    Next →
                  </button>
                </div>
              </div>
            </div>

            {/* 7-Day Bar Chart */}
            <div className="mt-6">
              <div className="grid h-64 grid-cols-7 items-end gap-2 border-b border-slate-400/15 pt-8 pb-3 sm:gap-4">
                {breakdown.map((day) => {
                  const value = chartMetric === 'xp' ? day.xpEarned : day.lessonsCompleted
                  const heightPercent = Math.round((value / maxMetricValue) * 100)
                  const barHeight = value > 0 ? Math.max(heightPercent, 10) : 4
                  const isToday = day.date === todayIso

                  return (
                    <div
                      key={day.date}
                      className="group flex h-full flex-col items-center justify-end"
                    >
                      {/* Value label above bar */}
                      <div className="mb-2 text-center">
                        <span
                          className={`text-xs font-bold ${
                            value > 0
                              ? chartMetric === 'xp'
                                ? 'text-emerald-300'
                                : 'text-sky-300'
                              : 'text-slate-600'
                          }`}
                        >
                          {value}
                          {chartMetric === 'xp' ? ' XP' : ''}
                        </span>
                      </div>

                      {/* Bar track */}
                      <div className="relative flex h-44 w-full max-w-[54px] items-end justify-center rounded-t-xl bg-slate-800/35 p-1">
                        <div
                          className={`w-full rounded-t-lg transition-all duration-500 ${
                            value > 0
                              ? chartMetric === 'xp'
                                ? 'bg-[linear-gradient(180deg,#39d5ab,#209978)] shadow-[0_0_20px_rgba(57,213,171,0.3)]'
                                : 'bg-[linear-gradient(180deg,#38bdf8,#2563eb)] shadow-[0_0_20px_rgba(56,189,248,0.3)]'
                              : 'bg-slate-700/40'
                          }`}
                          style={{ height: `${barHeight}%` }}
                          title={`${day.dayOfWeek} (${day.date}): ${day.xpEarned} XP, ${day.lessonsCompleted} lessons`}
                        />
                      </div>

                      {/* Day label */}
                      <div className="mt-2.5 flex flex-col items-center">
                        <span
                          className={`text-xs font-semibold ${
                            isToday ? 'text-emerald-300' : 'text-white'
                          }`}
                        >
                          {day.dayOfWeek.slice(0, 3)}
                        </span>
                        <span className="text-[0.68rem] text-[#738099]">
                          {day.date.slice(5)}
                        </span>
                        {isToday && (
                          <span className="mt-0.5 rounded bg-emerald-500/20 px-1.5 py-0.2 text-[0.6rem] font-bold text-emerald-300 uppercase">
                            Today
                          </span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Weekly Summary Footer */}
              <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="rounded-xl border border-slate-400/15 bg-white/[0.02] p-3.5">
                  <span className="text-[0.7rem] font-semibold tracking-wider text-[#738099] uppercase">
                    Weekly Total XP
                  </span>
                  <p className="mt-1 mb-0 text-lg font-bold text-emerald-300">
                    +{weeklyReport?.totalXp ?? 0} XP
                  </p>
                </div>

                <div className="rounded-xl border border-slate-400/15 bg-white/[0.02] p-3.5">
                  <span className="text-[0.7rem] font-semibold tracking-wider text-[#738099] uppercase">
                    Lessons Completed
                  </span>
                  <p className="mt-1 mb-0 text-lg font-bold text-sky-300">
                    {weeklyReport?.lessonsCompleted ?? 0} lessons
                  </p>
                </div>

                <div className="rounded-xl border border-slate-400/15 bg-white/[0.02] p-3.5">
                  <span className="text-[0.7rem] font-semibold tracking-wider text-[#738099] uppercase">
                    Active Days in Week
                  </span>
                  <p className="mt-1 mb-0 text-lg font-bold text-white">
                    {weeklyReport?.activeDaysCount ?? 0} / 7 days
                  </p>
                </div>

                <div className="rounded-xl border border-slate-400/15 bg-white/[0.02] p-3.5">
                  <span className="text-[0.7rem] font-semibold tracking-wider text-[#738099] uppercase">
                    Daily Average
                  </span>
                  <p className="mt-1 mb-0 text-lg font-bold text-amber-300">
                    {weeklyReport?.averageDailyXp ?? 0} XP / day
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Metric Descriptions & Guide Section */}
          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className={`${panelClass} p-5`}>
              <div className="flex items-center gap-2.5">
                <span className="grid size-8 place-items-center rounded-lg bg-emerald-400/15 text-sm text-emerald-300">
                  ⚡
                </span>
                <h4 className="m-0 text-base font-semibold text-white">
                  How Experience Points (XP) Work
                </h4>
              </div>
              <p className="mt-2.5 mb-0 text-xs leading-relaxed text-[#a8b0c3]">
                Every exercise in a lesson carries a point value. Completing all sign exercises in a
                lesson for the first time awards the full lesson XP to your global profile and logs it
                on your daily activity chart.
              </p>
            </div>

            <div className={`${panelClass} p-5`}>
              <div className="flex items-center gap-2.5">
                <span className="grid size-8 place-items-center rounded-lg bg-purple-400/15 text-sm text-purple-300">
                  🎯
                </span>
                <h4 className="m-0 text-base font-semibold text-white">
                  How Completion Rate Is Calculated
                </h4>
              </div>
              <p className="mt-2.5 mb-0 text-xs leading-relaxed text-[#a8b0c3]">
                When you open a lesson, an attempt is registered. Finishing every sign exercise in the
                session marks the lesson as completed. Your completion accuracy reflects the percentage
                of started attempts that resulted in a finished lesson.
              </p>
            </div>

            <div className={`${panelClass} p-5`}>
              <div className="flex items-center gap-2.5">
                <span className="grid size-8 place-items-center rounded-lg bg-sky-400/15 text-sm text-sky-300">
                  📈
                </span>
                <h4 className="m-0 text-base font-semibold text-white">
                  Building Consistent Habits
                </h4>
              </div>
              <p className="mt-2.5 mb-0 text-xs leading-relaxed text-[#a8b0c3]">
                Regular sign language practice improves gesture recall and hand-shape precision. Use
                the weekly chart above to monitor your active days and aim for steady daily practice
                across each course unit.
              </p>
            </div>
          </div>
        </>
      )}
    </section>
  )
}

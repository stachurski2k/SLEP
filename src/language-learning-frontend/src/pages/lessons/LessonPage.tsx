import { useEffect, useMemo, useRef, useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { fetchLessonDetails, validateExerciseAnswer } from '../../api/learning'
import { predictGesture } from '../../api/prediction'
import { completeLessonProgress, startLessonProgress } from '../../api/progress'
import { recordDailyActivity } from '../../api/statistics'
import { panelClass, primaryButtonClass } from '../../components/ui/classes'
import { lessons as staticLessons } from '../../data/lessons'
import { routes } from '../../router/routes'
import type { LessonEntity, MediaAsset } from '../../types/learning'
import type { Lesson as StaticLesson } from '../../types/lesson'
import type { LessonCompletionResult } from '../../types/progress'

import { parseMediaUrl } from '../../utils/media'

const recordingDurationMs = 3_000
const feedbackDurationMs = 2_000

type LessonState = 'ready' | 'loading' | 'recording' | 'checking' | 'correct' | 'incorrect'

type SessionExercise = {
  id?: string
  content: string
  expectedLabel?: string
  points: number
  media: MediaAsset[]
}

function stopStream(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop())
}

export default function LessonPage() {
  const { lessonId } = useParams<{ lessonId: string }>()

  const staticLesson = useMemo(
    () => staticLessons.find((entry) => entry.id === lessonId),
    [lessonId],
  )

  const [isLoading, setIsLoading] = useState(!staticLesson)
  const [dynamicLesson, setDynamicLesson] = useState<LessonEntity | null>(null)

  useEffect(() => {
    let isMounted = true

    if (staticLesson || !lessonId) {
      return
    }

    const loadDynamic = async () => {
      try {
        const data = await fetchLessonDetails(lessonId)
        if (isMounted) {
          setDynamicLesson(data)
        }
      } catch {
        // Not found or network error
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void loadDynamic()
    return () => {
      isMounted = false
    }
  }, [lessonId, staticLesson])

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3">
        <span className="size-10 animate-spin rounded-full border-4 border-emerald-400 border-t-transparent" />
        <p className="text-sm text-[#a8b0c3]">Loading lesson...</p>
      </div>
    )
  }

  if (staticLesson) {
    return <LessonSession key={staticLesson.id} staticLesson={staticLesson} />
  }

  if (dynamicLesson) {
    return <LessonSession key={dynamicLesson.id} dynamicLesson={dynamicLesson} />
  }

  return <Navigate replace to={routes.lessons} />
}

function LessonSession({
  staticLesson,
  dynamicLesson,
}: {
  staticLesson?: StaticLesson
  dynamicLesson?: LessonEntity
}) {
  const navigate = useNavigate()

  const lessonTitle = dynamicLesson ? dynamicLesson.title : staticLesson?.title || 'Lesson'

  const exercises: SessionExercise[] = useMemo(() => {
    if (dynamicLesson) {
      return (dynamicLesson.exercises || []).map((ex) => ({
        id: ex.id,
        content: ex.content,
        expectedLabel: ex.answer,
        points: ex.points,
        media: ex.media || [],
      }))
    }
    if (staticLesson) {
      return staticLesson.signs.map((sign) => ({
        content: `Show the sign: ${sign}`,
        expectedLabel: sign,
        points: 10,
        media: [],
      }))
    }
    return []
  }, [dynamicLesson, staticLesson])

  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const recordingTimeoutRef = useRef<number | null>(null)
  const feedbackTimeoutRef = useRef<number | null>(null)
  const predictionRequestRef = useRef<AbortController | null>(null)
  const isMountedRef = useRef(false)

  const [lessonState, setLessonState] = useState<LessonState>('ready')
  const [isComplete, setIsComplete] = useState(false)
  const [exerciseIndex, setExerciseIndex] = useState(0)
  const [activeMediaIndex, setActiveMediaIndex] = useState(0)
  const [isMiniPlayerVisible, setIsMiniPlayerVisible] = useState(true)
  const [isExpandedModal, setIsExpandedModal] = useState(false)
  const [earnedPointsTotal, setEarnedPointsTotal] = useState(0)
  const [completionResult, setCompletionResult] = useState<LessonCompletionResult | null>(null)
  const [mediaLoadError, setMediaLoadError] = useState(false)

  const currentExercise = exercises[exerciseIndex]
  const activeMedia = currentExercise?.media?.[activeMediaIndex]

  useEffect(() => {
    isMountedRef.current = true
    if (dynamicLesson?.id && exercises.length > 0) {
      void startLessonProgress(dynamicLesson.id).catch(() => {
        // Ignore if offline
      })
    }
    return () => {
      isMountedRef.current = false
      if (recordingTimeoutRef.current !== null) window.clearTimeout(recordingTimeoutRef.current)
      if (feedbackTimeoutRef.current !== null) window.clearTimeout(feedbackTimeoutRef.current)
      predictionRequestRef.current?.abort()
      const recorder = recorderRef.current
      if (recorder) {
        recorder.onstop = null
        recorder.onerror = null
        if (recorder.state !== 'inactive') recorder.stop()
      }
      stopStream(streamRef.current)
    }
  }, [dynamicLesson?.id, exercises.length])

  if (exercises.length === 0) {
    return (
      <section className="mx-auto grid min-h-[50vh] max-w-xl place-items-center py-16 text-center">
        <div className={`${panelClass} p-8`}>
          <div className="mx-auto grid size-16 place-items-center rounded-full bg-amber-400/10 text-3xl text-amber-300">
            !
          </div>
          <h3 className="mt-4 text-xl font-bold text-white">{lessonTitle}</h3>
          <p className="mt-2 text-sm text-[#a8b0c3]">
            This lesson does not have any exercises assigned yet. Contact your administrator.
          </p>
          <button
            type="button"
            className={`${primaryButtonClass} mt-6`}
            onClick={() => navigate(routes.lessons)}
          >
            Back to lessons
          </button>
        </div>
      </section>
    )
  }

  const enableCamera = async () => {
    const stream =
      streamRef.current ??
      (await navigator.mediaDevices.getUserMedia({ video: true, audio: false }))
    if (!isMountedRef.current || !videoRef.current) {
      stopStream(stream)
      return null
    }
    streamRef.current = stream
    if (videoRef.current.srcObject !== stream) videoRef.current.srcObject = stream
    await videoRef.current.play()
    return isMountedRef.current ? stream : null
  }

  const evaluateRecording = async (recording: Blob) => {
    setLessonState('checking')
    const request = new AbortController()
    predictionRequestRef.current = request

    try {
      const result = await predictGesture(recording, request.signal)
      if (!isMountedRef.current) return

      let isCorrect = false

      if (currentExercise.id) {
        // Dynamic exercise: validate against backend endpoint
        try {
          const valRes = await validateExerciseAnswer(currentExercise.id, result.label)
          isCorrect = valRes.isCorrect
          if (valRes.feedback) {
            toast.info(valRes.feedback)
          }
        } catch {
          // Fallback if API fails
          if (currentExercise.expectedLabel) {
            isCorrect =
              result.label.trim().toUpperCase() === currentExercise.expectedLabel.trim().toUpperCase()
          }
        }
      } else if (currentExercise.expectedLabel) {
        // Static lesson: compare predicted label directly
        isCorrect =
          result.label.trim().toUpperCase() === currentExercise.expectedLabel.trim().toUpperCase()
      }

      const nextTotalPoints = isCorrect
        ? earnedPointsTotal + currentExercise.points
        : earnedPointsTotal

      if (isCorrect) {
        setEarnedPointsTotal(nextTotalPoints)
      }

      setLessonState(isCorrect ? 'correct' : 'incorrect')

      feedbackTimeoutRef.current = window.setTimeout(() => {
        feedbackTimeoutRef.current = null
        if (isCorrect && exerciseIndex === exercises.length - 1) {
          stopStream(streamRef.current)
          streamRef.current = null

          const finalizeLesson = async () => {
            if (dynamicLesson?.id) {
              try {
                const res = await completeLessonProgress(
                  dynamicLesson.id,
                  Math.max(nextTotalPoints, 10),
                )
                if (isMountedRef.current) {
                  setCompletionResult(res)
                }
              } catch {
                // Ignore if offline
              }
            } else {
              await recordDailyActivity({
                xp: Math.max(nextTotalPoints, 10),
                lessonsCompleted: 1,
              }).catch(() => null)
            }
            if (isMountedRef.current) {
              setIsComplete(true)
            }
          }

          void finalizeLesson()
          return
        }
        if (isCorrect) {
          setExerciseIndex((index) => index + 1)
          setActiveMediaIndex(0)
          setMediaLoadError(false)
          setIsMiniPlayerVisible(true)
        }
        setLessonState('ready')
      }, feedbackDurationMs)
    } catch (error) {
      if (!isMountedRef.current) return
      toast.error(error instanceof Error ? error.message : 'Could not recognize gesture.')
      setLessonState('ready')
    } finally {
      predictionRequestRef.current = null
    }
  }

  const recordGesture = async () => {
    if (lessonState !== 'ready') return
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      toast.error('Your browser does not support camera recording.')
      return
    }

    setLessonState('loading')
    try {
      const stream = await enableCamera()
      if (!stream) return
      const recorder = new MediaRecorder(stream, { mimeType: 'video/webm' })
      recorderRef.current = recorder
      const chunks: BlobPart[] = []

      recorder.addEventListener('dataavailable', (event) => {
        if (event.data.size > 0) chunks.push(event.data)
      })

      recorder.onstop = () => {
        recorderRef.current = null
        if (isMountedRef.current) void evaluateRecording(new Blob(chunks, { type: 'video/webm' }))
      }

      recorder.onerror = () => {
        recorder.onstop = null
        if (recordingTimeoutRef.current !== null) window.clearTimeout(recordingTimeoutRef.current)
        recordingTimeoutRef.current = null
        recorderRef.current = null
        if (!isMountedRef.current) return
        toast.error('Video recording failed. Please try again.')
        setLessonState('ready')
      }

      recorder.start()
      setLessonState('recording')
      recordingTimeoutRef.current = window.setTimeout(() => {
        recordingTimeoutRef.current = null
        if (recorder.state !== 'inactive') recorder.stop()
      }, recordingDurationMs)
    } catch (error) {
      if (!isMountedRef.current) return
      toast.error(
        error instanceof DOMException && error.name === 'NotAllowedError'
          ? 'Camera access is required to verify your sign.'
          : 'Could not start camera.',
      )
      setLessonState('ready')
    }
  }

  if (isComplete) {
    return (
      <section className="mx-auto grid min-h-full max-w-xl place-items-center py-10 text-center">
        <div className={`${panelClass} p-8`}>
          <div className="mx-auto grid size-20 place-items-center rounded-full bg-emerald-300/15 text-4xl text-emerald-400">
            ✓
          </div>
          <p className="mt-6 text-xs font-semibold tracking-[0.16em] text-[#64d7bd] uppercase">
            Lesson Complete · {lessonTitle}
          </p>
          <h2 className="mt-3 mb-0 text-3xl font-semibold text-white">Congratulations!</h2>
          <p className="mt-3 text-[#a8b0c3]">
            You have successfully completed all {exercises.length} exercises. Session score:{' '}
            <strong className="font-bold text-emerald-300">+{earnedPointsTotal} pts</strong>.
          </p>

          {completionResult && (
            <div className="mt-4 rounded-xl border border-slate-400/20 bg-white/[0.03] px-4 py-3 text-xs text-[#a8b0c3]">
              {completionResult.isFirstCompletion ? (
                <span>
                  First-time completion bonus:{' '}
                  <strong className="text-amber-300">+{completionResult.earnedXp} XP</strong> awarded!
                  Total XP: <strong className="text-white">{completionResult.totalXp} XP</strong>
                </span>
              ) : (
                <span>
                  Repeat practice session completed! Total XP:{' '}
                  <strong className="text-white">{completionResult.totalXp} XP</strong>
                </span>
              )}
            </div>
          )}

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              className={primaryButtonClass}
              onClick={() => navigate(routes.lessons)}
            >
              Back to lessons
            </button>
            <button
              type="button"
              className="cursor-pointer rounded-xl border border-slate-400/25 bg-slate-400/10 px-5 py-3 text-sm font-semibold text-white transition hover:border-emerald-300/40 hover:bg-slate-400/15"
              onClick={() => navigate(routes.statistics)}
            >
              📊 View Statistics
            </button>
          </div>
        </div>
      </section>
    )
  }

  const isLoading = lessonState === 'loading' || lessonState === 'checking'
  const isFeedback = lessonState === 'correct' || lessonState === 'incorrect'
  const isCorrect = lessonState === 'correct'

  // Helper to render media preview content
  const renderMediaContent = (mediaItem: MediaAsset, isMini: boolean) => {
    const parsed = parseMediaUrl(mediaItem.url)

    if (parsed.isYouTube || parsed.isVimeo) {
      return (
        <iframe
          src={parsed.embedUrl}
          title="Reference demonstration"
          className="h-full w-full border-0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      )
    }

    if (mediaItem.type === 'video' || parsed.isDirectVideo) {
      return (
        <video
          key={mediaItem.url}
          src={mediaItem.url}
          autoPlay
          loop
          muted
          playsInline
          controls={!isMini}
          onError={() => setMediaLoadError(true)}
          className="h-full w-full object-cover"
        />
      )
    }

    return (
      <img
        key={mediaItem.url}
        src={mediaItem.url}
        alt="Reference sign"
        onError={() => setMediaLoadError(true)}
        className="h-full w-full object-contain"
      />
    )
  }

  return (
    <section className="mx-auto w-full max-w-4xl py-2">
      {/* Top progress and back button */}
      <div className="mx-auto flex w-full items-center gap-4">
        <button
          type="button"
          className="grid size-10 cursor-pointer place-items-center rounded-xl border border-slate-400/15 bg-slate-400/5 text-xl text-[#a8b0c3] transition hover:text-white"
          onClick={() => navigate(routes.lessons)}
          aria-label="Back to lessons"
        >
          ×
        </button>
        <div
          className="h-3 flex-1 overflow-hidden rounded-full bg-slate-400/10"
          role="progressbar"
          aria-label="Lesson progress"
          aria-valuemin={0}
          aria-valuemax={exercises.length}
          aria-valuenow={exerciseIndex + 1}
        >
          <div
            className="h-full rounded-full bg-[linear-gradient(90deg,#38c8a6,#4c78ff)] transition-[width] duration-500"
            style={{ width: `${((exerciseIndex + 1) / exercises.length) * 100}%` }}
          />
        </div>
        <span className="text-xs font-medium text-[#738099]">
          {exerciseIndex + 1} / {exercises.length}
        </span>
      </div>

      {/* Main session content */}
      <div className="mt-6 text-center sm:mt-8">
        <p className="mt-0 mb-2 text-sm font-medium text-[#64d7bd]">{lessonTitle}</p>
        <h2 className="mt-1 mb-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
          {currentExercise.content}
        </h2>
        {currentExercise.expectedLabel && (
          <p className="mt-0 mb-4 text-sm font-medium text-[#a8b0c3]">
            Expected sign: <strong className="text-white">{currentExercise.expectedLabel}</strong> ·{' '}
            <span className="text-amber-300 font-semibold">+{currentExercise.points} pts</span>
          </p>
        )}

        {/* Central Camera preview with Miniaturized UI Reference Video */}
        <div className="relative mx-auto aspect-video w-full overflow-hidden rounded-[28px] border border-slate-400/30 bg-[radial-gradient(circle_at_center,rgba(74,119,255,0.16),transparent_45%),#0a1018] shadow-2xl">
          <video
            ref={videoRef}
            className="absolute inset-0 h-full w-full object-cover [-webkit-transform:scaleX(-1)]"
            aria-label="Camera preview"
            autoPlay
            muted
            playsInline
          />

          {/* Start recording button overlay */}
          {lessonState === 'ready' && (
            <div className="absolute inset-0 grid place-items-center bg-black/20 p-4">
              <button
                type="button"
                className={`${primaryButtonClass} gap-3 px-8 py-5 text-lg sm:px-10 sm:py-6 sm:text-xl`}
                onClick={() => void recordGesture()}
              >
                <span className="size-3.5 rounded-full bg-white sm:size-4" aria-hidden="true" />
                Start recording
              </button>
            </div>
          )}

          {/* Status overlays */}
          <div role="status" aria-live="polite" aria-atomic="true">
            {isLoading && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-black/50">
                <span
                  className="size-12 animate-spin rounded-full border-4 border-white/20 border-t-emerald-300 sm:size-16"
                  aria-hidden="true"
                />
                <span className="text-sm font-medium text-white sm:text-base">
                  {lessonState === 'loading' ? 'Starting camera…' : 'Checking your sign…'}
                </span>
              </div>
            )}

            {lessonState === 'recording' && (
              <div className="absolute top-4 left-4 flex items-center gap-2 rounded-full bg-black/60 px-4 py-2 text-sm font-medium text-white">
                <span
                  className="size-2.5 rounded-full bg-red-400 motion-safe:animate-pulse"
                  aria-hidden="true"
                />
                Recording...
              </div>
            )}

            {isFeedback && (
              <div
                className={`absolute inset-0 grid place-items-center ${
                  isCorrect ? 'bg-emerald-950/40' : 'bg-red-950/40'
                }`}
              >
                <div
                  className={`grid size-28 place-items-center rounded-full border-2 backdrop-blur-sm sm:size-40 ${
                    isCorrect
                      ? 'border-emerald-300/70 bg-emerald-500/25 text-emerald-300 shadow-[0_0_100px_rgba(52,211,153,0.4)]'
                      : 'border-red-300/70 bg-red-500/25 text-red-300 shadow-[0_0_100px_rgba(248,113,113,0.35)]'
                  }`}
                >
                  <svg
                    className="size-16 sm:size-24"
                    viewBox="0 0 48 48"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    {isCorrect ? (
                      <path d="m11 25 9 9 18-20" />
                    ) : (
                      <path d="m14 14 20 20m0-20L14 34" />
                    )}
                  </svg>
                </div>
                <span className="sr-only">
                  {isCorrect ? 'Correct sign!' : 'Incorrect sign. Try again.'}
                </span>
              </div>
            )}
          </div>

          {/* Miniaturized Picture-in-Picture Reference Media Element */}
          {activeMedia && isMiniPlayerVisible && (
            <div className="absolute top-3 right-3 z-30 flex w-44 flex-col overflow-hidden rounded-2xl border border-emerald-400/40 bg-[#070b12]/95 shadow-2xl backdrop-blur-md transition-all sm:w-56">
              {/* Mini Header */}
              <div className="flex items-center justify-between border-b border-white/10 bg-white/5 px-2.5 py-1.5 text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-[0.7rem] font-semibold text-white">
                    {activeMedia.type === 'video' ? 'Reference Video' : 'Reference Image'}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setIsExpandedModal(true)}
                    className="cursor-pointer rounded p-1 text-slate-300 hover:bg-white/10 hover:text-white"
                    title="Expand full size"
                  >
                    ⤢
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsMiniPlayerVisible(false)}
                    className="cursor-pointer rounded p-1 text-slate-400 hover:bg-white/10 hover:text-rose-400"
                    title="Hide mini player"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Mini Preview Box */}
              <div className="relative aspect-video w-full overflow-hidden bg-black flex items-center justify-center">
                {mediaLoadError ? (
                  <div className="p-2 text-center text-[0.68rem] text-slate-400">
                    <p className="m-0">Cannot stream media directly.</p>
                    <a
                      href={activeMedia.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-emerald-400 underline"
                    >
                      Open link ↗
                    </a>
                  </div>
                ) : (
                  renderMediaContent(activeMedia, true)
                )}
              </div>

              {/* Multi-media miniature switcher */}
              {currentExercise.media.length > 1 && (
                <div className="flex items-center justify-center gap-1 border-t border-white/5 bg-black/60 px-1 py-1">
                  {currentExercise.media.map((m, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        setActiveMediaIndex(idx)
                        setMediaLoadError(false)
                      }}
                      className={`cursor-pointer rounded px-1.5 py-0.5 text-[0.65rem] font-semibold transition ${
                        activeMediaIndex === idx
                          ? 'bg-emerald-400 text-black'
                          : 'bg-white/10 text-slate-300 hover:text-white'
                      }`}
                    >
                      {m.type === 'video' ? '🎥' : '🖼️'} #{idx + 1}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Toolbar below camera */}
        {currentExercise.media && currentExercise.media.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
            <button
              type="button"
              onClick={() => setIsMiniPlayerVisible((v) => !v)}
              className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-slate-400/20 bg-slate-800/80 px-3.5 py-2 text-xs font-semibold text-slate-200 transition hover:border-emerald-400/40 hover:text-white"
            >
              <span>{isMiniPlayerVisible ? '👁 Hide Mini Reference' : '🎥 Show Mini Reference'}</span>
              <span className="rounded-full bg-emerald-500/20 px-1.5 py-0.2 text-[0.65rem] text-emerald-300">
                {currentExercise.media.length}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setIsExpandedModal(true)}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl border border-slate-400/20 bg-slate-800/80 px-3.5 py-2 text-xs font-semibold text-slate-300 transition hover:border-emerald-400/40 hover:text-white"
            >
              <span>⤢ Expand Preview</span>
            </button>
          </div>
        )}
      </div>

      {/* MODAL: Expanded Reference Preview */}
      {isExpandedModal && activeMedia && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
          <div className={`${panelClass} flex w-full max-w-2xl flex-col overflow-hidden p-5`}>
            <div className="flex items-center justify-between border-b border-slate-400/15 pb-3">
              <div className="flex items-center gap-2">
                <span className="size-2 rounded-full bg-emerald-400" />
                <h3 className="m-0 text-base font-bold text-white">Reference Demonstration</h3>
                <span className="rounded-md bg-emerald-500/15 px-2 py-0.5 text-xs font-semibold text-emerald-300">
                  {activeMedia.type === 'video' ? 'Video clip' : 'Image'}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setIsExpandedModal(false)}
                className="cursor-pointer rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white"
                title="Close modal"
              >
                ✕
              </button>
            </div>

            <div className="relative mt-4 aspect-video w-full overflow-hidden rounded-xl border border-slate-700/60 bg-black flex items-center justify-center">
              {renderMediaContent(activeMedia, false)}
            </div>

            <div className="mt-4 flex items-center justify-between">
              {currentExercise.media.length > 1 ? (
                <div className="flex items-center gap-1.5">
                  {currentExercise.media.map((m, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        setActiveMediaIndex(idx)
                        setMediaLoadError(false)
                      }}
                      className={`cursor-pointer rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                        activeMediaIndex === idx
                          ? 'bg-emerald-400 text-black'
                          : 'border border-slate-400/20 bg-slate-800 text-slate-300 hover:text-white'
                      }`}
                    >
                      {m.type === 'video' ? '🎥 Video' : '🖼️ Image'} #{idx + 1}
                    </button>
                  ))}
                </div>
              ) : (
                <span className="text-xs text-[#a8b0c3]">
                  Format: {activeMedia.type === 'video' ? 'Video Demonstration' : 'Reference Photo'}
                </span>
              )}

              <a
                href={activeMedia.url}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-emerald-400 transition hover:underline"
              >
                Open in new tab ↗
              </a>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

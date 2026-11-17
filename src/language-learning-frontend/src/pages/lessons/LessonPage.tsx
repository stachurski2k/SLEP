import { useEffect, useMemo, useRef, useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { fetchLessonDetails, validateExerciseAnswer } from '../../api/learning'
import { predictGesture } from '../../api/prediction'
import { panelClass, primaryButtonClass } from '../../components/ui/classes'
import { lessons as staticLessons } from '../../data/lessons'
import { routes } from '../../router/routes'
import type { LessonEntity, MediaAsset } from '../../types/learning'
import type { Lesson as StaticLesson } from '../../types/lesson'

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
        <p className="text-sm text-[#a8b0c3]">Ładowanie lekcji...</p>
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

  const lessonTitle = dynamicLesson ? dynamicLesson.title : staticLesson?.title || 'Lekcja'

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
        content: `Wykonaj znak dla: ${sign}`,
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
  const [earnedPointsTotal, setEarnedPointsTotal] = useState(0)

  const currentExercise = exercises[exerciseIndex]
  const activeMedia = currentExercise?.media?.[activeMediaIndex]

  useEffect(() => {
    isMountedRef.current = true
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
  }, [])

  if (exercises.length === 0) {
    return (
      <section className="mx-auto grid min-h-[50vh] max-w-xl place-items-center py-16 text-center">
        <div className={`${panelClass} p-8`}>
          <div className="mx-auto grid size-16 place-items-center rounded-full bg-amber-400/10 text-3xl text-amber-300">
            !
          </div>
          <h3 className="mt-4 text-xl font-bold text-white">{lessonTitle}</h3>
          <p className="mt-2 text-sm text-[#a8b0c3]">
            Ta lekcja nie posiada jeszcze przypisanych zadań. Skontaktuj się z administratorem.
          </p>
          <button
            type="button"
            className={`${primaryButtonClass} mt-6`}
            onClick={() => navigate(routes.lessons)}
          >
            Wróć do listy lekcji
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
        // Dynamic exercise: validate against backend validation endpoint
        try {
          const valRes = await validateExerciseAnswer(currentExercise.id, result.label)
          isCorrect = valRes.isCorrect
          if (valRes.feedback) {
            toast.info(valRes.feedback)
          }
        } catch {
          // Fallback if network issue
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

      if (isCorrect) {
        setEarnedPointsTotal((prev) => prev + currentExercise.points)
      }

      setLessonState(isCorrect ? 'correct' : 'incorrect')

      feedbackTimeoutRef.current = window.setTimeout(() => {
        feedbackTimeoutRef.current = null
        if (isCorrect && exerciseIndex === exercises.length - 1) {
          stopStream(streamRef.current)
          streamRef.current = null
          setIsComplete(true)
          return
        }
        if (isCorrect) {
          setExerciseIndex((index) => index + 1)
          setActiveMediaIndex(0)
        }
        setLessonState('ready')
      }, feedbackDurationMs)
    } catch (error) {
      if (!isMountedRef.current) return
      toast.error(error instanceof Error ? error.message : 'Nie udało się rozpoznać gestu.')
      setLessonState('ready')
    } finally {
      predictionRequestRef.current = null
    }
  }

  const recordGesture = async () => {
    if (lessonState !== 'ready') return
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      toast.error('Twoja przeglądarka nie wspiera nagrywania wideo.')
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
        toast.error('Wystąpił błąd zapisu wideo. Spróbuj ponownie.')
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
          ? 'Dostęp do kamery jest wymagany do weryfikacji gestu.'
          : 'Nie udało się uruchomić kamery.',
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
            Lekcja ukończona · {lessonTitle}
          </p>
          <h2 className="mt-3 mb-0 text-3xl font-semibold text-white">Gratulacje!</h2>
          <p className="mt-3 text-[#a8b0c3]">
            Pomyślnie ukończono wszystkie {exercises.length} zadań. Zdobyte punkty:{' '}
            <strong className="text-emerald-300 font-bold">{earnedPointsTotal} pkt</strong>.
          </p>
          <button
            type="button"
            className={`${primaryButtonClass} mt-8`}
            onClick={() => navigate(routes.lessons)}
          >
            Wróć do listy lekcji
          </button>
        </div>
      </section>
    )
  }

  const isLoading = lessonState === 'loading' || lessonState === 'checking'
  const isFeedback = lessonState === 'correct' || lessonState === 'incorrect'
  const isCorrect = lessonState === 'correct'

  return (
    <section className="mx-auto w-full max-w-6xl py-2">
      {/* Top progress and back button */}
      <div className="mx-auto flex max-w-4xl items-center gap-4">
        <button
          type="button"
          className="grid size-10 cursor-pointer place-items-center rounded-xl border border-slate-400/15 bg-slate-400/5 text-xl text-[#a8b0c3] transition hover:text-white"
          onClick={() => navigate(routes.lessons)}
          aria-label="Wróć do lekcji"
        >
          ×
        </button>
        <div
          className="h-3 flex-1 overflow-hidden rounded-full bg-slate-400/10"
          role="progressbar"
          aria-label="Postęp w lekcji"
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
            Oczekiwany gest: <strong className="text-white">{currentExercise.expectedLabel}</strong> ·{' '}
            <span className="text-amber-300 font-semibold">+{currentExercise.points} pkt</span>
          </p>
        )}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 lg:items-start">
          {/* Camera preview container */}
          <div
            className={`relative mx-auto aspect-video w-full overflow-hidden rounded-[28px] border border-slate-400/30 bg-[radial-gradient(circle_at_center,rgba(74,119,255,0.16),transparent_45%),#0a1018] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] ${
              currentExercise.media && currentExercise.media.length > 0
                ? 'lg:col-span-7'
                : 'lg:col-span-12 max-w-3xl'
            }`}
          >
            <video
              ref={videoRef}
              className="absolute inset-0 h-full w-full object-cover [-webkit-transform:scaleX(-1)]"
              aria-label="Podgląd kamery"
              autoPlay
              muted
              playsInline
            />

            {lessonState === 'ready' && (
              <div className="absolute inset-0 grid place-items-center bg-black/20 p-4">
                <button
                  type="button"
                  className={`${primaryButtonClass} gap-3 px-8 py-5 text-lg sm:px-10 sm:py-6 sm:text-xl`}
                  onClick={() => void recordGesture()}
                >
                  <span className="size-3.5 rounded-full bg-white sm:size-4" aria-hidden="true" />
                  Rozpocznij nagranie
                </button>
              </div>
            )}

            <div role="status" aria-live="polite" aria-atomic="true">
              {isLoading && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-black/50">
                  <span
                    className="size-12 animate-spin rounded-full border-4 border-white/20 border-t-emerald-300 sm:size-16"
                    aria-hidden="true"
                  />
                  <span className="text-sm font-medium text-white sm:text-base">
                    {lessonState === 'loading' ? 'Uruchamianie kamery…' : 'Weryfikacja gestu…'}
                  </span>
                </div>
              )}

              {lessonState === 'recording' && (
                <div className="absolute top-4 right-4 flex items-center gap-2 rounded-full bg-black/60 px-4 py-2 text-sm font-medium text-white sm:top-6 sm:right-6">
                  <span
                    className="size-2.5 rounded-full bg-red-400 motion-safe:animate-pulse"
                    aria-hidden="true"
                  />
                  Nagrywanie...
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
                    {isCorrect ? 'Poprawny gest!' : 'Niepoprawny gest. Spróbuj ponownie.'}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Auxiliary Media / Reference panel */}
          {currentExercise.media && currentExercise.media.length > 0 && (
            <div
              className={`${panelClass} flex flex-col gap-3 p-4 text-left lg:col-span-5`}
            >
              <div className="flex items-center justify-between border-b border-slate-400/15 pb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-white">Materiały pomocnicze</span>
                  <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[0.7rem] font-bold text-emerald-300">
                    {currentExercise.media.length}{' '}
                    {currentExercise.media.length === 1 ? 'materiał' : 'materiały'}
                  </span>
                </div>

                {currentExercise.media.length > 1 && (
                  <div className="flex items-center gap-1">
                    {currentExercise.media.map((m, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setActiveMediaIndex(idx)}
                        className={`cursor-pointer rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                          activeMediaIndex === idx
                            ? 'bg-emerald-400 text-black'
                            : 'border border-slate-400/20 bg-slate-800 text-slate-300 hover:text-white'
                        }`}
                      >
                        {m.type === 'video' ? '🎥' : '🖼️'} #{idx + 1}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {activeMedia && (
                <div className="flex flex-col items-center justify-center overflow-hidden rounded-xl border border-slate-700/60 bg-black/60 p-2">
                  {activeMedia.type === 'video' ? (
                    <video
                      key={activeMedia.url}
                      src={activeMedia.url}
                      controls
                      autoPlay
                      loop
                      muted
                      playsInline
                      className="max-h-64 w-full rounded-lg object-contain shadow-md sm:max-h-72"
                    />
                  ) : (
                    <img
                      key={activeMedia.url}
                      src={activeMedia.url}
                      alt="Wizualny materiał referencyjny"
                      className="max-h-64 w-full rounded-lg object-contain shadow-md sm:max-h-72"
                      onError={(e) => {
                        ;(e.target as HTMLElement).style.display = 'none'
                      }}
                    />
                  )}
                  <div className="mt-2 flex w-full items-center justify-between px-1 text-[0.72rem] text-[#a8b0c3]">
                    <span className="capitalize font-medium">
                      Format: {activeMedia.type === 'video' ? 'Wideo poglądowe' : 'Zdjęcie referencyjne'}
                    </span>
                    <a
                      href={activeMedia.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-emerald-400 transition hover:underline"
                    >
                      Pełny ekran ↗
                    </a>
                  </div>
                </div>
              )}

              <p className="mt-1 mb-0 text-[0.75rem] leading-relaxed text-[#738099]">
                💡 Wskazówka: Zwróć uwagę na ułożenie dłoni i palców przedstawione na materiałach powyżej przed rozpoczęciem nagrania.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

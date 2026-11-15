import { useEffect, useRef, useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { predictGesture } from '../actions'
import { lessons, type Lesson } from '../lesson'
import { routes } from '../routes'
import { primaryButtonClass } from '../ui/classes'

const recordingDurationMs = 3_000
const feedbackDurationMs = 2_000

type LessonState = 'ready' | 'loading' | 'recording' | 'checking' | 'correct' | 'incorrect'

function stopStream(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop())
}

export default function LessonPage() {
  const { lessonId } = useParams<{ lessonId: string }>()
  const lesson = lessons.find((entry) => entry.id === lessonId)

  if (!lesson) return <Navigate replace to={routes.lessons} />

  return <LessonSession key={lesson.id} lesson={lesson} />
}

function LessonSession({ lesson }: { lesson: Lesson }) {
  const navigate = useNavigate()
  const lessonSigns = lesson.signs
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const recordingTimeoutRef = useRef<number | null>(null)
  const feedbackTimeoutRef = useRef<number | null>(null)
  const predictionRequestRef = useRef<AbortController | null>(null)
  const isMountedRef = useRef(false)
  const [lessonState, setLessonState] = useState<LessonState>('ready')
  const [isComplete, setIsComplete] = useState(false)
  const [signIndex, setSignIndex] = useState(0)
  const expectedLabel = lessonSigns[signIndex]

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

  const enableCamera = async () => {
    const stream = streamRef.current
      ?? await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
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
      const isCorrect = result.label.trim().toUpperCase() === expectedLabel
      setLessonState(isCorrect ? 'correct' : 'incorrect')
      feedbackTimeoutRef.current = window.setTimeout(() => {
        feedbackTimeoutRef.current = null
        if (isCorrect && signIndex === lessonSigns.length - 1) {
          stopStream(streamRef.current)
          streamRef.current = null
          setIsComplete(true)
          return
        }
        if (isCorrect) setSignIndex((index) => index + 1)
        setLessonState('ready')
      }, feedbackDurationMs)
    } catch (error) {
      if (!isMountedRef.current) return
      toast.error(error instanceof Error ? error.message : 'The gesture could not be recognized.')
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
        toast.error('The video could not be recorded. Please try again.')
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
          ? 'Camera access is required to check your sign.'
          : 'The camera could not be started.',
      )
      setLessonState('ready')
    }
  }

  if (isComplete) {
    return (
      <section className="mx-auto grid min-h-full max-w-xl place-items-center py-10 text-center">
        <div>
          <div className="mx-auto grid size-20 place-items-center rounded-full bg-emerald-300/15 text-4xl">✓</div>
          <p className="mt-6 text-xs font-semibold tracking-[0.16em] text-[#64d7bd] uppercase">Lesson {lesson.id} complete · {lesson.title}</p>
          <h2 className="mt-3 mb-0 text-3xl font-semibold text-white">Nice work!</h2>
          <p className="mt-3 text-[#a8b0c3]">You completed all {lessonSigns.length} signs: {lessonSigns.join(', ')}.</p>
          <button type="button" className={`${primaryButtonClass} mt-8`} onClick={() => navigate(routes.lessons)}>Back to lessons</button>
        </div>
      </section>
    )
  }

  const isLoading = lessonState === 'loading' || lessonState === 'checking'
  const isFeedback = lessonState === 'correct' || lessonState === 'incorrect'
  const isCorrect = lessonState === 'correct'

  return (
    <section className="mx-auto w-full max-w-6xl py-2">
      <div className="mx-auto flex max-w-3xl items-center gap-4">
        <button type="button" className="grid size-10 cursor-pointer place-items-center rounded-xl border border-slate-400/15 bg-slate-400/5 text-xl text-[#a8b0c3] transition hover:text-white" onClick={() => navigate(routes.lessons)} aria-label="Back to lessons">×</button>
        <div className="h-3 flex-1 overflow-hidden rounded-full bg-slate-400/10" role="progressbar" aria-label="Lesson progress" aria-valuemin={0} aria-valuemax={lessonSigns.length} aria-valuenow={signIndex + 1}>
          <div className="h-full rounded-full bg-[linear-gradient(90deg,#38c8a6,#4c78ff)] transition-[width] duration-500" style={{ width: `${((signIndex + 1) / lessonSigns.length) * 100}%` }} />
        </div>
        <span className="text-xs font-medium text-[#738099]">{signIndex + 1} / {lessonSigns.length}</span>
      </div>
      <div className="mt-8 text-center sm:mt-10">
        <p className="mt-0 mb-3 text-sm font-medium text-[#64d7bd]">Lesson {lesson.id} · {lesson.title}</p>
        <p className="m-0 text-lg font-medium text-[#a8b0c3]">Show the sign:</p>
        <h2 className="mt-2 mb-0 text-5xl font-bold tracking-tight text-white sm:text-6xl">{expectedLabel}</h2>
        <div className="relative mt-6 aspect-video w-full overflow-hidden rounded-[28px] border border-slate-400/30 bg-[radial-gradient(circle_at_center,rgba(74,119,255,0.16),transparent_45%),#0a1018] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:mt-8">
          <video ref={videoRef} className="absolute inset-0 h-full w-full object-cover [-webkit-transform:scaleX(-1)]" aria-label="Camera preview" autoPlay muted playsInline />
          {lessonState === 'ready' && (
            <div className="absolute inset-0 grid place-items-center bg-black/20 p-4">
              <button type="button" className={`${primaryButtonClass} gap-3 px-8 py-6 text-xl sm:px-12 sm:py-8 sm:text-2xl`} onClick={() => void recordGesture()}>
                <span className="size-4 rounded-full bg-white sm:size-5" aria-hidden="true" />
                Start recording
              </button>
            </div>
          )}
          <div role="status" aria-live="polite" aria-atomic="true">
            {isLoading && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-black/40">
                <span className="size-12 animate-spin rounded-full border-4 border-white/20 border-t-emerald-300 sm:size-16" aria-hidden="true" />
                <span className="text-sm font-medium text-white sm:text-base">{lessonState === 'loading' ? 'Starting camera…' : 'Checking your sign…'}</span>
              </div>
            )}
            {lessonState === 'recording' && (
              <div className="absolute top-4 right-4 flex items-center gap-2 rounded-full bg-black/60 px-4 py-2 text-sm font-medium text-white sm:top-6 sm:right-6">
                <span className="size-2.5 rounded-full bg-red-400 motion-safe:animate-pulse" aria-hidden="true" />
                Recording
              </div>
            )}
            {isFeedback && (
              <div className={`absolute inset-0 grid place-items-center ${isCorrect ? 'bg-emerald-950/30' : 'bg-red-950/30'}`}>
                <div className={`grid size-28 place-items-center rounded-full border-2 backdrop-blur-sm sm:size-48 ${isCorrect ? 'border-emerald-300/70 bg-emerald-500/25 text-emerald-300 shadow-[0_0_100px_rgba(52,211,153,0.4)]' : 'border-red-300/70 bg-red-500/25 text-red-300 shadow-[0_0_100px_rgba(248,113,113,0.35)]'}`}>
                  <svg className="size-16 sm:size-28" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    {isCorrect ? <path d="m11 25 9 9 18-20" /> : <path d="m14 14 20 20m0-20L14 34" />}
                  </svg>
                </div>
                <span className="sr-only">{isCorrect ? 'Correct sign! Moving on.' : 'Incorrect sign. Try again.'}</span>
              </div>
            )}
          </div>
        </div>
        <details key={expectedLabel} className="group mt-6">
          <summary className="mx-auto flex min-h-12 w-fit cursor-pointer list-none items-center gap-2 rounded-xl border border-slate-400/20 bg-slate-400/5 px-5 font-medium text-[#a8b0c3] transition hover:border-emerald-300/35 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 [&::-webkit-details-marker]:hidden">
            Help
            <svg className="size-4 transition-transform group-open:rotate-180" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="m6 9 6 6 6-6" />
            </svg>
          </summary>
          <div className="mt-4 min-h-40 rounded-2xl border border-slate-400/15 bg-[#0a1018] sm:min-h-56" role="region" aria-label={`Help for ${expectedLabel}`} />
        </details>
      </div>
    </section>
  )
}

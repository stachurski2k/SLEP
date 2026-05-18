import { useEffect, useId, useMemo, useRef, useState } from 'react'
import type { ChangeEvent, DragEvent, MouseEvent } from 'react'
import { panelClass, panelLabelClass } from '../ui/classes'

const DEFAULT_FPS = 30
const MIN_ZOOM = 80
const MAX_ZOOM = 320
const TIMELINE_PADDING = 24
const readoutPillClass =
  'inline-flex min-h-[34px] items-center rounded-full border border-slate-400/15 bg-slate-400/5 px-3 text-sm text-[#a8b0c3]'
const primaryIconButtonClass =
  'inline-flex h-[42px] w-[42px] items-center justify-center rounded-[14px] border border-emerald-300/20 bg-[linear-gradient(180deg,rgba(61,217,179,0.18),rgba(75,123,255,0.14))] text-[#f5f7fb] transition duration-150 hover:-translate-y-px hover:border-emerald-300/40 disabled:cursor-not-allowed disabled:opacity-40 [&_svg]:h-[18px] [&_svg]:w-[18px]'
const secondaryIconButtonClass =
  'inline-flex h-[42px] w-[42px] items-center justify-center rounded-[14px] border border-slate-400/15 bg-slate-400/10 text-[#a8b0c3] transition duration-150 hover:-translate-y-px hover:border-emerald-300/40 disabled:cursor-not-allowed disabled:opacity-40 [&_svg]:h-[18px] [&_svg]:w-[18px]'

type VideoAsset = {
  url: string
  name: string
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

function formatTime(seconds: number) {
  if (!Number.isFinite(seconds)) {
    return '00:00:00'
  }

  const totalSeconds = Math.max(0, seconds)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const secs = Math.floor(totalSeconds % 60)

  return [hours, minutes, secs]
    .map((part) => part.toString().padStart(2, '0'))
    .join(':')
}

function formatFrameTime(seconds: number, fps: number) {
  if (!Number.isFinite(seconds)) {
    return '00:00:00:00'
  }

  const safeSeconds = Math.max(0, seconds)
  const hours = Math.floor(safeSeconds / 3600)
  const minutes = Math.floor((safeSeconds % 3600) / 60)
  const secs = Math.floor(safeSeconds % 60)
  const frame = Math.floor((safeSeconds % 1) * fps)

  return [hours, minutes, secs, frame]
    .map((part) => part.toString().padStart(2, '0'))
    .join(':')
}

function getRulerStep(zoom: number) {
  if (zoom >= 260) return 1
  if (zoom >= 180) return 2
  if (zoom >= 120) return 5
  return 10
}

export default function EditorPage() {
  const inputId = useId()
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const timelineRef = useRef<HTMLDivElement | null>(null)
  const objectUrlRef = useRef<string | null>(null)

  const [asset, setAsset] = useState<VideoAsset | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [zoom, setZoom] = useState(140)

  useEffect(() => {
    return () => {
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current)
      }
    }
  }, [])

  const fps = DEFAULT_FPS
  const secondsPerFrame = 1 / fps
  const timelineWidth = Math.max(duration * zoom + TIMELINE_PADDING * 2, 720)
  const clipWidth = Math.max(duration * zoom, 120)
  const markerOffset = TIMELINE_PADDING + currentTime * zoom

  const rulerMarks = useMemo(() => {
    if (!duration) {
      return []
    }

    const step = getRulerStep(zoom)
    const marks = []
    for (let second = 0; second <= Math.ceil(duration); second += step) {
      marks.push({
        second,
        left: TIMELINE_PADDING + second * zoom,
      })
    }
    return marks
  }, [duration, zoom])

  const loadFile = (file: File) => {
    if (file.type !== 'video/mp4' && !file.name.toLowerCase().endsWith('.mp4')) {
      return
    }

    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current)
    }

    const url = URL.createObjectURL(file)
    objectUrlRef.current = url
    setAsset({
      url,
      name: file.name,
    })
    setCurrentTime(0)
    setDuration(0)
    setIsPlaying(false)
  }

  const handleFileInput = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0]
    if (nextFile) {
      loadFile(nextFile)
    }
    event.target.value = ''
  }

  const handleDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault()
    setIsDragging(false)

    const nextFile = event.dataTransfer.files?.[0]
    if (nextFile) {
      loadFile(nextFile)
    }
  }

  const handleTimelineSeek = (event: MouseEvent<HTMLDivElement>) => {
    if (!videoRef.current || !duration) {
      return
    }

    const bounds = event.currentTarget.getBoundingClientRect()
    const rawX = event.clientX - bounds.left + event.currentTarget.scrollLeft
    const nextTime = clamp((rawX - TIMELINE_PADDING) / zoom, 0, duration)

    videoRef.current.currentTime = nextTime
    setCurrentTime(nextTime)
  }

  const togglePlayback = async () => {
    if (!videoRef.current || !asset) {
      return
    }

    if (videoRef.current.paused) {
      await videoRef.current.play()
      setIsPlaying(true)
      return
    }

    videoRef.current.pause()
    setIsPlaying(false)
  }

  const stepFrame = (direction: 1 | -1) => {
    if (!videoRef.current || !duration) {
      return
    }

    videoRef.current.pause()
    setIsPlaying(false)

    const nextTime = clamp(
      videoRef.current.currentTime + direction * secondsPerFrame,
      0,
      duration,
    )

    videoRef.current.currentTime = nextTime
    setCurrentTime(nextTime)
  }

  useEffect(() => {
    const timeline = timelineRef.current
    if (!timeline || !duration) {
      return
    }

    const centerTarget = markerOffset - timeline.clientWidth / 2
    const maxScroll = Math.max(0, timeline.scrollWidth - timeline.clientWidth)
    timeline.scrollLeft = clamp(centerTarget, 0, maxScroll)
  }, [duration, markerOffset])

  return (
    <section className="grid gap-[18px]">
      <div className={`${panelClass} min-h-0 overflow-hidden`}>
        {asset ? (
          <div className="grid p-[18px] max-[720px]:p-3.5">
            <video
              ref={videoRef}
              className="block min-h-[750px] max-h-[40vh] w-full rounded-[18px] border border-slate-400/10 bg-[radial-gradient(circle_at_top,rgba(61,217,179,0.14),transparent_22%),#05070b] object-contain max-[720px]:min-h-60"
              src={asset.url}
              controls={false}
              onLoadedMetadata={(event) => {
                setDuration(event.currentTarget.duration)
                setCurrentTime(0)
              }}
              onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onEnded={() => setIsPlaying(false)}
            />
          </div>
        ) : (
          <label
            className={[
              'grid min-h-[750px] cursor-pointer place-items-center rounded-[22px] border border-dashed p-9 transition duration-150 max-[720px]:min-h-60',
              'bg-[linear-gradient(135deg,rgba(61,217,179,0.08),transparent_36%),linear-gradient(225deg,rgba(75,123,255,0.1),transparent_30%),rgba(7,11,18,0.86)]',
              isDragging
                ? '-translate-y-px border-emerald-300/45 bg-[#0a1018]/95'
                : 'border-slate-400/20 hover:-translate-y-px hover:border-emerald-300/45 hover:bg-[#0a1018]/95',
            ].join(' ')}
            htmlFor={inputId}
            onDragEnter={(event) => {
              event.preventDefault()
              setIsDragging(true)
            }}
            onDragOver={(event) => {
              event.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={(event) => {
              event.preventDefault()
              if (event.currentTarget === event.target) {
                setIsDragging(false)
              }
            }}
            onDrop={handleDrop}
          >
            <input
              id={inputId}
              className="sr-only"
              type="file"
              accept="video/mp4,.mp4"
              onChange={handleFileInput}
            />
            <div className="max-w-[520px] text-center">
              <p className={panelLabelClass}>Import mp4</p>
              <h3 className="my-3 text-[1.6rem] font-semibold tracking-normal text-[#f5f7fb]">
                Drop a video here
              </h3>
              <p className="mb-0 text-[#a8b0c3]">
                Drag and drop an MP4 file, or click to browse and open it in
                the editor.
              </p>
            </div>
          </label>
        )}
      </div>

      <section className={`${panelClass} grid gap-4 p-4 max-[720px]:p-3.5`}>
        <div className="flex items-center justify-between gap-3.5 max-[720px]:flex-col max-[720px]:items-start">
          <div className="flex items-center gap-2.5">
            <button
              className={primaryIconButtonClass}
              type="button"
              onClick={togglePlayback}
              disabled={!asset}
              aria-label={isPlaying ? 'Pause video' : 'Play video'}
            >
              {isPlaying ? <PauseIcon /> : <PlayIcon />}
            </button>

            <button
              className={secondaryIconButtonClass}
              type="button"
              onClick={() => stepFrame(-1)}
              disabled={!asset}
              aria-label="Previous frame"
            >
              <PreviousFrameIcon />
            </button>

            <button
              className={secondaryIconButtonClass}
              type="button"
              onClick={() => stepFrame(1)}
              disabled={!asset}
              aria-label="Next frame"
            >
              <NextFrameIcon />
            </button>
          </div>

          <div className="flex gap-2">
            <span className={readoutPillClass}>{formatFrameTime(currentTime, fps)}</span>
            <span className={readoutPillClass}>30 fps step</span>
          </div>
        </div>

        <div className="grid min-h-56 grid-cols-[188px_minmax(0,1fr)] gap-3.5 max-[1080px]:grid-cols-1">
          <div className="grid grid-rows-[56px_1fr] overflow-hidden rounded-[18px] border border-slate-400/10 bg-[#070b12]/80 max-[1080px]:grid-cols-[96px_1fr] max-[1080px]:grid-rows-1">
            <div className="flex items-center border-b border-slate-400/10 px-4 text-xs tracking-[0.12em] text-[#738099] uppercase max-[1080px]:border-r max-[1080px]:border-b-0">
              V1
            </div>
            <div className="flex items-center px-4 text-[#a8b0c3]">
              {asset?.name ?? 'No clip loaded'}
            </div>
          </div>

          <div className="grid min-w-0 grid-rows-[minmax(0,1fr)_auto] overflow-hidden rounded-[18px] border border-slate-400/10 bg-[#070b12]/80">
            <div className="min-w-0 overflow-hidden">
              <div
                ref={timelineRef}
                className="relative h-full min-w-0 cursor-pointer overflow-x-auto overflow-y-hidden [scrollbar-color:rgba(148,163,184,0.45)_transparent]"
                onClick={handleTimelineSeek}
              >
                <div
                  className="relative min-h-44 bg-[linear-gradient(rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.035)_1px,transparent_1px),linear-gradient(180deg,rgba(11,17,25,0.94),rgba(8,12,18,1))] bg-[length:100%_44px,48px_100%,100%_100%]"
                  style={{ width: timelineWidth }}
                >
                  {rulerMarks.map((mark) => (
                    <div
                      key={mark.second}
                      className="absolute top-0 bottom-0 w-px bg-white/10"
                      style={{ left: mark.left }}
                    >
                      <span className="absolute top-2.5 left-2 whitespace-nowrap text-[0.72rem] text-[#738099]">
                        {formatTime(mark.second)}
                      </span>
                    </div>
                  ))}

                  {asset ? (
                    <button
                      className="absolute top-[62px] h-[70px] overflow-hidden rounded-[14px] border border-emerald-300/30 bg-[linear-gradient(180deg,rgba(61,217,179,0.22),rgba(75,123,255,0.18)),rgba(16,24,34,0.94)] px-4 py-3.5 text-left text-[#f5f7fb] shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
                      type="button"
                      style={{
                        width: clipWidth,
                        left: TIMELINE_PADDING,
                      }}
                    >
                      <span className="block overflow-hidden text-ellipsis whitespace-nowrap">
                        {asset.name}
                      </span>
                    </button>
                  ) : (
                    <div className="absolute inset-[62px_24px_24px] grid place-items-center rounded-2xl border border-dashed border-slate-400/20 text-[#738099]">
                      Import an MP4 file to build the timeline.
                    </div>
                  )}

                  {asset ? (
                    <div
                      className="pointer-events-none absolute top-0 bottom-0 w-0.5 bg-orange-500 shadow-[0_0_0_1px_rgba(249,115,22,0.18)]"
                      style={{ left: markerOffset }}
                      aria-hidden="true"
                    >
                      <span className="absolute top-2 left-1/2 h-3.5 w-3.5 -translate-x-1/2 rotate-45 rounded bg-orange-500" />
                    </div>
                  ) : null}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 border-t border-slate-400/10 px-3.5 pt-3 pb-3.5">
              <span className="text-xs tracking-[0.12em] text-[#738099] uppercase">
                Zoom
              </span>
              <input
                className="h-1.5 flex-1 appearance-none rounded-full bg-[linear-gradient(90deg,rgba(61,217,179,0.65),rgba(75,123,255,0.65))] outline-none [&::-moz-range-thumb]:h-[18px] [&::-moz-range-thumb]:w-[18px] [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-[#0a0e16]/90 [&::-moz-range-thumb]:bg-[#f5f7fb] [&::-moz-range-thumb]:shadow-[0_0_16px_rgba(75,123,255,0.28)] [&::-webkit-slider-thumb]:h-[18px] [&::-webkit-slider-thumb]:w-[18px] [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-[#0a0e16]/90 [&::-webkit-slider-thumb]:bg-[#f5f7fb] [&::-webkit-slider-thumb]:shadow-[0_0_16px_rgba(75,123,255,0.28)]"
                type="range"
                min={MIN_ZOOM}
                max={MAX_ZOOM}
                step={10}
                value={zoom}
                onChange={(event) => setZoom(Number(event.target.value))}
                aria-label="Timeline zoom"
              />
            </div>
          </div>
        </div>
      </section>
    </section>
  )
}

function PlayIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M8 6.5v11l9-5.5-9-5.5Z" fill="currentColor" />
    </svg>
  )
}

function PauseIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7 6h4v12H7zM13 6h4v12h-4z" fill="currentColor" />
    </svg>
  )
}

function PreviousFrameIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M8 6h2v12H8zM17 7.5 11 12l6 4.5v-9Z" fill="currentColor" />
    </svg>
  )
}

function NextFrameIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M14 7.5 20 12l-6 4.5v-9ZM6 6h2v12H6z" fill="currentColor" />
    </svg>
  )
}

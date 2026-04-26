import { useEffect, useId, useMemo, useRef, useState } from 'react'
import type { ChangeEvent, DragEvent, MouseEvent } from 'react'
import './Editor.css'

const DEFAULT_FPS = 30
const MIN_ZOOM = 80
const MAX_ZOOM = 320
const TIMELINE_PADDING = 24

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

export default function Editor() {
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
    <section className="editor-panel">

      <div className="preview-panel">
        {asset ? (
          <div className="video-stage">
            <video
              ref={videoRef}
              className="video-display"
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
            className={`dropzone${isDragging ? ' dropzone-active' : ''}`}
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
            <div className="dropzone-content">
              <p className="panel-label">Import mp4</p>
              <h3>Drop a video here</h3>
              <p>
                Drag and drop an MP4 file, or click to browse and open it in
                the editor.
              </p>
            </div>
          </label>
        )}
      </div>

      <section className="timeline-panel">
        <div className="timeline-toolbar">
          <div className="transport-group">
            <button
              className="icon-button"
              type="button"
              onClick={togglePlayback}
              disabled={!asset}
              aria-label={isPlaying ? 'Pause video' : 'Play video'}
            >
              {isPlaying ? <PauseIcon /> : <PlayIcon />}
            </button>

            <button
              className="icon-button icon-button-secondary"
              type="button"
              onClick={() => stepFrame(-1)}
              disabled={!asset}
              aria-label="Previous frame"
            >
              <PreviousFrameIcon />
            </button>

            <button
              className="icon-button icon-button-secondary"
              type="button"
              onClick={() => stepFrame(1)}
              disabled={!asset}
              aria-label="Next frame"
            >
              <NextFrameIcon />
            </button>
          </div>

          <div className="timeline-readout">
            <span>{formatFrameTime(currentTime, fps)}</span>
            <span>30 fps step</span>
          </div>
        </div>

        <div className="timeline-layout">
          <div className="track-labels">
            <div className="track-header">V1</div>
            <div className="track-name">{asset?.name ?? 'No clip loaded'}</div>
          </div>

          <div className="timeline-stage">
            <div className="timeline-ruler">
              <div
                ref={timelineRef}
                className="timeline-scroll"
                onClick={handleTimelineSeek}
              >
                <div className="timeline-content" style={{ width: timelineWidth }}>
                  {rulerMarks.map((mark) => (
                    <div
                      key={mark.second}
                      className="ruler-mark"
                      style={{ left: mark.left }}
                    >
                      <span>{formatTime(mark.second)}</span>
                    </div>
                  ))}

                  {asset ? (
                    <button
                      className="clip-block"
                      type="button"
                      style={{
                        width: clipWidth,
                        left: TIMELINE_PADDING,
                      }}
                    >
                      <span className="clip-name">{asset.name}</span>
                    </button>
                  ) : (
                    <div className="timeline-empty">
                      Import an MP4 file to build the timeline.
                    </div>
                  )}

                  {asset ? (
                    <div
                      className="playhead"
                      style={{ left: markerOffset }}
                      aria-hidden="true"
                    >
                      <span className="playhead-handle" />
                    </div>
                  ) : null}
                </div>
              </div>
            </div>

            <div className="zoom-strip">
              <span className="zoom-label">Zoom</span>
              <input
                className="zoom-slider"
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

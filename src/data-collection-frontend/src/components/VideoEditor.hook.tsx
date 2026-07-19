import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent, MouseEvent, SyntheticEvent } from 'react'
import { toast } from 'sonner'
import {
  createVideoClip,
  getDownloadUrl,
  getGestureClasses,
  getGestureTypes,
} from '../actions'
import type { GestureClass, GestureType, Video } from '../actions'

const DEFAULT_FPS = 30
export const MIN_ZOOM = 80
export const MAX_ZOOM = 320
export const TIMELINE_PADDING = 24

const SELECTED_GESTURE_CLASS_CACHE_KEY = 'videoEditor.selectedGestureClassId'
const SELECTED_GESTURE_TYPE_CACHE_KEY = 'videoEditor.selectedGestureTypeId'

type VideoAsset = {
  url: string
  name: string
  filepath: string
}

type ClipPointMarker = {
  id: 'start' | 'end'
  label: string
  frameIndex: number
  left: number
}

type RulerMark = {
  second: number
  left: number
  label: string
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

function shouldIgnoreHotkey(event: KeyboardEvent) {
  const target = event.target

  if (!(target instanceof HTMLElement)) {
    return false
  }

  return (
    target.isContentEditable ||
    target.closest(
      'a, button, input, select, textarea, [role="button"], [role="link"]',
    ) !== null
  )
}

function formatFrameIndex(frameIndex: number | null) {
  return frameIndex === null ? 'Not set' : frameIndex.toString()
}

function readCachedValue(key: string) {
  if (typeof window === 'undefined') {
    return ''
  }

  return window.localStorage.getItem(key) ?? ''
}

export function useVideoEditor(video: Video | null) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const timelineRef = useRef<HTMLDivElement | null>(null)
  const [loadedAsset, setLoadedAsset] = useState<VideoAsset | null>(null)
  const [failedVideoPath, setFailedVideoPath] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [zoom, setZoom] = useState(140)
  const [startFrameIndex, setStartFrameIndex] = useState<number | null>(null)
  const [endFrameIndex, setEndFrameIndex] = useState<number | null>(null)
  const [gestureClasses, setGestureClasses] = useState<GestureClass[]>([])
  const [gestureTypes, setGestureTypes] = useState<GestureType[]>([])
  const [selectedGestureClassId, setSelectedGestureClassId] = useState(() =>
    readCachedValue(SELECTED_GESTURE_CLASS_CACHE_KEY),
  )
  const [selectedGestureTypeId, setSelectedGestureTypeId] = useState(() =>
    readCachedValue(SELECTED_GESTURE_TYPE_CACHE_KEY),
  )
  const [isSavingClip, setIsSavingClip] = useState(false)

  const asset =
    video && loadedAsset?.filepath === video.filepath ? loadedAsset : null
  const fps = DEFAULT_FPS
  const secondsPerFrame = 1 / fps
  const activeDuration = asset ? duration : 0
  const activeCurrentTime = asset ? currentTime : 0
  const maxFrameIndex = Math.max(0, Math.floor(activeDuration * fps))
  const timelineWidth = Math.max(
    activeDuration * zoom + TIMELINE_PADDING * 2,
    720,
  )
  const clipWidth = Math.max(activeDuration * zoom, 120)
  const markerOffset = TIMELINE_PADDING + activeCurrentTime * zoom
  const isVideoLoading =
    Boolean(video) &&
    loadedAsset?.filepath !== video?.filepath &&
    failedVideoPath !== video?.filepath

  const rulerMarks = useMemo<RulerMark[]>(() => {
    if (!activeDuration) {
      return []
    }

    const step = getRulerStep(zoom)
    const marks = []
    for (let second = 0; second <= Math.ceil(activeDuration); second += step) {
      marks.push({
        second,
        left: TIMELINE_PADDING + second * zoom,
        label: formatTime(second),
      })
    }
    return marks
  }, [activeDuration, zoom])

  const clipPointMarkers = useMemo<ClipPointMarker[]>(
    () =>
      [
        { id: 'start', label: 'Start', frameIndex: startFrameIndex },
        { id: 'end', label: 'End', frameIndex: endFrameIndex },
      ]
        .filter(
          (point): point is {
            id: 'start' | 'end'
            label: string
            frameIndex: number
          } => point.frameIndex !== null,
        )
        .map((point) => ({
          ...point,
          left: TIMELINE_PADDING + (point.frameIndex / fps) * zoom,
        })),
    [endFrameIndex, fps, startFrameIndex, zoom],
  )

  const clipSelection = useMemo(() => {
    if (startFrameIndex === null || endFrameIndex === null) {
      return null
    }

    const firstFrame = Math.min(startFrameIndex, endFrameIndex)
    const lastFrame = Math.max(startFrameIndex, endFrameIndex)

    return {
      left: TIMELINE_PADDING + (firstFrame / fps) * zoom,
      width: Math.max(((lastFrame - firstFrame) / fps) * zoom, 2),
    }
  }, [endFrameIndex, fps, startFrameIndex, zoom])

  const resetPlaybackState = useCallback(() => {
    setCurrentTime(0)
    setDuration(0)
    setIsPlaying(false)
  }, [])

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

  const togglePlayback = useCallback(async () => {
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
  }, [asset])

  const stepFrame = useCallback(
    (direction: 1 | -1) => {
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
    },
    [duration, secondsPerFrame],
  )

  const getCurrentFrameIndex = useCallback(() => {
    const time = videoRef.current?.currentTime ?? activeCurrentTime

    return clamp(Math.round(time * fps), 0, maxFrameIndex)
  }, [activeCurrentTime, fps, maxFrameIndex])

  const setClipPoint = useCallback(
    (point: 'start' | 'end') => {
      if (!asset) {
        return
      }

      const frameIndex = getCurrentFrameIndex()

      if (point === 'start') {
        setStartFrameIndex(frameIndex)
        return
      }

      setEndFrameIndex(frameIndex)
    },
    [asset, getCurrentFrameIndex],
  )

  const saveClip = useCallback(async () => {
    if (!video || !asset) {
      toast.error('Select a video before saving a clip')
      return
    }

    if (isSavingClip) {
      return
    }

    if (startFrameIndex === null) {
      toast.error('Set clip start point')
      return
    }

    if (endFrameIndex === null) {
      toast.error('Set clip end point')
      return
    }

    if (endFrameIndex < startFrameIndex) {
      toast.error('Clip end point cannot be before start point')
      return
    }

    if (!selectedGestureClassId) {
      toast.error('Select gesture class')
      return
    }

    if (!selectedGestureTypeId) {
      toast.error('Select gesture type')
      return
    }

    setIsSavingClip(true)

    try {
      await createVideoClip(video.id, {
        start_frame_index: startFrameIndex,
        end_frame_index: endFrameIndex,
        gesture_class_id: Number(selectedGestureClassId),
        gesture_type_id: Number(selectedGestureTypeId),
      })
      toast.success('Clip saved')
    } catch {
      toast.error('Unable to save clip')
    } finally {
      setIsSavingClip(false)
    }
  }, [
    asset,
    endFrameIndex,
    isSavingClip,
    selectedGestureClassId,
    selectedGestureTypeId,
    startFrameIndex,
    video,
  ])

  const handleSaveClip = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void saveClip()
  }

  const handleLoadedMetadata = (event: SyntheticEvent<HTMLVideoElement>) => {
    setDuration(event.currentTarget.duration)
    setCurrentTime(0)
  }

  const handleTimeUpdate = (event: SyntheticEvent<HTMLVideoElement>) => {
    setCurrentTime(event.currentTarget.currentTime)
  }

  useEffect(() => {
    let isCancelled = false

    void Promise.all([getGestureClasses(), getGestureTypes()])
      .then(([classes, types]) => {
        if (isCancelled) {
          return
        }

        setGestureClasses(classes)
        setGestureTypes(types)
      })
      .catch(() => {
        if (!isCancelled) {
          toast.error('Unable to load gesture options')
        }
      })

    return () => {
      isCancelled = true
    }
  }, [])

  useEffect(() => {
    setStartFrameIndex(null)
    setEndFrameIndex(null)
  }, [video?.id])

  useEffect(() => {
    window.localStorage.setItem(
      SELECTED_GESTURE_CLASS_CACHE_KEY,
      selectedGestureClassId,
    )
  }, [selectedGestureClassId])

  useEffect(() => {
    window.localStorage.setItem(
      SELECTED_GESTURE_TYPE_CACHE_KEY,
      selectedGestureTypeId,
    )
  }, [selectedGestureTypeId])

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (shouldIgnoreHotkey(event)) {
        return
      }

      const key = event.key.toLowerCase()

      if (key === 'a') {
        event.preventDefault()
        stepFrame(-1)
        return
      }

      if (key === ' ') {
        event.preventDefault()
        void togglePlayback()
        return
      }

      if (key === 'd') {
        event.preventDefault()
        stepFrame(1)
        return
      }

      if (key === 'q') {
        event.preventDefault()
        setClipPoint('start')
        return
      }

      if (key === 'e') {
        event.preventDefault()
        setClipPoint('end')
        return
      }

      if (key === 'enter') {
        event.preventDefault()
        void saveClip()
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [saveClip, setClipPoint, stepFrame, togglePlayback])

  useEffect(() => {
    const timeline = timelineRef.current
    if (!timeline || !activeDuration) {
      return
    }

    const centerTarget = markerOffset - timeline.clientWidth / 2
    const maxScroll = Math.max(0, timeline.scrollWidth - timeline.clientWidth)
    timeline.scrollLeft = clamp(centerTarget, 0, maxScroll)
  }, [activeDuration, markerOffset])

  useEffect(() => {
    if (!video) {
      return
    }

    if (
      loadedAsset?.filepath === video.filepath ||
      failedVideoPath === video.filepath
    ) {
      return
    }

    let isCancelled = false

    void getDownloadUrl({ s3_key: video.filepath })
      .then((response) => {
        if (isCancelled) {
          return
        }

        resetPlaybackState()
        setLoadedAsset({
          url: response.url,
          name: video.name,
          filepath: video.filepath,
        })
        setFailedVideoPath(null)
      })
      .catch(() => {
        if (isCancelled) {
          return
        }

        setFailedVideoPath(video.filepath)
        toast.error('Unable to open the selected video in the editor')
      })

    return () => {
      isCancelled = true
    }
  }, [failedVideoPath, loadedAsset?.filepath, resetPlaybackState, video])

  return {
    activeCurrentTime,
    asset,
    clipPointMarkers,
    clipSelection,
    clipWidth,
    currentFrameTimeLabel: formatFrameTime(activeCurrentTime, fps),
    endFrameLabel: formatFrameIndex(endFrameIndex),
    fps,
    gestureClasses,
    gestureTypes,
    handleLoadedMetadata,
    handleSaveClip,
    handleTimeUpdate,
    handleTimelineSeek,
    isPlaying,
    isSavingClip,
    isVideoLoading,
    markerOffset,
    rulerMarks,
    selectedGestureClassId,
    selectedGestureTypeId,
    setClipPoint,
    setIsPlaying,
    setSelectedGestureClassId,
    setSelectedGestureTypeId,
    setZoom,
    startFrameLabel: formatFrameIndex(startFrameIndex),
    stepFrame,
    timelineRef,
    timelineWidth,
    togglePlayback,
    videoRef,
    zoom,
  }
}

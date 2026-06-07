import { useCallback, useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router'
import type { Dataset, Video } from '../actions'
import DatasetTable from '../components/DatasetTable'
import VideoEditor from '../components/VideoEditor'
import VideoTable from '../components/VideoTable'
import type { EditorRouteState } from '../routes'
import { panelClass, secondaryButtonClass } from '../ui/classes'

function isTextInputTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) {
    return false
  }

  return (
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement ||
    target instanceof HTMLSelectElement ||
    target.isContentEditable
  )
}

export default function EditorPage() {
  const location = useLocation()
  const routeState = location.state as EditorRouteState | null
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(
    routeState?.dataset ?? null,
  )
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(
    routeState?.video ?? null,
  )
  const [videos, setVideos] = useState<Video[]>([])
  const tableHeading = selectedDataset?.name ?? 'Datasets'

  const selectedVideoIndex = useMemo(() => {
    if (!selectedVideo) {
      return -1
    }

    return videos.findIndex((video) => video.id === selectedVideo.id)
  }, [selectedVideo, videos])

  const handleDatasetClick = (dataset: Dataset) => {
    setSelectedDataset(dataset)
    setSelectedVideo(null)
    setVideos([])
  }

  const handleVideosChange = useCallback((nextVideos: Video[]) => {
    setVideos(nextVideos)
    setSelectedVideo((currentVideo) => {
      if (nextVideos.length === 0) {
        return null
      }

      if (currentVideo && nextVideos.some((video) => video.id === currentVideo.id)) {
        return currentVideo
      }

      return nextVideos[0]
    })
  }, [])

  const selectVideoByOffset = useCallback(
    (offset: 1 | -1) => {
      if (videos.length === 0) {
        return
      }

      const currentIndex = selectedVideoIndex >= 0 ? selectedVideoIndex : 0
      const nextIndex = Math.min(
        Math.max(currentIndex + offset, 0),
        videos.length - 1,
      )
      setSelectedVideo(videos[nextIndex])
    },
    [selectedVideoIndex, videos],
  )

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (
        !selectedDataset ||
        event.altKey ||
        event.ctrlKey ||
        event.metaKey ||
        isTextInputTarget(event.target)
      ) {
        return
      }

      const key = event.key.toLowerCase()
      if (key === 'w') {
        event.preventDefault()
        selectVideoByOffset(-1)
      }

      if (key === 's') {
        event.preventDefault()
        selectVideoByOffset(1)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectVideoByOffset, selectedDataset])

  return (
    <section className="grid gap-[18px]">
      <VideoEditor video={selectedVideo} />

      {selectedDataset ? (
        <section className={panelClass}>
          <VideoTable
            datasetId={selectedDataset.id}
            heading={tableHeading}
            selectedVideoId={selectedVideo?.id ?? null}
            onVideoClick={setSelectedVideo}
            onRowsChange={handleVideosChange}
          />
          <footer className="flex justify-end border-t border-slate-400/10 bg-[#070b12]/35 px-[22px] py-4 max-[720px]:justify-stretch">
            <button
              className={`${secondaryButtonClass} max-[720px]:w-full`}
              type="button"
              onClick={() => {
                setSelectedDataset(null)
                setSelectedVideo(null)
                setVideos([])
              }}
            >
              Change Dataset
            </button>
          </footer>
        </section>
      ) : (
        <section className={panelClass}>
          <DatasetTable onDatasetClick={handleDatasetClick} />
        </section>
      )}
    </section>
  )
}

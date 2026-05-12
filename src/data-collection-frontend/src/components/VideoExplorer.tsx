import { useCallback, useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { getVideos } from '../actions'
import type { Dataset, Video } from '../actions'
import {
  panelClass,
  panelLabelClass,
  secondaryButtonClass,
} from '../ui/classes'

const PAGE = 0
const LIMIT = 50

type VideoExplorerProps = {
  dataset: Dataset
  onBack: () => void
}

export default function VideoExplorer({ dataset, onBack }: VideoExplorerProps) {
  const [videos, setVideos] = useState<Video[]>([])
  const [selectedVideoId, setSelectedVideoId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const loadVideos = useCallback(async () => {
    setIsLoading(true)

    try {
      const nextVideos = await getVideos({
        page: PAGE,
        limit: LIMIT,
        datasetId: dataset.id,
      })
      setVideos(nextVideos)
      setSelectedVideoId(nextVideos[0]?.id ?? null)
    } catch {
      setVideos([])
      setSelectedVideoId(null)
      toast.error('Unable to load videos')
    } finally {
      setIsLoading(false)
    }
  }, [dataset.id])

  useEffect(() => {
    loadVideos()
  }, [loadVideos])

  const selectedVideo = useMemo(
    () => videos.find((video) => video.id === selectedVideoId) ?? null,
    [selectedVideoId, videos],
  )

  return (
    <section className="grid gap-[18px]">
      <div className={panelClass}>
        <header className="flex items-start justify-between gap-[18px] border-b border-slate-400/10 px-[22px] py-5 max-[720px]:grid">
          <h2 className="mt-2 mb-0 text-[1.35rem] font-semibold tracking-normal text-[#f5f7fb]">
            {dataset.name}
          </h2>
        </header>

        <p
          className="m-0 border-b border-slate-400/10 bg-[#070b12]/35 px-4 py-3 text-sm whitespace-nowrap text-[#738099]"
          aria-label="Explorer location"
        >
          {isLoading ? 'Loading' : `${videos.length} videos`}
        </p>

        {isLoading ? (
          <ExplorerState title="Loading videos" />
        ) : videos.length === 0 ? (
          <ExplorerState
            title="No videos found"
            description="This dataset does not contain videos on page 0."
          />
        ) : (
          <div className="grid min-h-[430px] grid-cols-[minmax(0,1fr)_300px] max-[980px]:grid-cols-1">
            <div className="overflow-x-auto" role="listbox" aria-label="Dataset videos">
              <div
                className="grid min-w-[720px] grid-cols-[minmax(220px,1.2fr)_minmax(240px,1fr)_92px] items-center border-b border-slate-400/10 bg-[#070b12]/50 px-[18px] py-2.5 text-xs font-semibold tracking-[0.12em] text-[#738099] uppercase"
                aria-hidden="true"
              >
                <span>Name</span>
                <span>Path</span>
                <span>ID</span>
              </div>

              {videos.map((video) => (
                <button
                  key={video.id}
                  className={[
                    'grid min-w-[720px] w-full grid-cols-[minmax(220px,1.2fr)_minmax(240px,1fr)_92px] items-center border-0 border-b border-slate-400/10 px-[18px] py-[11px] text-left transition duration-150 focus-visible:outline-none',
                    video.id === selectedVideoId
                      ? 'bg-emerald-300/10 text-[#f5f7fb]'
                      : 'bg-transparent text-[#a8b0c3] hover:bg-slate-400/5 hover:text-[#f5f7fb] focus-visible:bg-slate-400/5 focus-visible:text-[#f5f7fb]',
                  ].join(' ')}
                  type="button"
                  role="option"
                  aria-selected={video.id === selectedVideoId}
                  onClick={() => setSelectedVideoId(video.id)}
                >
                  <span className="inline-flex min-w-0 items-center gap-2.5">
                    <span
                      className="h-[22px] w-[22px] shrink-0 text-blue-400 [&_svg]:block [&_svg]:h-full [&_svg]:w-full"
                      aria-hidden="true"
                    >
                      <VideoFileIcon />
                    </span>
                    <span className="overflow-hidden text-ellipsis whitespace-nowrap font-semibold text-[#f5f7fb]">
                      {video.name}
                    </span>
                  </span>
                  <span className="overflow-hidden text-ellipsis whitespace-nowrap text-sm text-[#738099]">
                    {video.filepath}
                  </span>
                  <span className="overflow-hidden text-ellipsis whitespace-nowrap text-sm text-[#738099]">
                    #{video.id}
                  </span>
                </button>
              ))}
            </div>

            <aside
              className="border-l border-slate-400/10 bg-[#070b12]/20 p-[18px] max-[980px]:border-t max-[980px]:border-l-0"
              aria-label="Selected video details"
            >
              <p className={panelLabelClass}>Details</p>
              {selectedVideo ? (
                <>
                  <h3 className="mt-2.5 mb-[18px] text-[1.05rem] font-semibold tracking-normal text-[#f5f7fb] [overflow-wrap:anywhere]">
                    {selectedVideo.name}
                  </h3>
                  <dl className="m-0 grid gap-3.5">
                    <div>
                      <dt className="text-xs font-semibold tracking-[0.12em] text-[#738099] uppercase">
                        ID
                      </dt>
                      <dd className="mt-1 mb-0 text-[#a8b0c3] [overflow-wrap:anywhere]">
                        {selectedVideo.id}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs font-semibold tracking-[0.12em] text-[#738099] uppercase">
                        File path
                      </dt>
                      <dd className="mt-1 mb-0 text-[#a8b0c3] [overflow-wrap:anywhere]">
                        {selectedVideo.filepath}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs font-semibold tracking-[0.12em] text-[#738099] uppercase">
                        Dataset
                      </dt>
                      <dd className="mt-1 mb-0 text-[#a8b0c3] [overflow-wrap:anywhere]">
                        {dataset.name}
                      </dd>
                    </div>
                  </dl>
                </>
              ) : (
                <p className="text-[#a8b0c3]">Select a video to inspect it.</p>
              )}
            </aside>
          </div>
        )}
      </div>
      <div>
        <button
          className={`${secondaryButtonClass} max-[720px]:w-full`}
          type="button"
          onClick={onBack}
        >
          Back to Datasets
        </button>
      </div>
    </section>
  )
}

type ExplorerStateProps = {
  title: string
  description?: string
}

function ExplorerState({
  title,
  description,
}: ExplorerStateProps) {
  return (
    <div className="grid min-h-[360px] place-items-center p-9 text-center text-[#a8b0c3]">
      <div className="max-w-[460px]">
        <p className={panelLabelClass}>Status</p>
        <h3 className="mt-2.5 mb-2 text-[1.05rem] font-semibold tracking-normal text-current">
          {title}
        </h3>
        {description ? <p className="mb-0">{description}</p> : null}
      </div>
    </div>
  )
}
// TODO: Uploadowanie filmów na backend
function VideoFileIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M6 3.75h8.25L18 7.5v12.75H6V3.75Zm8 1.8V8h2.45L14 5.55ZM8 10.25v7.5h8v-7.5H8Zm1.4 1.65 2.1 1.35v-1.1h3.1v3.7h-3.1v-1.1L9.4 16.1v-4.2Z"
        fill="currentColor"
      />
    </svg>
  )
}

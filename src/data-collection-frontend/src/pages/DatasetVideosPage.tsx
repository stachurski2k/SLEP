import { useEffect, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import {
  createImportVideoJob,
  getDownloadUrl,
  getUploadUrl,
  uploadFileToSignedUrl,
} from '../actions'
import type { ImportVideoUploadPayload, Video } from '../actions'
import ImportVideoDialog from '../components/ImportVideoDialog'
import VideoTable from '../components/VideoTable'
import { routes } from '../routes'
import type { DatasetRouteState, EditorRouteState } from '../routes'
import {
  fieldLabelClass,
  panelClass,
  panelLabelClass,
  primaryButtonClass,
  secondaryButtonClass,
} from '../ui/classes'

const detailPanelClass =
  'border-t border-slate-400/10 bg-[#070b12]/20 p-[18px] lg:border-t-0 lg:border-l'
const detailTitleClass =
  'mt-2.5 mb-[18px] text-[1.05rem] font-semibold tracking-normal text-[#f5f7fb] [overflow-wrap:anywhere]'
const detailValueClass =
  'mt-1 mb-0 text-[#a8b0c3] [overflow-wrap:anywhere]'

export default function DatasetVideosPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { datasetId } = useParams()
  const routeState = location.state as DatasetRouteState | null
  const parsedDatasetId = Number(datasetId)
  const dataset =
    routeState?.dataset?.id === parsedDatasetId ? routeState.dataset : null
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [tableRefreshKey, setTableRefreshKey] = useState(0)
  const [selectedVideoState, setSelectedVideoState] = useState<{
    datasetId: number
    video: Video | null
  }>({
    datasetId: parsedDatasetId,
    video: null,
  })
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isPreviewLoading, setIsPreviewLoading] = useState(false)
  const selectedVideo =
    selectedVideoState.datasetId === parsedDatasetId
      ? selectedVideoState.video
      : null

  useEffect(() => {
    if (!selectedVideo) {
      setPreviewUrl(null)
      setIsPreviewLoading(false)
      return
    }

    let isCancelled = false

    setPreviewUrl(null)
    setIsPreviewLoading(true)

    void getDownloadUrl({ s3_key: selectedVideo.filepath })
      .then((response) => {
        if (isCancelled) {
          return
        }

        setPreviewUrl(response.url)
      })
      .catch(() => {
        if (isCancelled) {
          return
        }

        toast.error('Unable to load video preview')
      })
      .finally(() => {
        if (isCancelled) {
          return
        }

        setIsPreviewLoading(false)
      })

    return () => {
      isCancelled = true
    }
  }, [selectedVideo])

  if (!Number.isInteger(parsedDatasetId)) {
    toast.error('Invalid dataset ID')
    navigate(routes.datasets, { replace: true })
    return null
  }

  const tableHeading = dataset?.name ?? `Dataset #${parsedDatasetId}`

  const handleImportVideo = async (payload: ImportVideoUploadPayload) => {
    setIsSubmitting(true)

    try {
      const contentType = payload.video_file.type || 'video/mp4'
      const uploadTarget = await getUploadUrl({
        s3_key: buildVideoUploadKey(payload.dataset_id, payload.video_file.name),
        content_type: contentType,
      })

      await uploadFileToSignedUrl(uploadTarget.url, payload.video_file, contentType)
      await createImportVideoJob({
        video_name: payload.video_name,
        video_filepath: uploadTarget.key,
        video_description: payload.video_description,
        dataset_id: payload.dataset_id,
      })

      setTableRefreshKey((currentValue) => currentValue + 1)
      setIsDialogOpen(false)
    } catch {
      toast.error('Unable to upload and import video')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCloseDialog = () => {
    if (isSubmitting) {
      return
    }

    setIsDialogOpen(false)
  }

  const handleOpenInEditor = (video?: Video) => {
    const editorState: EditorRouteState = {
      dataset: dataset ?? {
        id: parsedDatasetId,
        name: tableHeading,
        description: '',
      },
      video,
    }

    navigate(routes.editor, {
      state: editorState,
    })
  }

  return (
    <>
      <section className="grid gap-[18px]">
        <div
          className={`${panelClass} lg:grid lg:grid-cols-[minmax(0,1fr)_30%] lg:items-start`}
        >
          <div className="min-w-0">
            <VideoTable
              datasetId={parsedDatasetId}
              heading={tableHeading}
              refreshKey={tableRefreshKey}
              onVideoClick={(video) =>
                setSelectedVideoState({ datasetId: parsedDatasetId, video })
              }
              selectedVideoId={selectedVideo?.id ?? null}
            />
          </div>

          <aside className={detailPanelClass} aria-label="Selected video details">
            <p className={panelLabelClass}>Details</p>
            {selectedVideo ? (
              <>
                <div className="mt-2.5 mx-auto w-full max-w-[100%] overflow-hidden rounded-[18px] border border-slate-200/10 bg-[#02050b]">
                  {previewUrl ? (
                    <video
                      key={previewUrl}
                      className="block aspect-video w-full bg-black"
                      controls
                      preload="metadata"
                      src={previewUrl}
                    >
                      Your browser does not support video playback.
                    </video>
                  ) : (
                    <div className="flex aspect-video items-center justify-center px-4 text-center text-sm text-[#738099]">
                      {isPreviewLoading ? 'Loading video preview...' : 'Video preview unavailable.'}
                    </div>
                  )}
                </div>
                <h3 className={detailTitleClass}>{selectedVideo.name}</h3>
                <dl className="m-0 grid gap-3.5">
                  <div>
                    <dt className={fieldLabelClass}>ID</dt>
                    <dd className={detailValueClass}>{selectedVideo.id}</dd>
                  </div>
                  <div>
                    <dt className={fieldLabelClass}>File path</dt>
                    <dd className={detailValueClass}>{selectedVideo.filepath}</dd>
                  </div>
                  <div>
                    <dt className={fieldLabelClass}>Dataset</dt>
                    <dd className={detailValueClass}>{tableHeading}</dd>
                  </div>
                </dl>
                <div className="mt-5 flex justify-end">
                  <button
                    className={primaryButtonClass}
                    type="button"
                    onClick={() => handleOpenInEditor(selectedVideo)}
                  >
                    Open in Editor
                  </button>
                </div>
              </>
            ) : (
              <p className="text-[#a8b0c3]">Select a video to inspect it.</p>
            )}
          </aside>
        </div>
        <div className="flex justify-end gap-2.5 max-[720px]:grid">
          <button
            className={`${secondaryButtonClass} max-[720px]:w-full`}
            type="button"
            onClick={() => navigate(routes.datasets)}
          >
            Back to Datasets
          </button>
          <button
            className={`${secondaryButtonClass} max-[720px]:w-full`}
            type="button"
            onClick={() => handleOpenInEditor()}
          >
            Open Dataset in Editor
          </button>
          <button
            className={`${primaryButtonClass} max-[720px]:w-full`}
            type="button"
            onClick={() => setIsDialogOpen(true)}
          >
            Import Video
          </button>
        </div>
      </section>

      {isDialogOpen ? (
        <ImportVideoDialog
          datasetId={parsedDatasetId}
          datasetName={tableHeading}
          isSubmitting={isSubmitting}
          onCancel={handleCloseDialog}
          onSubmit={handleImportVideo}
        />
      ) : null}
    </>
  )
}

function buildVideoUploadKey(datasetId: number, filename: string) {
  const sanitizedFilename = filename
    .replaceAll('\\', '-')
    .replaceAll('/', '-')
    .replace(/\s+/g, '-')

  return `videos/dataset-${datasetId}/${sanitizedFilename}`
}

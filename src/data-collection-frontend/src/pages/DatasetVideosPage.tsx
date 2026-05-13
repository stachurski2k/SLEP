import { useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { createImportVideoJob } from '../actions'
import type { ImportVideoJobPayload, Video } from '../actions'
import CustomTable from '../components/CustomTable'
import type { CustomTableColumn } from '../components/CustomTable'
import ImportVideoDialog from '../components/ImportVideoDialog'
import { routes } from '../routes'
import type { DatasetRouteState } from '../routes'
import {
  fieldLabelClass,
  panelClass,
  panelLabelClass,
  primaryButtonClass,
  secondaryButtonClass,
} from '../ui/classes'

const PAGE = 0
const LIMIT = 50
const detailPanelClass = 'border-t border-slate-400/10 bg-[#070b12]/20 p-[18px]'
const detailTitleClass =
  'mt-2.5 mb-[18px] text-[1.05rem] font-semibold tracking-normal text-[#f5f7fb] [overflow-wrap:anywhere]'
const detailValueClass =
  'mt-1 mb-0 text-[#a8b0c3] [overflow-wrap:anywhere]'
const truncatedTextClass = 'overflow-hidden text-ellipsis whitespace-nowrap'

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
  const [selectedVideoState, setSelectedVideoState] = useState<{
    datasetId: number
    video: Video | null
  }>({
    datasetId: parsedDatasetId,
    video: null,
  })
  const selectedVideo =
    selectedVideoState.datasetId === parsedDatasetId
      ? selectedVideoState.video
      : null

  const columns = useMemo<CustomTableColumn<Video>[]>(
    () => [
      {
        id: 'id',
        header: 'ID',
        className:
          'w-24 text-[#738099] [font-variant-numeric:tabular-nums]',
        render: (video) => video.id,
      },
      {
        id: 'name',
        header: 'Name',
        className: 'w-[260px] font-semibold text-[#f5f7fb]',
        render: (video) => <span className={truncatedTextClass}>{video.name}</span>,
      },
      {
        id: 'filepath',
        header: 'Path',
        className: 'text-[#738099]',
        render: (video) => video.filepath,
      },
    ],
    [],
  )

  if (!Number.isInteger(parsedDatasetId)) {
    toast.error('Invalid dataset ID')
    navigate(routes.datasets, { replace: true })
    return null
  }

  const videosUrl = `/api/v1/videos/?page=${PAGE}&limit=${LIMIT}&dataset_id=${parsedDatasetId}`
  const tableHeading = dataset?.name ?? `Dataset #${parsedDatasetId}`

  const handleImportVideo = async (payload: ImportVideoJobPayload) => {
    setIsSubmitting(true)

    try {
      await createImportVideoJob(payload)
      setIsDialogOpen(false)
    } catch {
      toast.error('Unable to start video import')
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

  return (
    <>
      <section className="grid gap-[18px]">
        <div className={panelClass}>
          <CustomTable<Video>
            label="videos"
            heading={tableHeading}
            columns={columns}
            url={videosUrl}
            getRowKey={(video) => video.id}
            onRowClick={(video) =>
              setSelectedVideoState({ datasetId: parsedDatasetId, video })
            }
            rowAriaLabel={(video) => `Select video ${video.name}`}
            selectedRowKey={selectedVideo?.id ?? null}
            emptyDescription="This dataset does not contain videos on page 0."
          />

          <aside className={detailPanelClass} aria-label="Selected video details">
            <p className={panelLabelClass}>Details</p>
            {selectedVideo ? (
              <>
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

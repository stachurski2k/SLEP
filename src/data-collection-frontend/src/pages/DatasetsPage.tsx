import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { createDataset, deleteDataset } from '../actions'
import type { Dataset, DatasetPayload } from '../actions'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog'
import type { CustomTableAction } from '../components/CustomTable'
import DatasetTable from '../components/DatasetTable'
import DatasetEditorDialog from '../components/DatasetEditorDialog'
import TrashIcon from '../components/icons/TrashIcon'
import { getDatasetVideosPath } from '../routes'
import type { DatasetRouteState } from '../routes'
import { panelClass, primaryButtonClass } from '../ui/classes'

export default function DatasetsPage() {
  const navigate = useNavigate()
  const [tableRefreshKey, setTableRefreshKey] = useState(0)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [datasetPendingDelete, setDatasetPendingDelete] = useState<Dataset | null>(
    null,
  )
  const [isDeleting, setIsDeleting] = useState(false)

  const handleOpenDataset = (dataset: Dataset) => {
    navigate(getDatasetVideosPath(dataset.id), {
      state: { dataset } satisfies DatasetRouteState,
    })
  }

  const actions = useMemo<CustomTableAction<Dataset>[]>(
    () => [
      {
        id: 'delete',
        label: 'Delete dataset',
        ariaLabel: (dataset) => `Delete dataset ${dataset.name}`,
        onClick: (dataset) => setDatasetPendingDelete(dataset),
        icon: <TrashIcon />,
        className:
          'hover:border-rose-400/40 hover:bg-rose-400/10 hover:text-rose-200 focus-visible:outline-rose-300',
      },
    ],
    [],
  )

  const handleCreateDataset = async (payload: DatasetPayload) => {
    setIsSubmitting(true)

    try {
      await createDataset(payload)
      setIsDialogOpen(false)
      setTableRefreshKey((currentKey) => currentKey + 1)
    } catch {
      toast.error('Unable to create dataset')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteDataset = async () => {
    if (!datasetPendingDelete) {
      return
    }

    setIsDeleting(true)

    try {
      await deleteDataset(datasetPendingDelete.id)
      setDatasetPendingDelete(null)
      setTableRefreshKey((currentKey) => currentKey + 1)
    } catch {
      toast.error('Unable to delete dataset')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <>
      <section className={panelClass}>
        <DatasetTable
          actions={actions}
          refreshKey={tableRefreshKey}
          onDatasetClick={handleOpenDataset}
        />

        <footer className="flex justify-end border-t border-slate-400/10 bg-[#070b12]/35 px-[22px] py-4 max-[720px]:justify-stretch">
          <button
            className={`${primaryButtonClass} max-[720px]:w-full`}
            type="button"
            onClick={() => setIsDialogOpen(true)}
          >
            Add Dataset
          </button>
        </footer>
      </section>

      {isDialogOpen ? (
        <DatasetEditorDialog
          isSubmitting={isSubmitting}
          onCancel={() => setIsDialogOpen(false)}
          onSubmit={handleCreateDataset}
        />
      ) : null}

      {datasetPendingDelete ? (
        <ConfirmDeleteDialog
          sectionLabel="Deleting Dataset"
          description={
            <p className="m-0">
              Delete{' '}
              <span className="font-semibold text-[#f5f7fb]">
                {datasetPendingDelete.name}
              </span>
              ?
            </p>
          }
          isDeleting={isDeleting}
          onCancel={() => {
            if (!isDeleting) {
              setDatasetPendingDelete(null)
            }
          }}
          onDelete={handleDeleteDataset}
        />
      ) : null}
    </>
  )
}

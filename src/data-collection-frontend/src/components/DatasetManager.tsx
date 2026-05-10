import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { createDataset, deleteDataset, getDatasets } from '../actions'
import type { Dataset, DatasetPayload } from '../actions'
import ConfirmDeleteDialog from './ConfirmDeleteDialog'
import DatasetEditorDialog from './DatasetEditorDialog'
import {
  panelClass,
  panelLabelClass,
  primaryButtonClass,
  summaryPillClass,
} from '../ui/classes'

type DatasetManagerProps = {
  onOpenDataset: (dataset: Dataset) => void
}

export default function DatasetManager({ onOpenDataset }: DatasetManagerProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [datasetPendingDelete, setDatasetPendingDelete] = useState<Dataset | null>(
    null,
  )
  const [isDeleting, setIsDeleting] = useState(false)

  const loadDatasets = useCallback(async () => {
    setIsLoading(true)

    try {
      const nextDatasets = await getDatasets()
      setDatasets(nextDatasets)
    } catch {
      setDatasets([])
      toast.error('Unable to load datasets')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDatasets()
  }, [loadDatasets])

  const handleCreateDataset = async (payload: DatasetPayload) => {
    setIsSubmitting(true)

    try {
      await createDataset(payload)
      setIsDialogOpen(false)
      await loadDatasets()
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
      await loadDatasets()
    } catch {
      toast.error('Unable to delete dataset')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <>
      <section className={panelClass}>
        <header className="flex items-start justify-between gap-[18px] border-b border-slate-400/10 px-[22px] py-5 max-[720px]:grid">
          <h2 className="mt-2 mb-0 text-[1.35rem] font-semibold tracking-normal text-[#f5f7fb]">
            Dataset Manager
          </h2>
          <div className={`${summaryPillClass} max-[720px]:w-fit`}>
            {isLoading ? 'Loading' : `${datasets.length} datasets`}
          </div>
        </header>

        {isLoading ? (
          <DatasetState title="Loading datasets" />
        ) : datasets.length === 0 ? (
          <DatasetState
            title="No datasets found"
            description="Create a dataset in the backend to see it here."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[780px] border-collapse">
              <thead>
                <tr>
                  <th
                    className="border-b border-slate-400/10 bg-[#070b12]/50 px-[18px] py-4 text-left align-top text-xs font-semibold tracking-[0.12em] text-[#738099] uppercase"
                    scope="col"
                  >
                    ID
                  </th>
                  <th
                    className="border-b border-slate-400/10 bg-[#070b12]/50 px-[18px] py-4 text-left align-top text-xs font-semibold tracking-[0.12em] text-[#738099] uppercase"
                    scope="col"
                  >
                    Name
                  </th>
                  <th
                    className="border-b border-slate-400/10 bg-[#070b12]/50 px-[18px] py-4 text-left align-top text-xs font-semibold tracking-[0.12em] text-[#738099] uppercase"
                    scope="col"
                  >
                    Description
                  </th>
                  <th
                    className="w-16 border-b border-slate-400/10 bg-[#070b12]/50 px-[18px] py-4 text-right align-top"
                    scope="col"
                    aria-label="Actions"
                  />
                </tr>
              </thead>
              <tbody>
                {datasets.map((dataset) => (
                  <tr
                    key={dataset.id}
                    className="cursor-pointer outline-none transition-colors duration-150 hover:bg-slate-400/5 focus-visible:bg-slate-400/5 focus-visible:[&>td:first-child]:shadow-[inset_3px_0_0_#3dd9b3] [&:last-child>td]:border-b-0"
                    tabIndex={0}
                    role="button"
                    aria-label={`Open dataset ${dataset.name}`}
                    onClick={() => onOpenDataset(dataset)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        onOpenDataset(dataset)
                      }
                    }}
                  >
                    <td className="w-24 border-b border-slate-400/10 px-[18px] py-4 align-top text-[#738099] [font-variant-numeric:tabular-nums]">
                      {dataset.id}
                    </td>
                    <td className="w-[260px] border-b border-slate-400/10 px-[18px] py-4 align-top font-semibold text-[#f5f7fb]">
                      {dataset.name}
                    </td>
                    <td className="border-b border-slate-400/10 px-[18px] py-4 align-top text-[#a8b0c3]">
                      {dataset.description || 'No description'}
                    </td>
                    <td className="border-b border-slate-400/10 px-[18px] py-4 align-top text-right">
                      <button
                        className="inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-[12px] border border-slate-400/15 bg-slate-400/5 text-[#738099] transition duration-150 hover:-translate-y-px hover:border-rose-400/40 hover:bg-rose-400/10 hover:text-rose-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-300 disabled:cursor-not-allowed disabled:opacity-50"
                        type="button"
                        aria-label={`Delete dataset ${dataset.name}`}
                        onClick={(event) => {
                          event.stopPropagation()
                          setDatasetPendingDelete(dataset)
                        }}
                        onKeyDown={(event) => {
                          event.stopPropagation()
                        }}
                      >
                        <TrashIcon />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

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

type DatasetStateProps = {
  title: string
  description?: string
}

function DatasetState({
  title,
  description,
}: DatasetStateProps) {
  return (
    <div className="grid min-h-[220px] place-items-center p-9 text-center text-[#a8b0c3]">
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

function TrashIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="h-[18px] w-[18px]"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 6h18" />
      <path d="M8 6V4.75C8 4.34 8.34 4 8.75 4h6.5c.41 0 .75.34.75.75V6" />
      <path d="M6.75 6l.7 11.11A2 2 0 0 0 9.44 19h5.12a2 2 0 0 0 1.99-1.89L17.25 6" />
      <path d="M10 10.25v5.5" />
      <path d="M14 10.25v5.5" />
    </svg>
  )
}

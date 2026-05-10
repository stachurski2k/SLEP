import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { createDataset, getDatasets } from '../actions'
import type { Dataset, DatasetPayload } from '../actions'
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
            <table className="w-full min-w-[720px] border-collapse">
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

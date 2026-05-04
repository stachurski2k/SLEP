import { useCallback, useEffect, useState } from 'react'
import { createDataset, getDatasets } from '../actions'
import type { Dataset, DatasetPayload } from '../actions'
import DatasetEditorDialog from './DatasetEditorDialog'
import './DatasetManager.css'

export default function DatasetManager() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const loadDatasets = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const nextDatasets = await getDatasets()
      setDatasets(nextDatasets)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Unable to load datasets',
      )
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDatasets()
  }, [loadDatasets])

  const handleCreateDataset = async (payload: DatasetPayload) => {
    setIsSubmitting(true)
    setSubmitError(null)

    try {
      await createDataset(payload)
      setIsDialogOpen(false)
      await loadDatasets()
    } catch (requestError) {
      setSubmitError(
        requestError instanceof Error
          ? requestError.message
          : 'Unable to create dataset',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="dataset-manager">
      <div className="dataset-panel">
        <header className="dataset-panel-header">
          <div>
            <p className="panel-label">Dataset Manager</p>
            <h2>Datasets</h2>
          </div>
          <div className="dataset-summary">
            {isLoading ? 'Loading' : `${datasets.length} datasets`}
          </div>
        </header>

        {isLoading ? (
          <DatasetState title="Loading datasets" />
        ) : error ? (
          <DatasetState
            title="Datasets unavailable"
            description={error}
            variant="error"
          />
        ) : datasets.length === 0 ? (
          <DatasetState
            title="No datasets found"
            description="Create a dataset in the backend to see it here."
          />
        ) : (
          <div className="dataset-table-wrap">
            <table className="dataset-table">
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Name</th>
                  <th scope="col">Description</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((dataset) => (
                  <tr key={dataset.id}>
                    <td className="dataset-id">{dataset.id}</td>
                    <td className="dataset-name">{dataset.name}</td>
                    <td className="dataset-description">
                      {dataset.description || 'No description'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <footer className="dataset-panel-footer">
          <button
            className="dataset-button"
            type="button"
            onClick={() => {
              setSubmitError(null)
              setIsDialogOpen(true)
            }}
          >
            Add Dataset
          </button>
        </footer>
      </div>

      {isDialogOpen ? (
        <DatasetEditorDialog
          isSubmitting={isSubmitting}
          error={submitError}
          onCancel={() => setIsDialogOpen(false)}
          onSubmit={handleCreateDataset}
        />
      ) : null}
    </section>
  )
}

type DatasetStateProps = {
  title: string
  description?: string
  variant?: 'default' | 'error'
}

function DatasetState({
  title,
  description,
  variant = 'default',
}: DatasetStateProps) {
  return (
    <div className="dataset-state">
      <div
        className={`dataset-state-content${
          variant === 'error' ? ' dataset-error' : ''
        }`}
      >
        <p className="panel-label">Status</p>
        <h3>{title}</h3>
        {description ? <p>{description}</p> : null}
      </div>
    </div>
  )
}

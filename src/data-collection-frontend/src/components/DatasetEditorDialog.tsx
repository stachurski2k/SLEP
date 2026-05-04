import { useState } from 'react'
import type { FormEvent } from 'react'
import type { DatasetPayload } from '../actions'
import './DatasetEditorDialog.css'

type DatasetEditorDialogProps = {
  isSubmitting: boolean
  error: string | null
  onCancel: () => void
  onSubmit: (payload: DatasetPayload) => Promise<void>
}

export default function DatasetEditorDialog({
  isSubmitting,
  error,
  onCancel,
  onSubmit,
}: DatasetEditorDialogProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  const isSubmitDisabled = isSubmitting || !name.trim() || !description.trim()

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (isSubmitDisabled) {
      return
    }

    await onSubmit({
      name: name.trim(),
      description: description.trim(),
    })
  }

  return (
    <div className="dialog-backdrop" role="presentation">
      <section
        className="dataset-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dataset-dialog-title"
      >
        <header className="dataset-dialog-header">
          <p className="panel-label">Dataset editor</p>
          <h2 id="dataset-dialog-title">Add Dataset</h2>
        </header>

        <form className="dataset-dialog-form" onSubmit={handleSubmit}>
          <div className="dataset-field">
            <label htmlFor="dataset-name">Name</label>
            <input
              id="dataset-name"
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              disabled={isSubmitting}
              autoFocus
            />
          </div>

          <div className="dataset-field">
            <label htmlFor="dataset-description">Description</label>
            <textarea
              id="dataset-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              disabled={isSubmitting}
            />
          </div>

          {error ? <p className="dataset-dialog-error">{error}</p> : null}

          <div className="dataset-dialog-actions">
            <button
              className="dataset-button dataset-button-secondary"
              type="button"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              className="dataset-button"
              type="submit"
              disabled={isSubmitDisabled}
            >
              {isSubmitting ? 'Submitting' : 'Submit'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

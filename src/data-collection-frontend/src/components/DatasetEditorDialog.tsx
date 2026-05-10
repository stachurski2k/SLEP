import { useState } from 'react'
import type { FormEvent } from 'react'
import type { DatasetPayload } from '../actions'
import {
  fieldControlClass,
  fieldLabelClass,
  panelClass,
  panelLabelClass,
  primaryButtonClass,
  secondaryButtonClass,
} from '../ui/classes'

type DatasetEditorDialogProps = {
  isSubmitting: boolean
  onCancel: () => void
  onSubmit: (payload: DatasetPayload) => Promise<void>
}

export default function DatasetEditorDialog({
  isSubmitting,
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
    <div
      className="fixed inset-0 z-20 grid place-items-center bg-[#03060c]/70 p-6 backdrop-blur-xl max-[560px]:items-end max-[560px]:p-3.5"
      role="presentation"
    >
      <section
        className={`${panelClass} w-full max-w-[520px]`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dataset-dialog-title"
      >
        <header className="border-b border-slate-400/10 px-[22px] py-5">
          <p className={panelLabelClass}>Dataset editor</p>
          <h2
            className="mt-2 mb-0 text-[1.35rem] font-semibold tracking-normal text-[#f5f7fb]"
            id="dataset-dialog-title"
          >
            Add Dataset
          </h2>
        </header>

        <form className="grid gap-[18px] p-[22px]" onSubmit={handleSubmit}>
          <div className="grid gap-2">
            <label className={fieldLabelClass} htmlFor="dataset-name">
              Name
            </label>
            <input
              id="dataset-name"
              className={fieldControlClass}
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              disabled={isSubmitting}
              autoFocus
            />
          </div>

          <div className="grid gap-2">
            <label className={fieldLabelClass} htmlFor="dataset-description">
              Description
            </label>
            <textarea
              id="dataset-description"
              className={`${fieldControlClass} min-h-[118px] resize-y`}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="flex justify-end gap-2.5 max-[560px]:grid">
            <button
              className={secondaryButtonClass}
              type="button"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              className={primaryButtonClass}
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

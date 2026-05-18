import { useState } from 'react'
import type { FormEvent } from 'react'
import type { GestureClassPayload } from '../actions'
import {
  fieldControlClass,
  fieldLabelClass,
  panelClass,
  panelLabelClass,
  primaryButtonClass,
  secondaryButtonClass,
} from '../ui/classes'

type GestureClassEditorDialogProps = {
  isEditMode: boolean
  isSubmitting: boolean
  gestureClassId?: number
  initialName?: string
  onCancel: () => void
  onSubmit: (
    payload: GestureClassPayload,
    gestureClassId?: number,
  ) => Promise<void>
}

export default function GestureClassEditorDialog({
  isEditMode,
  isSubmitting,
  gestureClassId,
  initialName = '',
  onCancel,
  onSubmit,
}: GestureClassEditorDialogProps) {
  const [name, setName] = useState(initialName)

  const isSubmitDisabled =
    isSubmitting || !name.trim() || (isEditMode && gestureClassId === undefined)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (isSubmitDisabled) {
      return
    }

    await onSubmit(
      {
        name: name.trim(),
      },
      gestureClassId,
    )
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
        aria-labelledby="gesture-class-dialog-title"
      >
        <header className="border-b border-slate-400/10 px-[22px] py-5">
          <p className={panelLabelClass}>Gesture class editor</p>
          <h2
            className="mt-2 mb-0 text-[1.35rem] font-semibold tracking-normal text-[#f5f7fb]"
            id="gesture-class-dialog-title"
          >
            {isEditMode ? 'Edit Gesture Class' : 'Add Gesture Class'}
          </h2>
        </header>

        <form className="grid gap-[18px] p-[22px]" onSubmit={handleSubmit}>
          <div className="grid gap-2">
            <label className={fieldLabelClass} htmlFor="gesture-class-name">
              Name
            </label>
            <input
              id="gesture-class-name"
              className={fieldControlClass}
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              disabled={isSubmitting}
              autoFocus
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
              {isSubmitting
                ? 'Submitting'
                : isEditMode
                  ? 'Save Changes'
                  : 'Submit'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

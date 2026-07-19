import type { ReactNode } from 'react'
import {
  panelClass,
  panelLabelClass,
  primaryButtonClass,
  secondaryButtonClass,
} from '../ui/classes'

type ConfirmDeleteDialogProps = {
  description: ReactNode
  isDeleting: boolean
  onCancel: () => void
  onDelete: () => Promise<void> | void
  title?: string
  cancelLabel?: string
  deleteLabel?: string
  sectionLabel?: string
}

export default function ConfirmDeleteDialog({
  description,
  isDeleting,
  onCancel,
  onDelete,
  title = 'Are you sure?',
  cancelLabel = 'cancel',
  deleteLabel = 'delete',
  sectionLabel = 'Delete',
}: ConfirmDeleteDialogProps) {
  return (
    <div
      className="fixed inset-0 z-20 grid place-items-center bg-[#03060c]/70 p-6 backdrop-blur-xl max-[560px]:items-end max-[560px]:p-3.5"
      role="presentation"
    >
      <section
        className={`${panelClass} w-full max-w-[460px]`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-delete-dialog-title"
      >
        <header className="border-b border-slate-400/10 px-[22px] py-5">
          <p className={panelLabelClass}>{sectionLabel}</p>
          <h2
            className="mt-2 mb-0 text-[1.35rem] font-semibold tracking-normal text-[#f5f7fb]"
            id="confirm-delete-dialog-title"
          >
            {title}
          </h2>
        </header>

        <div className="grid gap-5 p-[22px]">
          <div className="text-[#a8b0c3]">{description}</div>

          <div className="flex justify-end gap-2.5 max-[560px]:grid">
            <button
              className={secondaryButtonClass}
              type="button"
              onClick={onCancel}
              disabled={isDeleting}
            >
              {cancelLabel}
            </button>
            <button
              className={`${primaryButtonClass} border-rose-400/20 bg-[linear-gradient(180deg,rgba(248,113,113,0.16),rgba(244,63,94,0.12))] hover:border-rose-400/40`}
              type="button"
              onClick={() => {
                void onDelete()
              }}
              disabled={isDeleting}
            >
              {isDeleting ? 'deleting' : deleteLabel}
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}

import { useState } from 'react'
import type { FormEvent } from 'react'
import type { ImportVideoJobPayload } from '../actions'
import {
  fieldControlClass,
  fieldLabelClass,
  panelClass,
  panelLabelClass,
  primaryButtonClass,
  secondaryButtonClass,
} from '../ui/classes'

type ImportVideoDialogProps = {
  datasetId: number
  datasetName: string
  isSubmitting: boolean
  onCancel: () => void
  onSubmit: (payload: ImportVideoJobPayload) => Promise<void>
}

export default function ImportVideoDialog({
  datasetId,
  datasetName,
  isSubmitting,
  onCancel,
  onSubmit,
}: ImportVideoDialogProps) {
  const [videoName, setVideoName] = useState('')
  const [videoFilepath, setVideoFilepath] = useState('')
  const [videoDescription, setVideoDescription] = useState('')

  const isSubmitDisabled =
    isSubmitting ||
    !videoName.trim() ||
    !videoFilepath.trim() ||
    !videoDescription.trim()

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (isSubmitDisabled) {
      return
    }

    await onSubmit({
      video_name: videoName.trim(),
      video_filepath: videoFilepath.trim(),
      video_description: videoDescription.trim(),
      dataset_id: datasetId,
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
        aria-labelledby="import-video-dialog-title"
      >
        <header className="border-b border-slate-400/10 px-[22px] py-5">
          <p className={panelLabelClass}>Video import</p>
          <h2
            className="mt-2 mb-0 text-[1.35rem] font-semibold tracking-normal text-[#f5f7fb]"
            id="import-video-dialog-title"
          >
            Import Video
          </h2>
          <p className="mt-2 mb-0 text-sm text-[#738099]">
            Dataset: {datasetName}
          </p>
        </header>

        <form className="grid gap-[18px] p-[22px]" onSubmit={handleSubmit}>
          <div className="grid gap-2">
            <label className={fieldLabelClass} htmlFor="import-video-name">
              Video name
            </label>
            <input
              id="import-video-name"
              className={fieldControlClass}
              type="text"
              value={videoName}
              onChange={(event) => setVideoName(event.target.value)}
              disabled={isSubmitting}
              autoFocus
            />
          </div>

          <div className="grid gap-2">
            <label className={fieldLabelClass} htmlFor="import-video-filepath">
              File path
            </label>
            <input
              id="import-video-filepath"
              className={fieldControlClass}
              type="text"
              value={videoFilepath}
              onChange={(event) => setVideoFilepath(event.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="grid gap-2">
            <label
              className={fieldLabelClass}
              htmlFor="import-video-description"
            >
              Description
            </label>
            <textarea
              id="import-video-description"
              className={`${fieldControlClass} min-h-[118px] resize-y`}
              value={videoDescription}
              onChange={(event) => setVideoDescription(event.target.value)}
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
              {isSubmitting ? 'Submitting' : 'Start Import'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

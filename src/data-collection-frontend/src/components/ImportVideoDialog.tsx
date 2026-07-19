import { useId, useState } from 'react'
import type { ChangeEvent, DragEvent, FormEvent } from 'react'
import { toast } from 'sonner'
import type { ImportVideoUploadPayload } from '../actions'
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
  onSubmit: (payload: ImportVideoUploadPayload) => Promise<void>
}

export default function ImportVideoDialog({
  datasetId,
  datasetName,
  isSubmitting,
  onCancel,
  onSubmit,
}: ImportVideoDialogProps) {
  const inputId = useId()
  const [isDragging, setIsDragging] = useState(false)
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [videoTitle, setVideoTitle] = useState('')
  const [videoDescription, setVideoDescription] = useState('')

  const isSubmitDisabled =
    isSubmitting || !videoFile || !videoTitle.trim() || !videoDescription.trim()

  const assignVideoFile = (file: File | null) => {
    if (!file) {
      setVideoFile(null)
      return
    }

    const normalizedName = file.name.toLowerCase()
    const isMp4File = file.type === 'video/mp4' || normalizedName.endsWith('.mp4')

    if (!isMp4File) {
      setVideoFile(null)
      toast.error('Only MP4 videos can be imported')
      return
    }

    setVideoFile(file)

    const defaultValue = file.name.replace(/\.mp4$/i, '')
    setVideoTitle(defaultValue)
    setVideoDescription(defaultValue)
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!videoFile || isSubmitDisabled) {
      return
    }

    await onSubmit({
      video_name: videoTitle.trim(),
      video_file: videoFile,
      video_description: videoDescription.trim(),
      dataset_id: datasetId,
    })
  }

  const handleVideoFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    assignVideoFile(event.target.files?.[0] ?? null)
    event.target.value = ''
  }

  const handleDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault()
    setIsDragging(false)
    assignVideoFile(event.dataTransfer.files?.[0] ?? null)
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
            <label className={fieldLabelClass} htmlFor={inputId}>
              Video file
            </label>
            <label
              className={[
                'grid min-h-44 cursor-pointer place-items-center rounded-[18px] border border-dashed p-6 text-center transition duration-150',
                'bg-[linear-gradient(135deg,rgba(61,217,179,0.08),transparent_36%),linear-gradient(225deg,rgba(75,123,255,0.1),transparent_30%),rgba(7,11,18,0.86)]',
                isDragging
                  ? '-translate-y-px border-emerald-300/45 bg-[#0a1018]/95'
                  : 'border-slate-400/20 hover:-translate-y-px hover:border-emerald-300/45 hover:bg-[#0a1018]/95',
              ].join(' ')}
              htmlFor={inputId}
              onDragEnter={(event) => {
                event.preventDefault()
                setIsDragging(true)
              }}
              onDragOver={(event) => {
                event.preventDefault()
                setIsDragging(true)
              }}
              onDragLeave={(event) => {
                event.preventDefault()
                if (event.currentTarget === event.target) {
                  setIsDragging(false)
                }
              }}
              onDrop={handleDrop}
            >
              <input
                id={inputId}
                className="sr-only"
                type="file"
                accept=".mp4,video/mp4"
                onChange={handleVideoFileChange}
                disabled={isSubmitting}
              />
              <div className="grid gap-2">
                <p className={panelLabelClass}>Import mp4</p>
                <h3 className="m-0 text-[1.2rem] font-semibold tracking-normal text-[#f5f7fb]">
                  {videoFile ? videoFile.name : 'Drop video here'}
                </h3>
                <p className="m-0 text-sm text-[#a8b0c3]">
                  {videoFile
                    ? 'Click to replace the file before starting the import.'
                    : 'Drag and drop an MP4 file here, or click to browse.'}
                </p>
              </div>
            </label>
          </div>

          {videoFile ? (
            <>
              <div className="grid gap-2">
                <label
                  className={fieldLabelClass}
                  htmlFor="import-video-title"
                >
                  Title
                </label>
                <input
                  id="import-video-title"
                  className={fieldControlClass}
                  type="text"
                  value={videoTitle}
                  onChange={(event) => setVideoTitle(event.target.value)}
                  disabled={isSubmitting}
                  autoFocus
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
            </>
          ) : null}

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

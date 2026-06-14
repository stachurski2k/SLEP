import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { toast } from 'sonner'
import {
  deleteVideoClip,
  updateVideoClip,
  type GestureClass,
  type GestureType,
  type VideoClip,
  type VideoClipPayload,
} from '../actions'
import {
  fieldControlClass,
  fieldLabelClass,
  panelClass,
  panelLabelClass,
  primaryButtonClass,
  secondaryButtonClass,
} from '../ui/classes'
import ConfirmDeleteDialog from './ConfirmDeleteDialog'
import CustomTable from './CustomTable'
import type { CustomTableAction, CustomTableColumn } from './CustomTable'
import EditIcon from './icons/EditIcon'
import TrashIcon from './icons/TrashIcon'

type VideoClipsTableProps = {
  videoId: number
  gestureClasses: GestureClass[]
  gestureTypes: GestureType[]
  selectedClipIds: number[]
  refreshKey: number
  onClipChanged: () => void
  onRowsChange: (clips: VideoClip[]) => void
  onToggleClip: (clip: VideoClip) => void
}

export default function VideoClipsTable({
  videoId,
  gestureClasses,
  gestureTypes,
  selectedClipIds,
  refreshKey,
  onClipChanged,
  onRowsChange,
  onToggleClip,
}: VideoClipsTableProps) {
  const [clipPendingEdit, setClipPendingEdit] = useState<VideoClip | null>(null)
  const [clipPendingDelete, setClipPendingDelete] = useState<VideoClip | null>(
    null,
  )
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const columns = useMemo<CustomTableColumn<VideoClip>[]>(
    () => [
      {
        id: 'start',
        header: 'start',
        className: 'w-16 text-[#a8b0c3] [font-variant-numeric:tabular-nums]',
        render: (clip) => clip.start_frame_index,
      },
      {
        id: 'end',
        header: 'end',
        className: 'w-16 text-[#a8b0c3] [font-variant-numeric:tabular-nums]',
        render: (clip) => clip.end_frame_index,
      },
      {
        id: 'class',
        header: 'class',
        className: 'max-w-28 truncate font-semibold text-[#f5f7fb]',
        render: (clip) => clip.gesture_class.name,
      },
      {
        id: 'type',
        header: 'type',
        className: 'max-w-24 truncate text-[#a8b0c3]',
        render: (clip) => clip.gesture_type.name,
      },
    ],
    [],
  )

  const actions = useMemo<CustomTableAction<VideoClip>[]>(
    () => [
      {
        id: 'edit',
        label: 'Edit clip',
        ariaLabel: (clip) => `Edit clip ${clip.id}`,
        onClick: (clip) => setClipPendingEdit(clip),
        icon: <EditIcon />,
      },
      {
        id: 'delete',
        label: 'Delete clip',
        ariaLabel: (clip) => `Delete clip ${clip.id}`,
        onClick: (clip) => setClipPendingDelete(clip),
        icon: <TrashIcon />,
        className:
          'hover:border-rose-400/40 hover:bg-rose-400/10 hover:text-rose-200 focus-visible:outline-rose-300',
      },
    ],
    [],
  )

  const handleSubmitClip = async (payload: VideoClipPayload, clipId: number) => {
    setIsSubmitting(true)

    try {
      await updateVideoClip(clipId, payload)
      setClipPendingEdit(null)
      onClipChanged()
    } catch {
      toast.error('Unable to update clip')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteClip = async () => {
    if (!clipPendingDelete) {
      return
    }

    setIsDeleting(true)

    try {
      await deleteVideoClip(clipPendingDelete.id)
      setClipPendingDelete(null)
      onClipChanged()
    } catch {
      toast.error('Unable to delete clip')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <aside className="min-w-0 overflow-hidden rounded-[18px] border border-slate-400/10 bg-[#070b12]/80">
      <CustomTable<VideoClip>
        label="clips"
        heading="Clips"
        columns={columns}
        actions={actions}
        url={`/api/v1/videos/${videoId}/clips`}
        getRowKey={(clip) => clip.id}
        onRowClick={onToggleClip}
        onRowsChange={onRowsChange}
        rowAriaLabel={(clip) => `Toggle clip ${clip.id}`}
        selectedRowKeys={selectedClipIds}
        refreshKey={refreshKey}
        tableClassName="min-w-[350px] text-sm"
        emptyDescription="Create clips on the timeline to see them here."
      />

      {clipPendingEdit ? (
        <VideoClipEditorDialog
          key={clipPendingEdit.id}
          clip={clipPendingEdit}
          gestureClasses={gestureClasses}
          gestureTypes={gestureTypes}
          isSubmitting={isSubmitting}
          onCancel={() => {
            if (!isSubmitting) {
              setClipPendingEdit(null)
            }
          }}
          onSubmit={handleSubmitClip}
        />
      ) : null}

      {clipPendingDelete ? (
        <ConfirmDeleteDialog
          sectionLabel="Deleting Clip"
          description={
            <p className="m-0">
              Delete clip{' '}
              <span className="font-semibold text-[#f5f7fb]">
                {clipPendingDelete.id} {clipPendingDelete.gesture_class.name}
              </span>
              ?
            </p>
          }
          isDeleting={isDeleting}
          onCancel={() => {
            if (!isDeleting) {
              setClipPendingDelete(null)
            }
          }}
          onDelete={handleDeleteClip}
        />
      ) : null}
    </aside>
  )
}

type VideoClipEditorDialogProps = {
  clip: VideoClip
  gestureClasses: GestureClass[]
  gestureTypes: GestureType[]
  isSubmitting: boolean
  onCancel: () => void
  onSubmit: (payload: VideoClipPayload, clipId: number) => Promise<void>
}

function VideoClipEditorDialog({
  clip,
  gestureClasses,
  gestureTypes,
  isSubmitting,
  onCancel,
  onSubmit,
}: VideoClipEditorDialogProps) {
  const [startFrameIndex, setStartFrameIndex] = useState(
    String(clip.start_frame_index),
  )
  const [endFrameIndex, setEndFrameIndex] = useState(
    String(clip.end_frame_index),
  )
  const [gestureClassId, setGestureClassId] = useState(
    String(clip.gesture_class.id),
  )
  const [gestureTypeId, setGestureTypeId] = useState(
    String(clip.gesture_type.id),
  )

  const startFrameNumber = Number(startFrameIndex)
  const endFrameNumber = Number(endFrameIndex)
  const isSubmitDisabled =
    isSubmitting ||
    !startFrameIndex ||
    !endFrameIndex ||
    !Number.isInteger(startFrameNumber) ||
    !Number.isInteger(endFrameNumber) ||
    startFrameNumber < 0 ||
    endFrameNumber < startFrameNumber ||
    !gestureClassId ||
    !gestureTypeId

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (isSubmitDisabled) {
      return
    }

    await onSubmit(
      {
        start_frame_index: startFrameNumber,
        end_frame_index: endFrameNumber,
        gesture_class_id: Number(gestureClassId),
        gesture_type_id: Number(gestureTypeId),
      },
      clip.id,
    )
  }

  return (
    <div
      className="fixed inset-0 z-20 grid place-items-center bg-[#03060c]/70 p-6 backdrop-blur-xl max-[560px]:items-end max-[560px]:p-3.5"
      role="presentation"
    >
      <section
        className={`${panelClass} w-full max-w-[560px]`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="video-clip-dialog-title"
      >
        <header className="border-b border-slate-400/10 px-[22px] py-5">
          <p className={panelLabelClass}>Clip editor</p>
          <h2
            className="mt-2 mb-0 text-[1.35rem] font-semibold tracking-normal text-[#f5f7fb]"
            id="video-clip-dialog-title"
          >
            Edit Clip
          </h2>
        </header>

        <form className="grid gap-[18px] p-[22px]" onSubmit={handleSubmit}>
          <div className="grid grid-cols-2 gap-3.5">
            <label className="grid gap-2">
              <span className={fieldLabelClass}>Start</span>
              <input
                className={fieldControlClass}
                type="number"
                min={0}
                step={1}
                value={startFrameIndex}
                onChange={(event) => setStartFrameIndex(event.target.value)}
                disabled={isSubmitting}
                autoFocus
              />
            </label>

            <label className="grid gap-2">
              <span className={fieldLabelClass}>End</span>
              <input
                className={fieldControlClass}
                type="number"
                min={0}
                step={1}
                value={endFrameIndex}
                onChange={(event) => setEndFrameIndex(event.target.value)}
                disabled={isSubmitting}
              />
            </label>
          </div>

          <div className="grid grid-cols-2 gap-3.5 max-[560px]:grid-cols-1">
            <label className="grid gap-2">
              <span className={fieldLabelClass}>Gesture Class</span>
              <select
                className={fieldControlClass}
                value={gestureClassId}
                onChange={(event) => setGestureClassId(event.target.value)}
                disabled={isSubmitting || gestureClasses.length === 0}
              >
                <option value="">Select gesture class</option>
                {gestureClasses.map((gestureClass) => (
                  <option key={gestureClass.id} value={gestureClass.id}>
                    {gestureClass.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2">
              <span className={fieldLabelClass}>Gesture Type</span>
              <select
                className={fieldControlClass}
                value={gestureTypeId}
                onChange={(event) => setGestureTypeId(event.target.value)}
                disabled={isSubmitting || gestureTypes.length === 0}
              >
                <option value="">Select gesture type</option>
                {gestureTypes.map((gestureType) => (
                  <option key={gestureType.id} value={gestureType.id}>
                    {gestureType.name}
                  </option>
                ))}
              </select>
            </label>
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
              {isSubmitting ? 'Submitting' : 'Save Changes'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

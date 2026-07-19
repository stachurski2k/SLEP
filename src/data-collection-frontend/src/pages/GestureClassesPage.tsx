import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import {
  createGestureClass,
  deleteGestureClass,
  updateGestureClass,
} from '../actions'
import type { GestureClass, GestureClassPayload } from '../actions'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog'
import CustomTable from '../components/CustomTable'
import type {
  CustomTableAction,
  CustomTableColumn,
} from '../components/CustomTable'
import GestureClassEditorDialog from '../components/GestureClassEditorDialog'
import EditIcon from '../components/icons/EditIcon'
import TrashIcon from '../components/icons/TrashIcon'
import { panelClass, primaryButtonClass } from '../ui/classes'

export default function GestureClassesPage() {
  const [tableRefreshKey, setTableRefreshKey] = useState(0)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [gestureClassPendingEdit, setGestureClassPendingEdit] =
    useState<GestureClass | null>(null)
  const [gestureClassPendingDelete, setGestureClassPendingDelete] =
    useState<GestureClass | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const columns = useMemo<CustomTableColumn<GestureClass>[]>(
    () => [
      {
        id: 'id',
        header: 'ID',
        className:
          'w-24 text-[#738099] [font-variant-numeric:tabular-nums]',
        render: (gestureClass) => gestureClass.id,
      },
      {
        id: 'name',
        header: 'Name',
        className: 'font-semibold text-[#f5f7fb]',
        render: (gestureClass) => gestureClass.name,
      },
    ],
    [],
  )

  const actions = useMemo<CustomTableAction<GestureClass>[]>(
    () => [
      {
        id: 'edit',
        label: 'Edit gesture class',
        ariaLabel: (gestureClass) => `Edit gesture class ${gestureClass.name}`,
        onClick: (gestureClass) => {
          setGestureClassPendingEdit(gestureClass)
          setIsDialogOpen(true)
        },
        icon: <EditIcon />,
      },
      {
        id: 'delete',
        label: 'Delete gesture class',
        ariaLabel: (gestureClass) => `Delete gesture class ${gestureClass.name}`,
        onClick: (gestureClass) => setGestureClassPendingDelete(gestureClass),
        icon: <TrashIcon />,
        className:
          'hover:border-rose-400/40 hover:bg-rose-400/10 hover:text-rose-200 focus-visible:outline-rose-300',
      },
    ],
    [],
  )

  const handleDeleteGestureClass = async () => {
    if (!gestureClassPendingDelete) {
      return
    }

    setIsDeleting(true)

    try {
      await deleteGestureClass(gestureClassPendingDelete.id)
      setGestureClassPendingDelete(null)
      setTableRefreshKey((currentKey) => currentKey + 1)
    } catch {
      toast.error('Unable to delete gesture class')
    } finally {
      setIsDeleting(false)
    }
  }

  const handleSubmitGestureClass = async (
    payload: GestureClassPayload,
    gestureClassId?: number,
  ) => {
    setIsSubmitting(true)

    try {
      if (gestureClassPendingEdit && gestureClassId !== undefined) {
        await updateGestureClass(gestureClassId, payload)
      } else {
        await createGestureClass(payload)
      }

      setIsDialogOpen(false)
      setGestureClassPendingEdit(null)
      setTableRefreshKey((currentKey) => currentKey + 1)
    } catch {
      toast.error(
        gestureClassPendingEdit
          ? 'Unable to update gesture class'
          : 'Unable to create gesture class',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCloseDialog = () => {
    if (isSubmitting) {
      return
    }

    setIsDialogOpen(false)
    setGestureClassPendingEdit(null)
  }

  return (
    <>
      <section className={panelClass}>
        <CustomTable<GestureClass>
          label="gesture classes"
          columns={columns}
          actions={actions}
          url="/api/v1/gesture-classes/"
          getRowKey={(gestureClass) => gestureClass.id}
          refreshKey={tableRefreshKey}
          emptyDescription="Create a gesture class in the backend to see it here."
        />

        <footer className="flex justify-end border-t border-slate-400/10 bg-[#070b12]/35 px-[22px] py-4 max-[720px]:justify-stretch">
          <button
            className={`${primaryButtonClass} max-[720px]:w-full`}
            type="button"
            onClick={() => {
              setGestureClassPendingEdit(null)
              setIsDialogOpen(true)
            }}
          >
            Add Gesture Class
          </button>
        </footer>
      </section>

      {isDialogOpen ? (
        <GestureClassEditorDialog
          key={gestureClassPendingEdit?.id ?? 'create'}
          isEditMode={gestureClassPendingEdit !== null}
          isSubmitting={isSubmitting}
          gestureClassId={gestureClassPendingEdit?.id}
          initialName={gestureClassPendingEdit?.name}
          onCancel={handleCloseDialog}
          onSubmit={handleSubmitGestureClass}
        />
      ) : null}

      {gestureClassPendingDelete ? (
        <ConfirmDeleteDialog
          sectionLabel="Deleting Gesture Class"
          description={
            <p className="m-0">
              Delete{' '}
              <span className="font-semibold text-[#f5f7fb]">
                {gestureClassPendingDelete.name}
              </span>
              ?
            </p>
          }
          isDeleting={isDeleting}
          onCancel={() => {
            if (!isDeleting) {
              setGestureClassPendingDelete(null)
            }
          }}
          onDelete={handleDeleteGestureClass}
        />
      ) : null}
    </>
  )
}

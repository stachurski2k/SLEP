import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import {
  createGestureType,
  deleteGestureType,
  updateGestureType,
} from '../actions'
import type { GestureType, GestureTypePayload } from '../actions'
import ConfirmDeleteDialog from '../components/ConfirmDeleteDialog'
import CustomTable from '../components/CustomTable'
import type {
  CustomTableAction,
  CustomTableColumn,
} from '../components/CustomTable'
import GestureTypesEditorDialog from '../components/GestureTypesEditorDialog'
import EditIcon from '../components/icons/EditIcon'
import TrashIcon from '../components/icons/TrashIcon'
import { panelClass, primaryButtonClass } from '../ui/classes'

export default function GestureTypesPage() {
  const [tableRefreshKey, setTableRefreshKey] = useState(0)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [gestureTypePendingEdit, setGestureTypePendingEdit] =
    useState<GestureType | null>(null)
  const [gestureTypePendingDelete, setGestureTypePendingDelete] =
    useState<GestureType | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const columns = useMemo<CustomTableColumn<GestureType>[]>(
    () => [
      {
        id: 'id',
        header: 'ID',
        className:
          'w-24 text-[#738099] [font-variant-numeric:tabular-nums]',
        render: (gestureType) => gestureType.id,
      },
      {
        id: 'name',
        header: 'Name',
        className: 'font-semibold text-[#f5f7fb]',
        render: (gestureType) => gestureType.name,
      },
    ],
    [],
  )

  const actions = useMemo<CustomTableAction<GestureType>[]>(
    () => [
      {
        id: 'edit',
        label: 'Edit gesture type',
        ariaLabel: (gestureType) => `Edit gesture type ${gestureType.name}`,
        onClick: (gestureType) => {
          setGestureTypePendingEdit(gestureType)
          setIsDialogOpen(true)
        },
        icon: <EditIcon />,
      },
      {
        id: 'delete',
        label: 'Delete gesture type',
        ariaLabel: (gestureType) => `Delete gesture type ${gestureType.name}`,
        onClick: (gestureType) => setGestureTypePendingDelete(gestureType),
        icon: <TrashIcon />,
        className:
          'hover:border-rose-400/40 hover:bg-rose-400/10 hover:text-rose-200 focus-visible:outline-rose-300',
      },
    ],
    [],
  )

  const handleDeleteGestureType = async () => {
    if (!gestureTypePendingDelete) {
      return
    }

    setIsDeleting(true)

    try {
      await deleteGestureType(gestureTypePendingDelete.id)
      setGestureTypePendingDelete(null)
      setTableRefreshKey((currentKey) => currentKey + 1)
    } catch {
      toast.error('Unable to delete gesture type')
    } finally {
      setIsDeleting(false)
    }
  }

  const handleSubmitGestureType = async (
    payload: GestureTypePayload,
    gestureTypeId?: number,
  ) => {
    setIsSubmitting(true)

    try {
      if (gestureTypePendingEdit && gestureTypeId !== undefined) {
        await updateGestureType(gestureTypeId, payload)
      } else {
        await createGestureType(payload)
      }

      setIsDialogOpen(false)
      setGestureTypePendingEdit(null)
      setTableRefreshKey((currentKey) => currentKey + 1)
    } catch {
      toast.error(
        gestureTypePendingEdit
          ? 'Unable to update gesture type'
          : 'Unable to create gesture type',
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
    setGestureTypePendingEdit(null)
  }

  return (
    <>
      <section className={panelClass}>
        <CustomTable<GestureType>
          label="gesture types"
          columns={columns}
          actions={actions}
          url="/api/v1/gesture-types/"
          getRowKey={(gestureType) => gestureType.id}
          refreshKey={tableRefreshKey}
          emptyDescription="Create a gesture type in the backend to see it here."
        />

        <footer className="flex justify-end border-t border-slate-400/10 bg-[#070b12]/35 px-[22px] py-4 max-[720px]:justify-stretch">
          <button
            className={`${primaryButtonClass} max-[720px]:w-full`}
            type="button"
            onClick={() => {
              setGestureTypePendingEdit(null)
              setIsDialogOpen(true)
            }}
          >
            Add Gesture Type
          </button>
        </footer>
      </section>

      {isDialogOpen ? (
        <GestureTypesEditorDialog
          key={gestureTypePendingEdit?.id ?? 'create'}
          isEditMode={gestureTypePendingEdit !== null}
          isSubmitting={isSubmitting}
          gestureTypeId={gestureTypePendingEdit?.id}
          initialName={gestureTypePendingEdit?.name}
          onCancel={handleCloseDialog}
          onSubmit={handleSubmitGestureType}
        />
      ) : null}

      {gestureTypePendingDelete ? (
        <ConfirmDeleteDialog
          sectionLabel="Deleting Gesture Type"
          description={
            <p className="m-0">
              Delete{' '}
              <span className="font-semibold text-[#f5f7fb]">
                {gestureTypePendingDelete.name}
              </span>
              ?
            </p>
          }
          isDeleting={isDeleting}
          onCancel={() => {
            if (!isDeleting) {
              setGestureTypePendingDelete(null)
            }
          }}
          onDelete={handleDeleteGestureType}
        />
      ) : null}
    </>
  )
}

import { useMemo } from 'react'
import type { Key } from 'react'
import type { Dataset } from '../actions'
import CustomTable from './CustomTable'
import type {
  CustomTableAction,
  CustomTableColumn,
} from './CustomTable'

type DatasetTableProps = {
  actions?: CustomTableAction<Dataset>[]
  refreshKey?: number
  selectedDatasetId?: Key | null
  onDatasetClick?: (dataset: Dataset) => void
}

export default function DatasetTable({
  actions,
  refreshKey,
  selectedDatasetId = null,
  onDatasetClick,
}: DatasetTableProps) {
  const columns = useMemo<CustomTableColumn<Dataset>[]>(
    () => [
      {
        id: 'id',
        header: 'ID',
        className:
          'w-24 text-[#738099] [font-variant-numeric:tabular-nums]',
        render: (dataset) => dataset.id,
      },
      {
        id: 'name',
        header: 'Name',
        className: 'w-[260px] font-semibold text-[#f5f7fb]',
        render: (dataset) => dataset.name,
      },
      {
        id: 'description',
        header: 'Description',
        className: 'text-[#a8b0c3]',
        render: (dataset) => dataset.description || 'No description',
      },
    ],
    [],
  )

  return (
    <CustomTable<Dataset>
      label="datasets"
      columns={columns}
      actions={actions}
      url="/api/v1/datasets/"
      getRowKey={(dataset) => dataset.id}
      onRowClick={onDatasetClick}
      rowAriaLabel={(dataset) => `Open dataset ${dataset.name}`}
      selectedRowKey={selectedDatasetId}
      refreshKey={refreshKey}
      emptyDescription="Create a dataset in the backend to see it here."
    />
  )
}

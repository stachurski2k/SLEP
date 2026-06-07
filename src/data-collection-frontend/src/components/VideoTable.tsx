import { useMemo } from 'react'
import type { Key } from 'react'
import type { Video } from '../actions'
import CustomTable from './CustomTable'
import type { CustomTableColumn } from './CustomTable'

const VIDEO_TABLE_PAGE = 0
const VIDEO_TABLE_LIMIT = 50

const truncatedTextClass = 'overflow-hidden text-ellipsis whitespace-nowrap'

type VideoTableProps = {
  datasetId: number
  heading: string
  refreshKey?: number
  selectedVideoId?: Key | null
  onVideoClick?: (video: Video) => void
  onRowsChange?: (videos: Video[]) => void
  emptyDescription?: string
}

function getDatasetVideosUrl(datasetId: number) {
  return `/api/v1/videos/?page=${VIDEO_TABLE_PAGE}&limit=${VIDEO_TABLE_LIMIT}&dataset_id=${datasetId}`
}

export default function VideoTable({
  datasetId,
  heading,
  refreshKey,
  selectedVideoId = null,
  onVideoClick,
  onRowsChange,
  emptyDescription = 'This dataset does not contain videos on page 0.',
}: VideoTableProps) {
  const columns = useMemo<CustomTableColumn<Video>[]>(
    () => [
      {
        id: 'id',
        header: 'ID',
        className:
          'w-24 text-[#738099] [font-variant-numeric:tabular-nums]',
        render: (video) => video.id,
      },
      {
        id: 'name',
        header: 'Name',
        className: 'w-[260px] font-semibold text-[#f5f7fb]',
        render: (video) => <span className={truncatedTextClass}>{video.name}</span>,
      },
      {
        id: 'filepath',
        header: 'Path',
        className: 'text-[#738099]',
        render: (video) => video.filepath,
      },
    ],
    [],
  )

  return (
    <CustomTable<Video>
      label="videos"
      heading={heading}
      columns={columns}
      url={getDatasetVideosUrl(datasetId)}
      getRowKey={(video) => video.id}
      refreshKey={refreshKey}
      onRowClick={onVideoClick}
      rowAriaLabel={(video) => `Select video ${video.name}`}
      selectedRowKey={selectedVideoId}
      onRowsChange={onRowsChange}
      emptyDescription={emptyDescription}
    />
  )
}

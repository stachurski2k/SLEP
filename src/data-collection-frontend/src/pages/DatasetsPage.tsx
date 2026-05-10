import { useNavigate } from 'react-router'
import type { Dataset } from '../actions'
import DatasetManager from '../components/DatasetManager'
import { getDatasetVideosPath } from '../routes'
import type { DatasetRouteState } from '../routes'

export default function DatasetsPage() {
  const navigate = useNavigate()

  const handleOpenDataset = (dataset: Dataset) => {
    navigate(getDatasetVideosPath(dataset.id), {
      state: { dataset } satisfies DatasetRouteState,
    })
  }

  return <DatasetManager onOpenDataset={handleOpenDataset} />
}

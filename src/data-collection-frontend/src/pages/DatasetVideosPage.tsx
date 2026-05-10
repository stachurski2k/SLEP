import { useEffect, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router'
import type { Dataset } from '../actions'
import { getDataset } from '../actions'
import VideoExplorer from '../components/VideoExplorer'
import { routes } from '../routes'
import type { DatasetRouteState } from '../routes'
import RouteState from '../ui/RouteState'

export default function DatasetVideosPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { datasetId } = useParams()
  const routeState = location.state as DatasetRouteState | null
  const stateDataset = routeState?.dataset
  const parsedDatasetId = Number(datasetId)
  const [dataset, setDataset] = useState<Dataset | null>(
    stateDataset?.id === parsedDatasetId ? stateDataset : null,
  )
  const [isLoading, setIsLoading] = useState(!dataset)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!Number.isInteger(parsedDatasetId)) {
      setDataset(null)
      setIsLoading(false)
      setError('Invalid dataset ID')
      return
    }

    if (stateDataset?.id === parsedDatasetId) {
      setDataset(stateDataset)
      setIsLoading(false)
      setError(null)
      return
    }

    if (dataset?.id === parsedDatasetId) {
      return
    }

    let isMounted = true

    async function loadDataset() {
      setIsLoading(true)
      setError(null)

      try {
        const nextDataset = await getDataset(parsedDatasetId)

        if (isMounted) {
          setDataset(nextDataset)
        }
      } catch (requestError) {
        if (isMounted) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'Unable to load dataset',
          )
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadDataset()

    return () => {
      isMounted = false
    }
  }, [dataset?.id, parsedDatasetId, stateDataset])

  if (isLoading) {
    return <RouteState title="Loading dataset" />
  }

  if (error || !dataset) {
    return (
      <RouteState
        title="Dataset unavailable"
        description={error ?? 'Dataset could not be found.'}
        variant="error"
      />
    )
  }

  return (
    <VideoExplorer
      dataset={dataset}
      onBack={() => navigate(routes.datasets)}
    />
  )
}

import type { Dataset } from './actions'

export type Page = 'editor' | 'dataset-manager' | 'video-explorer'

export type DatasetRouteState = {
  dataset?: Dataset
}

export const routes = {
  editor: '/',
  datasets: '/datasets',
  datasetVideos: '/datasets/:datasetId/videos',
} as const

export const navRoutes: Array<{
  page: Exclude<Page, 'video-explorer'>
  label: string
  path: string
  end?: boolean
}> = [
  { page: 'editor', label: 'Video editor', path: routes.editor, end: true },
  { page: 'dataset-manager', label: 'Dataset Manager', path: routes.datasets },
]

export function getDatasetVideosPath(datasetId: number) {
  return `/datasets/${datasetId}/videos`
}

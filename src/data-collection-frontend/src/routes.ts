import type { Dataset, Video } from './actions'

export type Page =
  | 'editor'
  | 'dataset-manager'
  | 'gesture-class'
  | 'gesture-type'
  | 'video-explorer'

export type DatasetRouteState = {
  dataset?: Dataset
}

export type EditorRouteState = {
  dataset?: Dataset
  video?: Video
}

export const routes = {
  editor: '/',
  datasets: '/datasets',
  gestureClasses: '/gesture-classes',
  gestureTypes: '/gesture-types',
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
  { page: 'gesture-class', label: 'Gesture Class', path: routes.gestureClasses },
  { page: 'gesture-type', label: 'Gesture Types', path: routes.gestureTypes },
]

export function getDatasetVideosPath(datasetId: number) {
  return `/datasets/${datasetId}/videos`
}

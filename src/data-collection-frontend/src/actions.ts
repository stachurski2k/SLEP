const API_BASE_URL = `http://${window.location.hostname}:5000`

export type Dataset = {
  id: number
  name: string
  description: string
}

export type DatasetPayload = {
  name: string
  description: string
}

export type Video = {
  id: number
  name: string
  filepath: string
}

export type ImportVideoJobPayload = {
  video_name: string
  video_filepath: string
  video_description: string
  dataset_id: number
}

export type ImportVideoUploadPayload = {
  video_name: string
  video_file: File
  video_description: string
  dataset_id: number
}

export type UploadUrlPayload = {
  s3_key: string
  content_type: string
  expires_in?: number
}

export type UploadUrlResponse = {
  url: string
  key: string
  expires_in: number
}

export type DownloadUrlPayload = {
  s3_key: string
  expires_in?: number
}

export type DownloadUrlResponse = {
  url: string
}

export type GestureClass = {
  id: number
  name: string
}

export type GestureClassPayload = {
  name: string
}

export type GestureType = {
  id: number
  name: string
}

export type GestureTypePayload = {
  name: string
}

export type VideoClip = {
  id: number
  start_frame_index: number
  end_frame_index: number
  gesture_class: GestureClass
  gesture_type: GestureType
}

export type VideoClipPayload = {
  start_frame_index: number
  end_frame_index: number
  gesture_class_id: number
  gesture_type_id: number
}

export async function requestJson<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options)

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }

  return response.json() as Promise<T>
}

async function request(
  path: string,
  options?: RequestInit,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, options)

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }
}

export function getDatasets() {
  return requestJson<Dataset[]>('/api/v1/datasets/')
}

export function getDataset(datasetId: number) {
  return requestJson<Dataset>(`/api/v1/datasets/${datasetId}`)
}

export function getVideos({
  page,
  limit,
  datasetId,
}: {
  page: number
  limit: number
  datasetId: number | null
}) {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(limit),
  })

  if (datasetId !== null) {
    params.set('dataset_id', String(datasetId))
  }

  return requestJson<Video[]>(`/api/v1/videos/?${params.toString()}`)
}

export function createImportVideoJob(payload: ImportVideoJobPayload) {
  return requestJson<unknown>('/api/v1/import-video-jobs/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export async function getUploadUrl(payload: UploadUrlPayload) {
  return requestJson<UploadUrlResponse>('/api/v1/s3/upload-url', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export async function getDownloadUrl(payload: DownloadUrlPayload) {
  return requestJson<DownloadUrlResponse>('/api/v1/s3/download-url', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export async function uploadFileToSignedUrl(
  url: string,
  file: File,
  contentType: string,
) {
  const response = await fetch(url, {
    method: 'PUT',
    headers: {
      'Content-Type': contentType,
    },
    body: file,
  })

  if (!response.ok) {
    throw new Error(`Upload failed with status ${response.status}`)
  }
}

export function createDataset(payload: DatasetPayload) {
  return requestJson<Dataset>('/api/v1/datasets/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export function deleteDataset(datasetId: number) {
  return request(`/api/v1/datasets/${datasetId}`, {
    method: 'DELETE',
    headers: {
      Accept: '*/*',
    },
  })
}

export function getGestureClasses() {
  return requestJson<GestureClass[]>('/api/v1/gesture-classes/')
}

export function deleteGestureClass(gestureClassId: number) {
  return request(`/api/v1/gesture-classes/${gestureClassId}`, {
    method: 'DELETE',
    headers: {
      Accept: '*/*',
    },
  })
}

export function createGestureClass(payload: GestureClassPayload) {
  return requestJson<GestureClass>('/api/v1/gesture-classes/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export function updateGestureClass(
  gestureClassId: number,
  payload: GestureClassPayload,
) {
  return requestJson<GestureClass>(`/api/v1/gesture-classes/${gestureClassId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export function getGestureTypes() {
  return requestJson<GestureType[]>('/api/v1/gesture-types/')
}

export function deleteGestureType(gestureTypeId: number) {
  return request(`/api/v1/gesture-types/${gestureTypeId}`, {
    method: 'DELETE',
    headers: {
      Accept: '*/*',
    },
  })
}

export function createGestureType(payload: GestureTypePayload) {
  return requestJson<GestureType>('/api/v1/gesture-types/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export function createVideoClip(videoId: number, payload: VideoClipPayload) {
  return requestJson<VideoClip>(`/api/v1/videos/${videoId}/clips`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

export function updateGestureType(
  gestureTypeId: number,
  payload: GestureTypePayload,
) {
  return requestJson<GestureType>(`/api/v1/gesture-types/${gestureTypeId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}

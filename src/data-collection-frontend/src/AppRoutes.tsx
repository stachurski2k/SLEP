import { Navigate, Route, Routes } from 'react-router'
import Editor from './components/Editor'
import DatasetVideosPage from './pages/DatasetVideosPage'
import DatasetsPage from './pages/DatasetsPage'
import { routes } from './routes'

export default function AppRoutes() {
  return (
    <Routes>
      <Route index element={<Editor />} />
      <Route path={routes.datasets.slice(1)} element={<DatasetsPage />} />
      <Route
        path={routes.datasetVideos.slice(1)}
        element={<DatasetVideosPage />}
      />
      <Route path="*" element={<Navigate replace to={routes.editor} />} />
    </Routes>
  )
}

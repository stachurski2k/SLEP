import { Navigate, Route, Routes } from 'react-router'
import DatasetVideosPage from './pages/DatasetVideosPage'
import DatasetsPage from './pages/DatasetsPage'
import GestureClassesPage from './pages/GestureClassesPage'
import GestureTypesPage from './pages/GestureTypesPage'
import { routes } from './routes'
import EditorPage from './pages/EditorPage'

export default function AppRoutes() {
  return (
    <Routes>
      <Route index element={<EditorPage />} />
      <Route path={routes.datasets.slice(1)} element={<DatasetsPage />} />
      <Route
        path={routes.gestureClasses.slice(1)}
        element={<GestureClassesPage />}
      />
      <Route
        path={routes.gestureTypes.slice(1)}
        element={<GestureTypesPage />}
      />
      <Route
        path={routes.datasetVideos.slice(1)}
        element={<DatasetVideosPage />}
      />
      <Route path="*" element={<Navigate replace to={routes.editor} />} />
    </Routes>
  )
}

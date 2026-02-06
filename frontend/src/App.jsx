import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import QuestionnaireList from './pages/QuestionnaireList'
import QuestionnaireBuilder from './pages/QuestionnaireBuilder'
import QuestionnaireView from './pages/QuestionnaireView'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/questionnaires" replace />} />
        <Route path="/questionnaires" element={<QuestionnaireList />} />
        <Route path="/questionnaires/new" element={<QuestionnaireBuilder />} />
        <Route path="/questionnaires/:id/edit" element={<QuestionnaireBuilder />} />
        <Route path="/questionnaires/:id" element={<QuestionnaireView />} />
      </Routes>
    </Layout>
  )
}

export default App

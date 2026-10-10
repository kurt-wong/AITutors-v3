/** App router：Phase I Review Console 路由。 */

import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AdminLayout } from "./components/layout/AdminLayout";
import { AdminWorkspace } from "./pages/AdminWorkspace";
import { CandidateReview } from "./pages/CandidateReview";
import { DocumentList } from "./pages/DocumentList";
import { DocumentReview } from "./pages/DocumentReview";
import DocumentUpload from "./pages/DocumentUpload";
import { QuestionDetailPage } from "./pages/QuestionDetail";
import { QuestionList } from "./pages/QuestionList";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<AdminWorkspace />} />
          <Route path="documents" element={<DocumentList />} />
          <Route path="documents/upload" element={<DocumentUpload />} />
          <Route path="documents/:id" element={<DocumentReview />} />
          <Route path="candidates/:id" element={<CandidateReview />} />
          <Route path="questions" element={<QuestionList />} />
          <Route path="questions/:id" element={<QuestionDetailPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

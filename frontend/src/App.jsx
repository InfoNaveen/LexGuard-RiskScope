import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import UploadPage from "./pages/UploadPage.jsx";
import AnalyzePage from "./pages/AnalyzePage.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/analyze/:job_id" element={<AnalyzePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

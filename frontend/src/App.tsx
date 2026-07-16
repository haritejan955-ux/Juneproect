import { Link, Route, Routes } from "react-router-dom";

import { HistoryPage } from "./pages/HistoryPage";
import { ProcessingPage } from "./pages/ProcessingPage";
import { ReportPage } from "./pages/ReportPage";
import { SubmitPage } from "./pages/SubmitPage";

export function App() {
  return (
    <div className="min-h-screen bg-white text-gray-900 dark:bg-gray-950 dark:text-gray-100">
      <nav className="border-b border-gray-200 px-6 py-4 dark:border-gray-800">
        <div className="mx-auto flex max-w-3xl items-center gap-6">
          <Link to="/submit" className="font-semibold">
            Medication Safety Checker
          </Link>
          <Link to="/submit" className="text-sm text-gray-500 hover:text-gray-900 dark:hover:text-gray-100">
            New check
          </Link>
          <Link to="/history" className="text-sm text-gray-500 hover:text-gray-900 dark:hover:text-gray-100">
            History
          </Link>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<SubmitPage />} />
        <Route path="/submit" element={<SubmitPage />} />
        <Route path="/processing/:reportId" element={<ProcessingPage />} />
        <Route path="/report/:reportId" element={<ReportPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Routes>
    </div>
  );
}

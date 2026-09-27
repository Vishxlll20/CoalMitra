import { Routes, Route, Navigate } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { Landing } from "./pages/Landing";
import { Dashboard } from "./pages/app/Dashboard";
import { Documents } from "./pages/app/Documents";
import { DocumentDetail } from "./pages/app/DocumentDetail";
import { Reports } from "./pages/app/Reports";
import { ReportDetail } from "./pages/app/ReportDetail";
import { Insights } from "./pages/app/Insights";
import { Anomalies } from "./pages/app/Anomalies";
import { Query } from "./pages/app/Query";
import { Metrics } from "./pages/app/Metrics";

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Landing />} />

      {/* App frame */}
      <Route element={<AppShell />}>
        <Route path="/app" element={<Dashboard />} />
        <Route path="/app/documents" element={<Documents />} />
        <Route path="/app/documents/:id" element={<DocumentDetail />} />
        <Route path="/app/reports" element={<Reports />} />
        <Route path="/app/reports/:id" element={<ReportDetail />} />
        <Route path="/app/insights" element={<Insights />} />
        <Route path="/app/anomalies" element={<Anomalies />} />
        <Route path="/app/query" element={<Query />} />
        <Route path="/app/metrics" element={<Metrics />} />
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
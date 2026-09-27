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
import { AuthPage } from "./pages/AuthPage";
import { RequireAuth, RequireRole } from "./components/auth/RouteGuards";

const ALL_ROLES = ["GEOLOGIST", "MINISTRY_OFFICIAL", "AUDITOR"] as const;
const GEOLOGIST_AUDITOR = ["GEOLOGIST", "AUDITOR"] as const;
const GEOLOGIST_MINISTRY = ["GEOLOGIST", "MINISTRY_OFFICIAL"] as const;

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/register" element={<AuthPage mode="register" />} />

      {/* App frame */}
      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route path="/app" element={<RequireRole allowed={[...ALL_ROLES]}><Dashboard /></RequireRole>} />
          <Route path="/app/documents" element={<RequireRole allowed={[...GEOLOGIST_AUDITOR]}><Documents /></RequireRole>} />
          <Route path="/app/documents/:id" element={<RequireRole allowed={[...GEOLOGIST_AUDITOR]}><DocumentDetail /></RequireRole>} />
          <Route path="/app/reports" element={<RequireRole allowed={[...ALL_ROLES]}><Reports /></RequireRole>} />
          <Route path="/app/reports/:id" element={<RequireRole allowed={[...ALL_ROLES]}><ReportDetail /></RequireRole>} />
          <Route path="/app/insights" element={<RequireRole allowed={[...ALL_ROLES]}><Insights /></RequireRole>} />
          <Route path="/app/anomalies" element={<RequireRole allowed={[...GEOLOGIST_AUDITOR]}><Anomalies /></RequireRole>} />
          <Route path="/app/query" element={<RequireRole allowed={[...GEOLOGIST_MINISTRY]}><Query /></RequireRole>} />
          <Route path="/app/metrics" element={<RequireRole allowed={[...ALL_ROLES]}><Metrics /></RequireRole>} />
        </Route>
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
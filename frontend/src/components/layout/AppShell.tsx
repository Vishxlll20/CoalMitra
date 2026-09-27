import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { SourcePanelHost } from "../traceability/SourcePanelHost";

/**
 * App frame: dark sidebar + sticky topbar + scrollable content.
 * SourcePanelHost lives here so the slide-in trace panel is available
 * on every app route with a shared focus state.
 */
export function AppShell() {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="ml-[232px] flex min-h-screen flex-col">
        <Topbar />
        <main className="mx-auto w-full max-w-[1440px] flex-1 px-6 py-7 pb-16">
          <Outlet />
        </main>
      </div>
      <SourcePanelHost />
    </div>
  );
}
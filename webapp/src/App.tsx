import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { RequireAuth } from "./auth/RequireAuth";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Market = lazy(() => import("./pages/Market"));
const Decisions = lazy(() => import("./pages/Decisions"));
const Positions = lazy(() => import("./pages/Positions"));
const Performance = lazy(() => import("./pages/Performance"));
const Risk = lazy(() => import("./pages/Risk"));
const Lab = lazy(() => import("./pages/Lab"));
const Audit = lazy(() => import("./pages/Audit"));
const Admin = lazy(() => import("./pages/Admin"));
const Settings = lazy(() => import("./pages/Settings"));
const Login = lazy(() => import("./pages/Login"));

function Fallback() {
  return (
    <div className="flex h-full w-full items-center justify-center bg-bg-0">
      <span className="font-mono text-sm text-fg-4">加载中…</span>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<Fallback />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        {/* 登录后可见（RequireAuth 守卫） */}
        <Route element={<RequireAuth />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/market" element={<Market />} />
          <Route path="/decisions" element={<Decisions />} />
          <Route path="/positions" element={<Positions />} />
          <Route path="/performance" element={<Performance />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="/lab" element={<Lab />} />
          <Route path="/audit" element={<Audit />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

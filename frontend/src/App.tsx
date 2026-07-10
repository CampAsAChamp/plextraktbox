import { Center, Loader } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { Navigate, Route, Routes } from "react-router-dom";
import { api } from "./api/client";
import type { SetupStatus, User } from "./api/auth";
import { ApiError } from "./api/client";
import { AppLayout } from "./components/layout/AppLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { SetupWizardPage } from "./pages/SetupWizardPage";

function LoadingScreen() {
  return (
    <Center mih="100vh">
      <Loader />
    </Center>
  );
}

function useSetupStatus() {
  return useQuery({
    queryKey: ["setup", "status"],
    queryFn: () => api.get<SetupStatus>("/setup/status"),
  });
}

function useCurrentUser() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      try {
        return await api.get<User>("/auth/me");
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
    retry: false,
  });
}

function SetupRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/setup" element={<SetupWizardPage />} />
        <Route path="*" element={<Navigate to="/setup" replace />} />
      </Route>
    </Routes>
  );
}

function AppRoutes() {
  const meQuery = useCurrentUser();

  if (meQuery.isLoading) return <LoadingScreen />;
  if (meQuery.isError) {
    return <Center mih="100vh">API unreachable. Start the backend and refresh.</Center>;
  }

  const user = meQuery.data;
  const authed = user !== null;

  return (
    <Routes>
      <Route
        element={
          <AppLayout username={user?.username} showLogout={authed} />
        }
      >
        <Route path="/setup" element={<Navigate to="/login" replace />} />
        <Route
          path="/login"
          element={authed ? <Navigate to="/" replace /> : <LoginPage />}
        />
        <Route
          path="/"
          element={
            authed && user ? (
              <DashboardPage user={user} />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route path="*" element={<Navigate to={authed ? "/" : "/login"} replace />} />
      </Route>
    </Routes>
  );
}

export function App() {
  const setupQuery = useSetupStatus();

  if (setupQuery.isLoading) return <LoadingScreen />;
  if (setupQuery.isError) {
    return <Center mih="100vh">API unreachable. Start the backend and refresh.</Center>;
  }

  if (setupQuery.data?.needs_setup) {
    return <SetupRoutes />;
  }

  return <AppRoutes />;
}

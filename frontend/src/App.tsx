import { Center, Loader } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { Navigate, Route, Routes } from "react-router-dom";
import { api } from "src/api/client";
import type { SetupStatus, User } from "src/api/auth";
import type { ConnectionsStatus } from "src/api/connections";
import { ApiError } from "src/api/client";
import { AppLayout } from "src/components/layout/AppLayout";
import { DashboardPage } from "src/pages/Dashboard";
import { JobCreatePage } from "src/pages/JobCreatePage";
import { JobEditPage } from "src/pages/JobEditPage";
import { JobsPage } from "src/pages/JobsPage";
import { LoginPage } from "src/pages/LoginPage";
import { ConnectionsPage } from "src/pages/ConnectionsPage";
import { RunDetailPage } from "src/pages/RunDetailPage";
import { RunHistoryPage } from "src/pages/RunHistoryPage";
import { SettingsPage } from "src/pages/Settings";
import { SetupWizardPage } from "src/pages/SetupWizardPage";
import { DisplayPreferencesProvider } from "src/settings/DisplayPreferencesProvider";

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

function useConnectionsStatus(enabled: boolean) {
  return useQuery({
    queryKey: ["connections", "status"],
    queryFn: () => api.get<ConnectionsStatus>("/connections/status"),
    enabled,
  });
}

function AppRoutes() {
  const meQuery = useCurrentUser();
  const authed = meQuery.isSuccess && meQuery.data !== null;
  const connectionsQuery = useConnectionsStatus(authed);

  if (meQuery.isLoading) return <LoadingScreen />;
  if (meQuery.isError) {
    return <Center mih="100vh">API unreachable. Start the backend and refresh.</Center>;
  }

  const user = meQuery.data;

  if (authed && connectionsQuery.isLoading) return <LoadingScreen />;
  if (authed && connectionsQuery.isError) {
    return <Center mih="100vh">API unreachable. Start the backend and refresh.</Center>;
  }

  const needsConnections = authed && connectionsQuery.data?.needs_connections === true;

  return (
    <Routes>
      <Route
        element={
          <AppLayout
            username={user?.username}
            avatarUrl={user?.avatar_url}
            showLogout={authed}
          />
        }
      >
        <Route path="/setup" element={<Navigate to="/login" replace />} />
        <Route
          path="/login"
          element={authed ? <Navigate to="/" replace /> : <LoginPage />}
        />
        <Route
          path="/onboarding"
          element={<Navigate to="/connections" replace />}
        />
        <Route
          path="/connections"
          element={authed ? <ConnectionsPage /> : <Navigate to="/login" replace />}
        />
        <Route
          path="/"
          element={
            authed && user ? (
              needsConnections ? (
                <Navigate to="/connections" replace />
              ) : (
                <DashboardPage user={user} connections={connectionsQuery.data?.connections} />
              )
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/jobs"
          element={authed ? <JobsPage /> : <Navigate to="/login" replace />}
        />
        <Route
          path="/jobs/new"
          element={authed ? <JobCreatePage /> : <Navigate to="/login" replace />}
        />
        <Route
          path="/jobs/:jobId/edit"
          element={authed ? <JobEditPage /> : <Navigate to="/login" replace />}
        />
        <Route
          path="/runs"
          element={authed ? <RunHistoryPage /> : <Navigate to="/login" replace />}
        />
        <Route
          path="/runs/:runId"
          element={authed ? <RunDetailPage /> : <Navigate to="/login" replace />}
        />
        <Route
          path="/settings"
          element={
            authed && user ? (
              <SettingsPage user={user} />
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
    return (
      <DisplayPreferencesProvider>
        <SetupRoutes />
      </DisplayPreferencesProvider>
    );
  }

  return (
    <DisplayPreferencesProvider>
      <AppRoutes />
    </DisplayPreferencesProvider>
  );
}

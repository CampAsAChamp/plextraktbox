import {
  Alert,
  Button,
  Group,
  List,
  PasswordInput,
  Stack,
  Stepper,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { api, ApiError } from "../api/client";
import type {
  ConnectionSummary,
  ConnectionsStatus,
  ConnectionTestResult,
  LetterboxdConnectionInput,
  PlexPinPollInput,
  PlexPinPollResult,
  PlexPinStart,
  Service,
  TmdbConnectionInput,
  TraktDevicePollInput,
  TraktDevicePollResult,
  TraktDeviceStart,
} from "../api/connections";
import {
  isConnectionConfigured,
  SAVED_SECRET_PLACEHOLDER,
  savedUsername,
  secretPlaceholderInputProps,
  showConnectionTestResult,
} from "../components/connections/connectionFormHelpers";
import { ConnectionStatusBadge } from "../components/connections/ConnectionStatusBadge";
import { SERVICE_LABELS } from "../components/connections/connectionStatus";
import { ServiceLogo } from "../components/connections/ServiceLogo";
import { ServiceStepLabel } from "../components/connections/ServiceStepLabel";
import classes from "./OnboardingStepper.module.css";

const tmdbSchema = z.object({
  api_key: z.string().min(1, "API key is required"),
});

const TMDB_API_SETTINGS_URL = "https://www.themoviedb.org/settings/api";

const SERVICE_ORDER = ["plex", "trakt", "letterboxd", "tmdb"] as const;

function ClearConnectionButton({
  service,
  connection,
  onCleared,
  variant = "outline",
}: {
  service: Service;
  connection: ConnectionSummary | undefined;
  onCleared: () => void;
  variant?: "subtle" | "outline";
}) {
  const clear = useMutation({
    mutationFn: () => api.del(`/connections/${service}`),
    onSuccess: () => {
      onCleared();
      notifications.show({
        color: "green",
        message: `${SERVICE_LABELS[service]} connection cleared`,
      });
    },
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message:
          error instanceof ApiError
            ? String(error.message)
            : `Could not clear ${SERVICE_LABELS[service]} connection`,
      });
    },
  });

  if (!connection || connection.status === "unconfigured") return null;

  function handleClear() {
    const confirmed = window.confirm(
      `Remove the saved ${SERVICE_LABELS[service]} connection? You will need to set it up again.`,
    );
    if (confirmed) clear.mutate();
  }

  return (
    <Button
      variant={variant}
      color="red"
      size="xs"
      onClick={handleClear}
      loading={clear.isPending}
      w="fit-content"
    >
      Clear {SERVICE_LABELS[service]} connection
    </Button>
  );
}

function PlexStep({
  connection,
  onSaved,
  onCleared,
}: {
  connection: ConnectionSummary | undefined;
  onSaved: () => void;
  onCleared: () => void;
}) {
  const [pin, setPin] = useState<PlexPinStart | null>(null);
  const [polling, setPolling] = useState(false);
  const [pollError, setPollError] = useState<string | null>(null);
  const pinRef = useRef<PlexPinStart | null>(null);
  pinRef.current = pin;

  const start = useMutation({
    mutationFn: () => api.post<PlexPinStart>("/connections/plex/pin/start"),
    onSuccess: (data) => {
      setPollError(null);
      setPin(data);
      setPolling(true);
      notifications.show({ color: "blue", message: "Sign in to Plex to authorize plextraktbox" });
    },
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Plex authorization failed",
      });
    },
  });

  const poll = useMutation({
    mutationFn: (body: PlexPinPollInput) =>
      api.post<PlexPinPollResult>("/connections/plex/pin/poll", body),
    onSuccess: (data) => {
      if (data.status === "ok") {
        setPolling(false);
        setPin(null);
        notifications.show({ color: "green", message: "Plex connected" });
        onSaved();
      }
    },
    onError: (error: unknown) => {
      setPolling(false);
      const message =
        error instanceof ApiError ? String(error.message) : "Plex authorization failed";
      setPollError(message);
      notifications.show({ color: "red", message });
    },
  });
  const pollMutate = useRef(poll.mutate);
  pollMutate.current = poll.mutate;

  useEffect(() => {
    if (!polling || !pinRef.current || poll.isPending) return undefined;
    const timer = window.setInterval(() => {
      const activePin = pinRef.current;
      if (!activePin?.pin_code) return;
      pollMutate.current({ pin_id: activePin.pin_id, pin_code: activePin.pin_code });
    }, (pinRef.current.interval || 2) * 1000);
    return () => window.clearInterval(timer);
  }, [polling, pin, poll.isPending]);

  useEffect(() => () => setPolling(false), []);

  function cancelAuthorization() {
    setPolling(false);
    setPollError(null);
    setPin(null);
  }

  const showManualCode = pin ? pin.pin_code.length <= 8 : false;
  const configured = isConnectionConfigured(connection);
  const plexConnected = connection?.status === "ok";

  const testSaved = useMutation({
    mutationFn: () => api.post<ConnectionTestResult>("/connections/plex/test"),
    onSuccess: showConnectionTestResult,
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Plex test failed",
      });
    },
  });

  return (
    <Stack gap="sm">
      <Text c="dimmed" size="sm">
        Authorize plextraktbox to access your Plex account. Your server will be discovered
        automatically after you sign in.
      </Text>
      {plexConnected && connection ? (
        <Alert color="green" title="Plex connected">
          <Text size="sm">
            {typeof connection.config.friendly_name === "string"
              ? connection.config.friendly_name
              : "Plex server"}
            {typeof connection.config.url === "string" ? ` — ${connection.config.url}` : ""}
          </Text>
        </Alert>
      ) : null}
      <Group>
        <Button
          onClick={() => start.mutate()}
          loading={start.isPending}
          disabled={plexConnected || pin !== null}
        >
          Connect Plex
        </Button>
        {configured ? (
          <Button
            variant="light"
            onClick={() => testSaved.mutate()}
            loading={testSaved.isPending}
          >
            Test connection
          </Button>
        ) : null}
      </Group>
      {pollError ? (
        <Alert color="red" title="Could not finish Plex setup">
          <Stack gap="xs">
            <Text size="sm">{pollError}</Text>
            <Button
              size="xs"
              variant="light"
              onClick={() => {
                cancelAuthorization();
                start.mutate();
              }}
            >
              Try again
            </Button>
          </Stack>
        </Alert>
      ) : null}
      {pin ? (
        <Alert color="blue" title="Authorize on Plex">
          <Stack gap="xs">
            <Text size="sm">
              Sign in to Plex and approve access for plextraktbox. Use the same browser
              session where you are already signed in to Plex, or sign in when prompted.
            </Text>
            <Button
              component="a"
              href={pin.auth_url}
              target="_blank"
              rel="noreferrer"
              variant="light"
            >
              Open Plex authorization
            </Button>
            {showManualCode ? (
              <Text size="sm">
                Or visit{" "}
                <a href={pin.verification_url} target="_blank" rel="noreferrer">
                  {pin.verification_url}
                </a>{" "}
                and enter code <strong>{pin.pin_code}</strong>.
              </Text>
            ) : null}
            <Text size="sm" c="dimmed">
              Waiting for authorization…
            </Text>
            <Button variant="subtle" size="xs" onClick={cancelAuthorization}>
              Cancel
            </Button>
          </Stack>
        </Alert>
      ) : null}
      <ClearConnectionButton service="plex" connection={connection} onCleared={onCleared} />
    </Stack>
  );
}

function TraktStep({
  connection,
  onSaved,
  onCleared,
}: {
  connection: ConnectionSummary | undefined;
  onSaved: () => void;
  onCleared: () => void;
}) {
  const [device, setDevice] = useState<TraktDeviceStart | null>(null);

  const start = useMutation({
    mutationFn: () => api.post<TraktDeviceStart>("/connections/trakt/device/start"),
    onSuccess: (data) => {
      setDevice(data);
      notifications.show({ color: "blue", message: "Visit Trakt to authorize this device" });
    },
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Trakt authorization failed",
      });
    },
  });

  const poll = useMutation({
    mutationFn: (body: TraktDevicePollInput) =>
      api.post<TraktDevicePollResult>("/connections/trakt/device/poll", body),
    onSuccess: (data) => {
      if (data.status === "ok") {
        setDevice(null);
        notifications.show({ color: "green", message: "Trakt connected" });
        onSaved();
      }
    },
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Trakt authorization failed",
      });
    },
  });
  const pollMutate = useRef(poll.mutate);
  pollMutate.current = poll.mutate;

  useEffect(() => {
    if (!device || poll.isPending) return undefined;
    const timer = window.setInterval(() => {
      pollMutate.current({ device_code: device.device_code });
    }, (device.interval || 5) * 1000);
    return () => window.clearInterval(timer);
  }, [device, poll.isPending]);

  const configured = isConnectionConfigured(connection);
  const traktConnected = connection?.status === "ok";

  const testSaved = useMutation({
    mutationFn: () => api.post<ConnectionTestResult>("/connections/trakt/test"),
    onSuccess: showConnectionTestResult,
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Trakt test failed",
      });
    },
  });

  return (
    <Stack gap="sm">
      <Text c="dimmed" size="sm">
        Authorize plextraktbox to access your Trakt account. You will visit Trakt and enter a
        one-time code.
      </Text>
      {traktConnected ? (
        <Alert color="green" title="Trakt connected">
          <Text size="sm">Your Trakt account is authorized for sync.</Text>
        </Alert>
      ) : null}
      <Group>
        <Button
          onClick={() => start.mutate()}
          loading={start.isPending}
          disabled={traktConnected || device !== null}
        >
          Connect Trakt
        </Button>
        {configured ? (
          <Button
            variant="light"
            onClick={() => testSaved.mutate()}
            loading={testSaved.isPending}
          >
            Test connection
          </Button>
        ) : null}
      </Group>
      {device ? (
        <Alert color="blue" title="Authorize on Trakt">
          <Stack gap="xs">
            <Text size="sm">
              Visit{" "}
              <a href={device.verification_url} target="_blank" rel="noreferrer">
                {device.verification_url}
              </a>{" "}
              and enter code <strong>{device.user_code}</strong>.
            </Text>
            <Text size="sm" c="dimmed">
              Waiting for authorization…
            </Text>
          </Stack>
        </Alert>
      ) : null}
      <ClearConnectionButton service="trakt" connection={connection} onCleared={onCleared} />
    </Stack>
  );
}

function LetterboxdStep({
  connection,
  onSaved,
  onCleared,
}: {
  connection: ConnectionSummary | undefined;
  onSaved: () => void;
  onCleared: () => void;
}) {
  const configured = isConnectionConfigured(connection);
  const baselineUsername = savedUsername(connection);
  const baselinePassword = configured ? SAVED_SECRET_PLACEHOLDER : "";

  const [username, setUsername] = useState(baselineUsername);
  const [password, setPassword] = useState(baselinePassword);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const nextConfigured = isConnectionConfigured(connection);
    setUsername(savedUsername(connection));
    setPassword(nextConfigured ? SAVED_SECRET_PLACEHOLDER : "");
    setErrors({});
  }, [connection?.service, connection?.status, connection?.config.username]);

  const isDirty = username !== baselineUsername || password !== baselinePassword;

  const save = useMutation({
    mutationFn: (body: LetterboxdConnectionInput) =>
      api.post<ConnectionSummary>("/connections/letterboxd", body),
    onSuccess: () => {
      notifications.show({ color: "green", message: "Letterboxd connected" });
      onSaved();
    },
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Letterboxd setup failed",
      });
    },
  });

  const testSaved = useMutation({
    mutationFn: () => api.post<ConnectionTestResult>("/connections/letterboxd/test"),
    onSuccess: showConnectionTestResult,
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Letterboxd test failed",
      });
    },
  });

  const testDraft = useMutation({
    mutationFn: (body: LetterboxdConnectionInput) =>
      api.post<ConnectionTestResult>("/connections/letterboxd/test", body),
    onSuccess: showConnectionTestResult,
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Letterboxd test failed",
      });
    },
  });

  function buildPayload(): LetterboxdConnectionInput | null {
    if (!username.trim()) return null;
    const payload: LetterboxdConnectionInput = { username: username.trim() };
    if (password && password !== SAVED_SECRET_PLACEHOLDER) {
      payload.password = password;
    } else if (!configured) {
      return null;
    }
    return payload;
  }

  function handleTest() {
    if (!isDirty && configured) {
      testSaved.mutate();
      return;
    }
    const payload = buildPayload();
    if (!payload) return;
    testDraft.mutate(payload);
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const payload = buildPayload();
    if (!payload) {
      const fieldErrors: Record<string, string> = {};
      if (!username.trim()) fieldErrors.username = "Username is required";
      if (!configured && (!password || password === SAVED_SECRET_PLACEHOLDER)) {
        fieldErrors.password = "Password is required";
      }
      setErrors(fieldErrors);
      return;
    }
    setErrors({});
    save.mutate(payload);
  }

  const canTest =
    username.trim() !== "" &&
    (configured
      ? password === SAVED_SECRET_PLACEHOLDER || password.trim() !== ""
      : password.trim() !== "" && password !== SAVED_SECRET_PLACEHOLDER);

  return (
    <form onSubmit={handleSubmit}>
      <Stack gap="sm">
        <Text c="dimmed" size="sm">
          Letterboxd is read-only. Your credentials are used to scrape your diary and ratings.
        </Text>
        {connection?.status === "ok" ? (
          <Alert color="green" title="Letterboxd connected">
            <Text size="sm">
              Signed in as <strong>{savedUsername(connection)}</strong>.
            </Text>
          </Alert>
        ) : null}
        <TextInput
          label="Letterboxd username"
          value={username}
          onChange={(event) => setUsername(event.currentTarget.value)}
          error={errors.username}
        />
        <PasswordInput
          label="Letterboxd password"
          onChange={(event) => setPassword(event.currentTarget.value)}
          error={errors.password}
          {...secretPlaceholderInputProps(
            password,
            setPassword,
            configured,
            "Saved password hidden",
            "Saved on the server — enter a new password to replace it.",
          )}
        />
        <Group>
          <Button type="submit" loading={save.isPending} disabled={!isDirty}>
            Save Letterboxd connection
          </Button>
          <Button
            type="button"
            variant="light"
            onClick={handleTest}
            loading={testSaved.isPending || testDraft.isPending}
            disabled={!canTest}
          >
            Test connection
          </Button>
        </Group>
        <ClearConnectionButton service="letterboxd" connection={connection} onCleared={onCleared} />
      </Stack>
    </form>
  );
}

function TmdbStep({
  connection,
  onSaved,
  onCleared,
}: {
  connection: ConnectionSummary | undefined;
  onSaved: () => void;
  onCleared: () => void;
}) {
  const configured = isConnectionConfigured(connection);
  const baselineApiKey = configured ? SAVED_SECRET_PLACEHOLDER : "";

  const [apiKey, setApiKey] = useState(baselineApiKey);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const nextConfigured = isConnectionConfigured(connection);
    setApiKey(nextConfigured ? SAVED_SECRET_PLACEHOLDER : "");
    setErrors({});
  }, [connection?.service, connection?.status]);

  const isDirty = apiKey !== baselineApiKey;

  const save = useMutation({
    mutationFn: (body: TmdbConnectionInput) =>
      api.post<ConnectionSummary>("/connections/tmdb", body),
    onSuccess: () => {
      notifications.show({ color: "green", message: "TMDB connected" });
      onSaved();
    },
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "TMDB setup failed",
      });
    },
  });

  const testSaved = useMutation({
    mutationFn: () => api.post<ConnectionTestResult>("/connections/tmdb/test"),
    onSuccess: showConnectionTestResult,
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "TMDB test failed",
      });
    },
  });

  const testDraft = useMutation({
    mutationFn: (body: TmdbConnectionInput) =>
      api.post<ConnectionTestResult>("/connections/tmdb/test", body),
    onSuccess: showConnectionTestResult,
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "TMDB test failed",
      });
    },
  });

  function handleTest() {
    if (!isDirty && configured) {
      testSaved.mutate();
      return;
    }
    if (!apiKey.trim() || apiKey === SAVED_SECRET_PLACEHOLDER) return;
    testDraft.mutate({ api_key: apiKey.trim() });
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const parsed = tmdbSchema.safeParse({ api_key: apiKey });
    if (!parsed.success || apiKey === SAVED_SECRET_PLACEHOLDER) {
      const fieldErrors: Record<string, string> = {};
      if (!apiKey.trim() || apiKey === SAVED_SECRET_PLACEHOLDER) {
        fieldErrors.api_key = "API key is required";
      }
      for (const issue of parsed.error?.issues ?? []) {
        const key = issue.path[0];
        if (typeof key === "string") fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }
    setErrors({});
    save.mutate(parsed.data);
  }

  const canTest =
    configured && !isDirty
      ? true
      : apiKey.trim() !== "" && apiKey !== SAVED_SECRET_PLACEHOLDER;

  return (
    <form onSubmit={handleSubmit}>
      <Stack gap="sm">
        <Text c="dimmed" size="sm">
          TMDB helps match titles across Plex, Trakt, and Letterboxd.
        </Text>
        {connection?.status === "ok" ? (
          <Alert color="green" title="TMDB connected">
            <Text size="sm">API key saved and ready for title matching.</Text>
          </Alert>
        ) : null}
        <Alert color="blue" title="Get a TMDB API key">
          <Stack gap="xs">
            <List size="sm" spacing="xs">
              <List.Item>
                Sign in or create a free account at{" "}
                <a href="https://www.themoviedb.org/" target="_blank" rel="noreferrer">
                  themoviedb.org
                </a>
              </List.Item>
              <List.Item>
                Open{" "}
                <a href={TMDB_API_SETTINGS_URL} target="_blank" rel="noreferrer">
                  Account Settings → API
                </a>
              </List.Item>
              <List.Item>
                Click <strong>Request an API Key</strong>, choose <strong>Developer</strong>, and
                complete the application form
              </List.Item>
              <List.Item>
                Copy the <strong>API Key</strong> (v3 auth) — not the Read Access Token
              </List.Item>
            </List>
            <Button
              component="a"
              href={TMDB_API_SETTINGS_URL}
              target="_blank"
              rel="noreferrer"
              variant="light"
              size="xs"
              w="fit-content"
            >
              Open TMDB API settings
            </Button>
          </Stack>
        </Alert>
        <PasswordInput
          label="TMDB API key"
          onChange={(event) => setApiKey(event.currentTarget.value)}
          error={errors.api_key}
          {...secretPlaceholderInputProps(
            apiKey,
            setApiKey,
            configured,
            "Saved API key hidden",
            "Saved on the server — enter a new API key to replace it.",
          )}
        />
        <Group>
          <Button type="submit" loading={save.isPending} disabled={!isDirty}>
            Save TMDB connection
          </Button>
          <Button
            type="button"
            variant="light"
            onClick={handleTest}
            loading={testSaved.isPending || testDraft.isPending}
            disabled={!canTest}
          >
            Test connection
          </Button>
        </Group>
        <ClearConnectionButton service="tmdb" connection={connection} onCleared={onCleared} />
      </Stack>
    </form>
  );
}

function resolveActiveStep(
  connections: ConnectionSummary[],
  mode: "onboarding" | "settings",
) {
  for (let index = 0; index < SERVICE_ORDER.length; index += 1) {
    const service = SERVICE_ORDER[index];
    const row = connections.find((item) => item.service === service);
    if (!row || row.status !== "ok") return index;
  }
  if (mode === "onboarding") return SERVICE_ORDER.length;
  return 0;
}

function stepIconClass(connection: ConnectionSummary | undefined) {
  return connection?.status === "ok"
    ? `${classes.stepIcon} ${classes.stepIconConnected}`
    : classes.stepIcon;
}

function FinishedStep({
  connections,
  onGoToDashboard,
}: {
  connections: ConnectionSummary[];
  onGoToDashboard: () => void;
}) {
  return (
    <Stack gap="md">
      <Alert color="green" title="All services connected">
        <Text size="sm">
          Plex, Trakt, Letterboxd, and TMDB are configured. You can manage connections
          anytime from the dashboard.
        </Text>
      </Alert>
      <Group gap="xs">
        {connections.map((item) => (
          <ConnectionStatusBadge key={item.service} connection={item} />
        ))}
      </Group>
      <Button onClick={onGoToDashboard} w="fit-content">
        Go to dashboard
      </Button>
    </Stack>
  );
}

interface OnboardingPageProps {
  mode?: "onboarding" | "settings";
}

export function OnboardingPage({ mode = "onboarding" }: OnboardingPageProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const statusQuery = useQuery({
    queryKey: ["connections", "status"],
    queryFn: () => api.get<ConnectionsStatus>("/connections/status"),
  });

  const [active, setActive] = useState(0);
  const prevModeRef = useRef(mode);

  useEffect(() => {
    if (!statusQuery.data) return;
    const modeChanged = prevModeRef.current !== mode;
    prevModeRef.current = mode;
    const step = resolveActiveStep(statusQuery.data.connections, mode);
    setActive((current) => {
      if (mode === "onboarding" && current === SERVICE_ORDER.length) return current;
      if (mode === "settings" && !modeChanged) return current;
      return step;
    });
  }, [statusQuery.data, mode]);

  function refreshStatus() {
    void queryClient.invalidateQueries({ queryKey: ["connections", "status"] });
  }

  const clearAll = useMutation({
    mutationFn: () => api.del("/connections"),
    onSuccess: () => {
      setActive(0);
      refreshStatus();
      notifications.show({ color: "green", message: "All connections cleared" });
    },
    onError: (error: unknown) => {
      notifications.show({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Could not clear connections",
      });
    },
  });

  function handleConnectionCleared() {
    refreshStatus();
  }

  function handleGoToDashboard() {
    navigate("/", { replace: true });
  }

  function handleClearAll() {
    const confirmed = window.confirm(
      "Remove all saved Plex, Trakt, Letterboxd, and TMDB connections? You will need to set them up again.",
    );
    if (confirmed) clearAll.mutate();
  }

  if (statusQuery.isLoading) {
    return <Text>Loading connections…</Text>;
  }

  const connections = statusQuery.data?.connections ?? [];
  const hasConfiguredConnections = connections.some((item) => item.status !== "unconfigured");

  function connectionFor(service: Service) {
    return connections.find((item) => item.service === service);
  }

  return (
    <Stack gap="md" maw={640}>
      <Title order={3}>
        {mode === "onboarding" ? "Connect your services" : "Manage connections"}
      </Title>
      <Text c="dimmed" size="sm">
        Configure Plex, Trakt, Letterboxd, and TMDB before running sync jobs.
      </Text>

      <Group gap="xs">
        {connections.map((item) => (
          <ConnectionStatusBadge key={item.service} connection={item} />
        ))}
      </Group>

      {mode === "settings" && hasConfiguredConnections ? (
        <Group justify="flex-end">
          <Button
            variant="outline"
            color="red"
            onClick={handleClearAll}
            loading={clearAll.isPending}
          >
            Clear all connections
          </Button>
        </Group>
      ) : null}

      <Stepper
        active={active}
        onStepClick={setActive}
        classNames={{ stepIcon: classes.stepIcon }}
      >
        <Stepper.Step
          classNames={{ stepIcon: stepIconClass(connectionFor("plex")) }}
          icon={<ServiceLogo service="plex" size={18} />}
          completedIcon={<ServiceLogo service="plex" size={18} />}
          label={<ServiceStepLabel service="plex" connection={connectionFor("plex")} />}
          description="Plex account"
        >
          <PlexStep
            connection={connectionFor("plex")}
            onSaved={() => {
              refreshStatus();
              setActive(1);
            }}
            onCleared={handleConnectionCleared}
          />
        </Stepper.Step>
        <Stepper.Step
          classNames={{ stepIcon: stepIconClass(connectionFor("trakt")) }}
          icon={<ServiceLogo service="trakt" size={18} />}
          completedIcon={<ServiceLogo service="trakt" size={18} />}
          label={<ServiceStepLabel service="trakt" connection={connectionFor("trakt")} />}
          description="Device OAuth"
        >
          <TraktStep
            connection={connectionFor("trakt")}
            onSaved={() => {
              refreshStatus();
              setActive(2);
            }}
            onCleared={handleConnectionCleared}
          />
        </Stepper.Step>
        <Stepper.Step
          classNames={{ stepIcon: stepIconClass(connectionFor("letterboxd")) }}
          icon={<ServiceLogo service="letterboxd" size={18} />}
          completedIcon={<ServiceLogo service="letterboxd" size={18} />}
          label={
            <ServiceStepLabel service="letterboxd" connection={connectionFor("letterboxd")} />
          }
          description="Read-only login"
        >
          <LetterboxdStep
            connection={connectionFor("letterboxd")}
            onSaved={() => {
              refreshStatus();
              setActive(3);
            }}
            onCleared={handleConnectionCleared}
          />
        </Stepper.Step>
        <Stepper.Step
          classNames={{ stepIcon: stepIconClass(connectionFor("tmdb")) }}
          icon={<ServiceLogo service="tmdb" size={18} />}
          completedIcon={<ServiceLogo service="tmdb" size={18} />}
          label={<ServiceStepLabel service="tmdb" connection={connectionFor("tmdb")} />}
          description="API key"
        >
          <TmdbStep
            connection={connectionFor("tmdb")}
            onSaved={() => {
              refreshStatus();
              if (mode === "onboarding") {
                setActive(SERVICE_ORDER.length);
              }
            }}
            onCleared={handleConnectionCleared}
          />
        </Stepper.Step>

        {mode === "onboarding" ? (
          <Stepper.Completed>
            <FinishedStep connections={connections} onGoToDashboard={handleGoToDashboard} />
          </Stepper.Completed>
        ) : null}
      </Stepper>
    </Stack>
  );
}

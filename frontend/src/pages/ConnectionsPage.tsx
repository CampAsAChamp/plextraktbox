import {
  Accordion,
  Alert,
  Button,
  Checkbox,
  Group,
  List,
  PasswordInput,
  Stack,
  Stepper,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { useMediaQuery } from "@mantine/hooks";
import { showToast } from "../toast";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type ReactNode } from "react";
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
  PlexLibrariesResponse,
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
} from "../components/connections/connectionFormHelpers";
import {
  TestConnectionButton,
  useConnectionTestFeedback,
} from "../components/connections/connectionTestFeedback";
import { SERVICE_LABELS } from "../components/connections/connectionStatus";
import { ServiceLogo } from "../components/connections/ServiceLogo";
import { ServiceStepLabel } from "../components/connections/ServiceStepLabel";
import { StatusCheckIcon } from "../components/connections/StatusCheckIcon";
import { ConnectIcon } from "../components/icons/ConnectIcon";
import { FilmIcon } from "../components/icons/FilmIcon";
import { HomeIcon } from "../components/icons/HomeIcon";
import { KeyIcon } from "../components/icons/KeyIcon";
import { LockIcon } from "../components/icons/LockIcon";
import { SaveIcon } from "../components/icons/SaveIcon";
import { TrashIcon } from "../components/icons/TrashIcon";
import { TvIcon } from "../components/icons/TvIcon";
import { UserIcon } from "../components/icons/UserIcon";
import classes from "./OnboardingStepper.module.css";

const tmdbSchema = z.object({
  api_key: z.string().min(1, "API key is required"),
});

const TMDB_API_SETTINGS_URL = "https://www.themoviedb.org/settings/api";

const SERVICE_ORDER = ["plex", "trakt", "letterboxd", "tmdb"] as const;

function FieldLabel({
  icon,
  children,
}: {
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <Group gap={6} wrap="nowrap">
      <span style={{ display: "inline-flex", color: "var(--mantine-color-dimmed)" }}>{icon}</span>
      <span>{children}</span>
    </Group>
  );
}

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
      showToast({
        color: "green",
        message: `${SERVICE_LABELS[service]} connection cleared`,
      });
    },
    onError: (error: unknown) => {
      showToast({
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
      leftSection={<TrashIcon />}
      onClick={handleClear}
      loading={clear.isPending}
      w="fit-content"
    >
      Clear {SERVICE_LABELS[service]} connection
    </Button>
  );
}

function PlexLibraryPicker({ enabled }: { enabled: boolean }) {
  const queryClient = useQueryClient();
  const librariesQuery = useQuery({
    queryKey: ["connections", "plex", "libraries"],
    queryFn: () => api.get<PlexLibrariesResponse>("/connections/plex/libraries"),
    enabled,
  });
  const [selected, setSelected] = useState<string[]>([]);

  useEffect(() => {
    if (librariesQuery.data) {
      setSelected(librariesQuery.data.selected_ids);
    }
  }, [librariesQuery.data]);

  const save = useMutation({
    mutationFn: (libraryIds: string[]) =>
      api.put<ConnectionSummary>("/connections/plex/libraries", { library_ids: libraryIds }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connections"] });
      queryClient.invalidateQueries({ queryKey: ["connections", "plex", "libraries"] });
      showToast({ color: "green", message: "Plex library selection saved" });
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Could not save Plex libraries",
      });
    },
  });

  if (!enabled) {
    return null;
  }

  if (librariesQuery.isLoading) {
    return <Text size="sm">Loading Plex libraries…</Text>;
  }

  if (librariesQuery.isError || !librariesQuery.data) {
    return (
      <Alert color="yellow" title="Could not load Plex libraries">
        Connect and test Plex first, then choose which Plex libraries to sync.
      </Alert>
    );
  }

  const { libraries } = librariesQuery.data;
  if (libraries.length === 0) {
    return (
      <Alert color="yellow" title="No Plex libraries">
        Add a movie or show library to your Plex server to sync ratings and watched history.
      </Alert>
    );
  }

  return (
    <Stack gap="xs">
      <Text fw={500} size="sm">
        Plex libraries to sync
      </Text>
      <Text c="dimmed" size="sm">
        Movie ratings and movie/episode watched history are fetched from the libraries you select.
        Show libraries enable episode watched sync; leave all unchecked to include every movie and
        show library.
      </Text>
      <Checkbox.Group value={selected} onChange={setSelected}>
        <Stack gap="xs">
          {libraries.map((library) => (
            <Checkbox
              key={library.id}
              value={library.id}
              label={
                <Group gap="xs" wrap="nowrap">
                  {library.type === "show" ? <TvIcon /> : <FilmIcon />}
                  <span>{library.title}</span>
                  <Text size="sm" c="dimmed" component="span">
                    {library.type === "show" ? "TV" : "Movies"}
                  </Text>
                </Group>
              }
            />
          ))}
        </Stack>
      </Checkbox.Group>
      <Button
        variant="light"
        w="fit-content"
        loading={save.isPending}
        leftSection={<SaveIcon />}
        onClick={() => save.mutate(selected)}
      >
        Save Plex library selection
      </Button>
    </Stack>
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
      showToast({ color: "blue", message: "Sign in to Plex to authorize plextraktbox" });
    },
    onError: (error: unknown) => {
      showToast({
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
        showToast({ color: "green", message: "Plex connected" });
        onSaved();
      }
    },
    onError: (error: unknown) => {
      setPolling(false);
      const message =
        error instanceof ApiError ? String(error.message) : "Plex authorization failed";
      setPollError(message);
      showToast({ color: "red", message });
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
  const { testStatus, onTestSuccess, onTestError, resetTestStatus } = useConnectionTestFeedback();

  useEffect(() => {
    resetTestStatus();
  }, [connection?.service, connection?.status, resetTestStatus]);

  const testSaved = useMutation({
    mutationFn: () => api.post<ConnectionTestResult>("/connections/plex/test", {}),
    onSuccess: onTestSuccess,
    onError: (error: unknown) => onTestError(error, "Plex test failed"),
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
      <Group wrap="wrap">
        <Button
          onClick={() => start.mutate()}
          loading={start.isPending}
          disabled={plexConnected || pin !== null}
          leftSection={<ConnectIcon />}
        >
          Connect Plex
        </Button>
        {configured ? (
          <TestConnectionButton
            testStatus={testStatus}
            onClick={() => testSaved.mutate()}
            loading={testSaved.isPending}
          />
        ) : null}
        <ClearConnectionButton service="plex" connection={connection} onCleared={onCleared} />
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
      <PlexLibraryPicker enabled={plexConnected} />
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
      showToast({ color: "blue", message: "Visit Trakt to authorize this device" });
    },
    onError: (error: unknown) => {
      showToast({
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
        showToast({ color: "green", message: "Trakt connected" });
        onSaved();
      }
    },
    onError: (error: unknown) => {
      showToast({
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
  const { testStatus, onTestSuccess, onTestError, resetTestStatus } = useConnectionTestFeedback();

  useEffect(() => {
    resetTestStatus();
  }, [connection?.service, connection?.status, resetTestStatus]);

  const testSaved = useMutation({
    mutationFn: () => api.post<ConnectionTestResult>("/connections/trakt/test", {}),
    onSuccess: onTestSuccess,
    onError: (error: unknown) => onTestError(error, "Trakt test failed"),
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
      <Group wrap="wrap">
        <Button
          onClick={() => start.mutate()}
          loading={start.isPending}
          disabled={traktConnected || device !== null}
          leftSection={<ConnectIcon />}
        >
          Connect Trakt
        </Button>
        {configured ? (
          <TestConnectionButton
            testStatus={testStatus}
            onClick={() => testSaved.mutate()}
            loading={testSaved.isPending}
          />
        ) : null}
        <ClearConnectionButton service="trakt" connection={connection} onCleared={onCleared} />
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
  const { testStatus, onTestSuccess, onTestError, resetTestStatus } = useConnectionTestFeedback();

  useEffect(() => {
    resetTestStatus();
  }, [connection?.service, connection?.status, resetTestStatus]);

  useEffect(() => {
    if (isDirty) resetTestStatus();
  }, [isDirty, resetTestStatus]);

  const save = useMutation({
    mutationFn: (body: LetterboxdConnectionInput) =>
      api.post<ConnectionSummary>("/connections/letterboxd", body),
    onSuccess: () => {
      showToast({ color: "green", message: "Letterboxd connected" });
      onSaved();
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Letterboxd setup failed",
      });
    },
  });

  const testSaved = useMutation({
    mutationFn: () => api.post<ConnectionTestResult>("/connections/letterboxd/test", {}),
    onSuccess: onTestSuccess,
    onError: (error: unknown) => onTestError(error, "Letterboxd test failed"),
  });

  const testDraft = useMutation({
    mutationFn: (body: LetterboxdConnectionInput) =>
      api.post<ConnectionTestResult>("/connections/letterboxd/test", body),
    onSuccess: onTestSuccess,
    onError: (error: unknown) => onTestError(error, "Letterboxd test failed"),
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
          label={
            <FieldLabel icon={<UserIcon />}>Letterboxd username</FieldLabel>
          }
          value={username}
          onChange={(event) => setUsername(event.currentTarget.value)}
          error={errors.username}
        />
        <PasswordInput
          label={
            <FieldLabel icon={<LockIcon />}>Letterboxd password</FieldLabel>
          }
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
        <Group wrap="wrap">
          <Button type="submit" loading={save.isPending} disabled={!isDirty} leftSection={<SaveIcon />}>
            Save Letterboxd connection
          </Button>
          <TestConnectionButton
            testStatus={testStatus}
            onClick={handleTest}
            loading={testSaved.isPending || testDraft.isPending}
            disabled={!canTest}
          />
          <ClearConnectionButton service="letterboxd" connection={connection} onCleared={onCleared} />
        </Group>
      </Stack>
    </form>
  );
}

function TmdbApiKeyHelpContent() {
  return (
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
          Click <strong>Request an API Key</strong>, choose <strong>Developer</strong>, and complete
          the application form
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
  );
}

function TmdbApiKeyHelp({
  collapsible,
  expanded,
  onExpandedChange,
}: {
  collapsible: boolean;
  expanded: boolean;
  onExpandedChange: (next: boolean) => void;
}) {
  if (!collapsible) {
    return (
      <Alert color="blue" title="Get a TMDB API key">
        <TmdbApiKeyHelpContent />
      </Alert>
    );
  }

  return (
    <Alert
      color="blue"
      p={0}
      styles={{
        root: { overflow: "hidden" },
        message: { margin: 0 },
      }}
    >
      <Accordion
        chevronPosition="right"
        onChange={(value) => onExpandedChange(value === "help")}
        styles={{
          chevron: { color: "var(--mantine-color-blue-light-color)" },
          control: { padding: "var(--mantine-spacing-md)" },
          label: { color: "var(--mantine-color-blue-light-color)", fontWeight: 600 },
          panel: { padding: "0 var(--mantine-spacing-md) var(--mantine-spacing-md)" },
        }}
        value={expanded ? "help" : null}
        variant="unstyled"
      >
        <Accordion.Item style={{ border: "none" }} value="help">
          <Accordion.Control>Get a TMDB API key</Accordion.Control>
          <Accordion.Panel>
            <TmdbApiKeyHelpContent />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Alert>
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
  const [showTmdbHelp, setShowTmdbHelp] = useState(!configured);

  useEffect(() => {
    const nextConfigured = isConnectionConfigured(connection);
    setApiKey(nextConfigured ? SAVED_SECRET_PLACEHOLDER : "");
    setErrors({});
    setShowTmdbHelp(!nextConfigured);
  }, [connection?.service, connection?.status]);

  const isDirty = apiKey !== baselineApiKey;
  const { testStatus, onTestSuccess, onTestError, resetTestStatus } = useConnectionTestFeedback();

  useEffect(() => {
    resetTestStatus();
  }, [connection?.service, connection?.status, resetTestStatus]);

  useEffect(() => {
    if (isDirty) resetTestStatus();
  }, [isDirty, resetTestStatus]);

  const save = useMutation({
    mutationFn: (body: TmdbConnectionInput) =>
      api.post<ConnectionSummary>("/connections/tmdb", body),
    onSuccess: () => {
      showToast({ color: "green", message: "TMDB connected" });
      onSaved();
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "TMDB setup failed",
      });
    },
  });

  const testSaved = useMutation({
    mutationFn: () => api.post<ConnectionTestResult>("/connections/tmdb/test", {}),
    onSuccess: onTestSuccess,
    onError: (error: unknown) => onTestError(error, "TMDB test failed"),
  });

  const testDraft = useMutation({
    mutationFn: (body: TmdbConnectionInput) =>
      api.post<ConnectionTestResult>("/connections/tmdb/test", body),
    onSuccess: onTestSuccess,
    onError: (error: unknown) => onTestError(error, "TMDB test failed"),
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
        <TmdbApiKeyHelp
          collapsible={configured}
          expanded={showTmdbHelp}
          onExpandedChange={setShowTmdbHelp}
        />
        <PasswordInput
          label={<FieldLabel icon={<KeyIcon />}>TMDB API key</FieldLabel>}
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
        <Group wrap="wrap">
          <Button type="submit" loading={save.isPending} disabled={!isDirty} leftSection={<SaveIcon />}>
            Save TMDB connection
          </Button>
          <TestConnectionButton
            testStatus={testStatus}
            onClick={handleTest}
            loading={testSaved.isPending || testDraft.isPending}
            disabled={!canTest}
          />
          <ClearConnectionButton service="tmdb" connection={connection} onCleared={onCleared} />
        </Group>
      </Stack>
    </form>
  );
}

function resolveActiveStep(connections: ConnectionSummary[]) {
  for (let index = 0; index < SERVICE_ORDER.length; index += 1) {
    const service = SERVICE_ORDER[index];
    const row = connections.find((item) => item.service === service);
    if (!row || row.status !== "ok") return index;
  }
  return SERVICE_ORDER.length;
}

function allConnectionsOk(connections: ConnectionSummary[]) {
  return SERVICE_ORDER.every((service) => {
    const row = connections.find((item) => item.service === service);
    return row?.status === "ok";
  });
}

function stepIconClass(connection: ConnectionSummary | undefined) {
  return connection?.status === "ok"
    ? `${classes.stepIcon} ${classes.stepIconConnected}`
    : classes.stepIcon;
}

function FinishedStep({
  onGoToDashboard,
}: {
  onGoToDashboard: () => void;
}) {
  return (
    <Stack gap="md">
      <Alert
        color="green"
        title="All connections successful"
        icon={
          <span style={{ display: "inline-flex" }}>
            <StatusCheckIcon size={16} />
          </span>
        }
      >
        <Text size="sm">
          Plex, Trakt, Letterboxd, and TMDB are configured and ready for sync. Use the steps above
          anytime to review or update a connection.
        </Text>
      </Alert>
      <Button onClick={onGoToDashboard} w="fit-content" leftSection={<HomeIcon />}>
        Go to dashboard
      </Button>
    </Stack>
  );
}

export function ConnectionsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isNarrow = useMediaQuery("(max-width: 47.997em)");
  const statusQuery = useQuery({
    queryKey: ["connections", "status"],
    queryFn: () => api.get<ConnectionsStatus>("/connections/status"),
  });

  const [active, setActive] = useState(0);
  const prevNeedsConnectionsRef = useRef<boolean | undefined>(undefined);

  const needsConnections = statusQuery.data?.needs_connections === true;

  useEffect(() => {
    if (!statusQuery.data) return;
    const needsChanged = prevNeedsConnectionsRef.current !== statusQuery.data.needs_connections;
    prevNeedsConnectionsRef.current = statusQuery.data.needs_connections;
    const step = resolveActiveStep(statusQuery.data.connections);
    const allOk = allConnectionsOk(statusQuery.data.connections);
    setActive((current) => {
      if (current === SERVICE_ORDER.length) return current;
      if (allOk) return step;
      if (!statusQuery.data.needs_connections && !needsChanged) return current;
      return step;
    });
  }, [statusQuery.data]);

  function refreshStatus() {
    void queryClient.invalidateQueries({ queryKey: ["connections", "status"] });
  }

  const clearAll = useMutation({
    mutationFn: () => api.del("/connections"),
    onSuccess: () => {
      setActive(0);
      refreshStatus();
      showToast({ color: "green", message: "All connections cleared" });
    },
    onError: (error: unknown) => {
      showToast({
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
    <Stack gap="md" maw={{ base: "100%", lg: "85%" }} mx="auto">
      <Title order={3}>{needsConnections ? "Connect your services" : "Connections"}</Title>
      <Text c="dimmed" size="sm">
        {needsConnections
          ? "Configure Plex, Trakt, Letterboxd, and TMDB before running sync jobs."
          : "Manage Plex, Trakt, Letterboxd, and TMDB credentials for sync jobs."}
      </Text>

      {!needsConnections && hasConfiguredConnections ? (
        <Group justify="flex-end" wrap="wrap">
          <Button
            variant="outline"
            color="red"
            leftSection={<TrashIcon />}
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
        orientation={isNarrow ? "vertical" : "horizontal"}
        classNames={{
          stepIcon: classes.stepIcon,
          stepCompletedIcon: classes.stepCompletedIcon,
        }}
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
              setActive(SERVICE_ORDER.length);
            }}
            onCleared={handleConnectionCleared}
          />
        </Stepper.Step>

        <Stepper.Completed>
          <FinishedStep onGoToDashboard={handleGoToDashboard} />
        </Stepper.Completed>
      </Stepper>
    </Stack>
  );
}

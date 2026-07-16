import {
  Box,
  Button,
  Checkbox,
  Divider,
  Group,
  Paper,
  Stack,
  Switch,
  Text,
  TextInput,
} from "@mantine/core";
import { showToast } from "src/toast";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  CHANNEL_LABELS,
  createNotificationConfig,
  deleteNotificationConfig,
  listNotificationConfigs,
  testNotificationConfig,
  updateNotificationConfig,
  type NotificationChannel,
  type NotificationConfig,
} from "src/api/notifications";
import { ApiError } from "src/api/client";
import { SettingsSectionTitle } from "src/components/SettingsSectionTitle";
import { BellIcon } from "src/components/icons/BellIcon";
import { DiscordIcon } from "src/components/icons/DiscordIcon";
import { SaveIcon } from "src/components/icons/SaveIcon";

const CHANNELS: NotificationChannel[] = ["discord", "inapp"];
const DISCORD_BLURPLE = "#5865F2";

interface ChannelFormState {
  enabled: boolean;
  onSuccess: boolean;
  onFailure: boolean;
  webhookUrl: string;
}

function defaultFormState(): ChannelFormState {
  return {
    enabled: true,
    onSuccess: true,
    onFailure: true,
    webhookUrl: "",
  };
}

function configToFormState(config: NotificationConfig | undefined): ChannelFormState {
  const base = defaultFormState();
  if (!config) return base;
  return {
    enabled: config.enabled,
    onSuccess: config.on_success,
    onFailure: config.on_failure,
    webhookUrl: "",
  };
}

function ChannelSettings({
  channel,
  config,
  onSaved,
}: {
  channel: NotificationChannel;
  config: NotificationConfig | undefined;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<ChannelFormState>(() => configToFormState(config));

  useEffect(() => {
    setForm(configToFormState(config));
  }, [config]);

  const save = useMutation({
    mutationFn: async () => {
      if (config) {
        return updateNotificationConfig(config.id, {
          enabled: form.enabled,
          on_success: form.onSuccess,
          on_failure: form.onFailure,
          discord:
            channel === "discord" && form.webhookUrl
              ? { webhook_url: form.webhookUrl }
              : undefined,
        });
      }
      return createNotificationConfig({
        channel,
        enabled: form.enabled,
        on_success: form.onSuccess,
        on_failure: form.onFailure,
        scope: "global",
        discord:
          channel === "discord" ? { webhook_url: form.webhookUrl } : undefined,
      });
    },
    onSuccess: () => {
      showToast({ color: "green", message: `${CHANNEL_LABELS[channel]} settings saved` });
      onSaved();
    },
    onError: (error) => {
      const message = error instanceof ApiError ? error.message : "Save failed";
      showToast({ color: "red", message });
    },
  });

  const remove = useMutation({
    mutationFn: () => deleteNotificationConfig(config!.id),
    onSuccess: () => {
      showToast({ color: "green", message: `${CHANNEL_LABELS[channel]} removed` });
      onSaved();
    },
  });

  const test = useMutation({
    mutationFn: () => testNotificationConfig(config!.id),
    onSuccess: () => {
      showToast({ color: "green", message: "Test notification sent" });
      onSaved();
    },
    onError: (error) => {
      const message = error instanceof ApiError ? error.message : "Test failed";
      showToast({ color: "red", message });
    },
  });

  const body = (
    <Stack gap="sm">
      <Group justify="space-between" wrap="wrap" gap="sm">
        <Group gap="sm">
          {channel === "discord" ? <DiscordIcon size={22} /> : null}
          <Text fw={600} c={channel === "discord" ? DISCORD_BLURPLE : undefined}>
            {CHANNEL_LABELS[channel]}
          </Text>
        </Group>
        <Switch
          label="Enabled"
          checked={form.enabled}
          onChange={(event) => setForm((current) => ({ ...current, enabled: event.currentTarget.checked }))}
        />
      </Group>

      <Group wrap="wrap">
        <Checkbox
          label="On success"
          checked={form.onSuccess}
          onChange={(event) =>
            setForm((current) => ({ ...current, onSuccess: event.currentTarget.checked }))
          }
        />
        <Checkbox
          label="On failure"
          checked={form.onFailure}
          onChange={(event) =>
            setForm((current) => ({ ...current, onFailure: event.currentTarget.checked }))
          }
        />
      </Group>

      {channel === "discord" ? (
        <TextInput
          label="Webhook URL"
          description={
            config?.has_secret ? "Leave blank to keep the existing webhook URL" : undefined
          }
          value={form.webhookUrl}
          onChange={(event) => setForm((current) => ({ ...current, webhookUrl: event.currentTarget.value }))}
          placeholder={config?.has_secret ? "Configured" : "https://discord.com/api/webhooks/..."}
        />
      ) : null}

      {channel === "inapp" ? (
        <Text size="sm" c="dimmed">
          In-app notifications appear in the bell menu after each job run.
        </Text>
      ) : null}

      <Group wrap="wrap">
        <Button loading={save.isPending} onClick={() => save.mutate()} leftSection={<SaveIcon />}>
          Save
        </Button>
        {config ? (
          <>
            <Button variant="light" loading={test.isPending} onClick={() => test.mutate()}>
              Send test
            </Button>
            <Button
              variant="subtle"
              color="red"
              loading={remove.isPending}
              onClick={() => remove.mutate()}
            >
              Remove
            </Button>
          </>
        ) : null}
      </Group>
    </Stack>
  );

  if (channel === "discord") {
    return (
      <Box
        p="sm"
        style={{
          borderLeft: `3px solid ${DISCORD_BLURPLE}`,
          borderRadius: "var(--mantine-radius-lg)",
          background:
            "color-mix(in srgb, var(--mantine-color-body) 92%, #5865F2 8%)",
        }}
      >
        {body}
      </Box>
    );
  }

  return body;
}

export function NotificationSettings() {
  const queryClient = useQueryClient();
  const configsQuery = useQuery({
    queryKey: ["notifications", "configs", "global"],
    queryFn: () => listNotificationConfigs(),
  });

  const globalConfigs = (configsQuery.data ?? []).filter((item) => item.scope === "global");
  const configByChannel = Object.fromEntries(globalConfigs.map((item) => [item.channel, item])) as Partial<
    Record<NotificationChannel, NotificationConfig>
  >;

  function refresh() {
    void queryClient.invalidateQueries({ queryKey: ["notifications"] });
  }

  return (
    <Paper
      id="settings-notifications"
      withBorder
      p="md"
      data-settings-section="Notifications"
      style={{ scrollMarginTop: 80 }}
    >
      <Stack gap="md">
        <Stack gap={4}>
          <SettingsSectionTitle icon={<BellIcon size={18} />}>Notifications</SettingsSectionTitle>
          <Text size="sm" c="dimmed">
            Configure global alerts for completed job runs. Jobs can inherit these settings or use
            custom per-job channels.
          </Text>
        </Stack>

        {CHANNELS.map((channel, index) => (
          <Stack key={channel} gap="sm">
            {index > 0 ? <Divider /> : null}
            <ChannelSettings
              channel={channel}
              config={configByChannel[channel]}
              onSaved={refresh}
            />
          </Stack>
        ))}
      </Stack>
    </Paper>
  );
}

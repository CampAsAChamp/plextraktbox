import { Button, Checkbox, Group, NumberInput, Paper, Stack, Text } from "@mantine/core";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";
import { ApiError } from "src/api/client";
import {
  clearSyncCaches,
  getSettings,
  updateSettings,
  type AppSettingsInput,
} from "src/api/settings";
import { SettingsSectionTitle } from "src/components/SettingsSectionTitle";
import { SaveIcon } from "src/components/icons/SaveIcon";
import { SyncIcon } from "src/components/icons/SyncIcon";
import { showToast } from "src/toast";

export function SyncCachesSection() {
  const queryClient = useQueryClient();
  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  const [exportTtlHours, setExportTtlHours] = useState(24);
  const [traktTtlMinutes, setTraktTtlMinutes] = useState(30);
  const [clearExport, setClearExport] = useState(true);
  const [clearSlug, setClearSlug] = useState(true);
  const [clearTrakt, setClearTrakt] = useState(true);
  const [clearDiscover, setClearDiscover] = useState(true);

  useEffect(() => {
    const data = settingsQuery.data;
    if (!data) return;
    setExportTtlHours(data.letterboxd_export_cache_ttl_hours);
    setTraktTtlMinutes(data.trakt_list_cache_ttl_minutes);
  }, [settingsQuery.data]);

  const saveMutation = useMutation({
    mutationFn: (input: AppSettingsInput) => updateSettings(input),
    onSuccess: (data) => {
      void queryClient.setQueryData(["settings"], data);
      showToast({ color: "green", message: "Cache settings saved" });
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Save failed";
      showToast({ color: "red", message });
    },
  });

  const clearMutation = useMutation({
    mutationFn: () =>
      clearSyncCaches({
        letterboxd_export: clearExport,
        letterboxd_slug: clearSlug,
        trakt_lists: clearTrakt,
        discover_keys: clearDiscover,
      }),
    onSuccess: (result) => {
      showToast({
        color: "green",
        message:
          `Cleared caches (export dirs=${result.letterboxd_export}, ` +
          `slugs=${result.letterboxd_slug}, trakt=${result.trakt_lists}, ` +
          `discover=${result.discover_keys})`,
      });
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Clear failed";
      showToast({ color: "red", message });
    },
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const data = settingsQuery.data;
    if (!data) return;
    if (exportTtlHours < 1 || traktTtlMinutes < 1) {
      showToast({ color: "red", message: "Cache TTLs must be at least 1" });
      return;
    }
    saveMutation.mutate({
      default_cron: data.default_cron,
      cron_timezone: data.cron_timezone,
      log_retention_days: data.log_retention_days,
      global_dry_run: data.global_dry_run,
      exclude_ids: data.exclude_ids,
      letterboxd_export_cache_ttl_hours: exportTtlHours,
      trakt_list_cache_ttl_minutes: traktTtlMinutes,
    });
  }

  return (
    <Paper
      id="settings-sync-caches"
      withBorder
      p="md"
      data-settings-section="Sync caches"
      style={{ scrollMarginTop: 80 }}
    >
      <Stack gap="md">
        <SettingsSectionTitle icon={<SyncIcon size={18} />}>Sync caches</SettingsSectionTitle>
        <Text size="sm" c="dimmed">
          Reuse Letterboxd exports, Trakt lists, slug→ID resolves, and Plex Discover keys across
          sync runs. Plex library walks are still once-per-run only (not persisted).
        </Text>

        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            <NumberInput
              label="Letterboxd export cache TTL (hours)"
              description="Reuse the downloaded CSV ZIP until this TTL expires"
              min={1}
              max={720}
              value={exportTtlHours}
              onChange={(value) => setExportTtlHours(typeof value === "number" ? value : 24)}
              disabled={settingsQuery.isLoading}
            />
            <NumberInput
              label="Trakt list cache TTL (minutes)"
              description="Cache watchlist / ratings / watched list fetches"
              min={1}
              max={1440}
              value={traktTtlMinutes}
              onChange={(value) => setTraktTtlMinutes(typeof value === "number" ? value : 30)}
              disabled={settingsQuery.isLoading}
            />
            <Group>
              <Button
                type="submit"
                loading={saveMutation.isPending}
                leftSection={<SaveIcon />}
                disabled={settingsQuery.isLoading}
              >
                Save cache settings
              </Button>
            </Group>
          </Stack>
        </form>

        <Stack gap="xs">
          <Text fw={500}>Clear caches</Text>
          <Checkbox
            label="Letterboxd export files"
            checked={clearExport}
            onChange={(event) => setClearExport(event.currentTarget.checked)}
          />
          <Checkbox
            label="Letterboxd slug → IDs"
            checked={clearSlug}
            onChange={(event) => setClearSlug(event.currentTarget.checked)}
          />
          <Checkbox
            label="Trakt list snapshots"
            checked={clearTrakt}
            onChange={(event) => setClearTrakt(event.currentTarget.checked)}
          />
          <Checkbox
            label="Plex Discover keys"
            checked={clearDiscover}
            onChange={(event) => setClearDiscover(event.currentTarget.checked)}
          />
          <Button
            variant="light"
            color="red"
            loading={clearMutation.isPending}
            disabled={!clearExport && !clearSlug && !clearTrakt && !clearDiscover}
            onClick={() => clearMutation.mutate()}
            maw={280}
          >
            Clear selected caches
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
}

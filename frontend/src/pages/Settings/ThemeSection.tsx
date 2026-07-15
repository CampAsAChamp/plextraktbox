import {
  ActionIcon,
  Box,
  Button,
  FileButton,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  Textarea,
  Tooltip,
  UnstyledButton,
} from "@mantine/core";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { getSettings } from "../../api/settings";
import {
  deleteTheme,
  listThemes,
  updateActiveTheme,
  uploadTheme,
  type ThemeInfo,
} from "../../api/themes";
import { SettingsSectionTitle } from "../../components/SettingsSectionTitle";
import { PaletteIcon } from "../../components/icons/PaletteIcon";
import { TrashIcon } from "../../components/icons/TrashIcon";
import { showToast } from "../../toast";
import { BUILTIN_THEMES, getBuiltinTheme } from "../../themes/registry";
import { writeCachedThemeId } from "../../themes/themePreference";

function ThemeSwatch({
  theme,
  active,
  onSelect,
  onDelete,
}: {
  theme: ThemeInfo;
  active: boolean;
  onSelect: () => void;
  onDelete?: () => void;
}) {
  const builtin = getBuiltinTheme(theme.id);
  const swatches = builtin?.swatches ?? ["#282C34", "#3E4452", "#61AFEF"];

  return (
    <Box pos="relative">
      <UnstyledButton
        onClick={onSelect}
        aria-pressed={active}
        aria-label={`Use theme ${theme.name}`}
        style={{
          display: "block",
          width: "100%",
          borderRadius: "var(--mantine-radius-lg)",
          border: active
            ? "2px solid var(--mantine-primary-color-filled)"
            : "1px solid var(--mantine-color-dark-4)",
          padding: 12,
          background: "var(--mantine-color-dark-7)",
          textAlign: "left",
        }}
      >
        <Group gap={6} mb="xs" wrap="nowrap">
          {swatches.map((color) => (
            <Box
              key={color}
              w={22}
              h={22}
              style={{
                borderRadius: 999,
                background: color,
                border: "1px solid var(--mantine-color-dark-3)",
              }}
            />
          ))}
        </Group>
        <Text size="sm" fw={600}>
          {theme.name}
        </Text>
        <Text size="xs" c="dimmed">
          {theme.source === "builtin" ? "Built-in" : "Custom"} · {theme.id}
        </Text>
      </UnstyledButton>
      {theme.source === "custom" && onDelete ? (
        <Tooltip label="Delete custom theme">
          <ActionIcon
            variant="subtle"
            color="red"
            size="sm"
            pos="absolute"
            top={8}
            right={8}
            aria-label={`Delete theme ${theme.name}`}
            onClick={(event) => {
              event.stopPropagation();
              onDelete();
            }}
          >
            <TrashIcon size={14} />
          </ActionIcon>
        </Tooltip>
      ) : null}
    </Box>
  );
}

export function ThemeSection() {
  const queryClient = useQueryClient();
  const [pasteCss, setPasteCss] = useState("");
  const [pasteName, setPasteName] = useState("custom-theme.css");

  const themesQuery = useQuery({
    queryKey: ["themes"],
    queryFn: listThemes,
  });

  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  const activeId = settingsQuery.data?.ui_theme ?? "one-dark-pro";

  const activateMutation = useMutation({
    mutationFn: updateActiveTheme,
    onSuccess: async (result) => {
      writeCachedThemeId(result.theme_id);
      queryClient.setQueryData(["settings"], (prev: { ui_theme?: string } | undefined) =>
        prev ? { ...prev, ui_theme: result.theme_id } : prev,
      );
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
      showToast({ color: "green", message: `Theme set to ${result.theme_id}` });
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Failed to set theme";
      showToast({ color: "red", message });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ css, filename }: { css: string; filename?: string }) =>
      uploadTheme(css, filename),
    onSuccess: async (info) => {
      setPasteCss("");
      await queryClient.invalidateQueries({ queryKey: ["themes"] });
      showToast({ color: "green", message: `Uploaded ${info.name}` });
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Upload failed";
      showToast({ color: "red", message });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTheme,
    onSuccess: async (_void, themeId) => {
      await queryClient.invalidateQueries({ queryKey: ["themes"] });
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
      showToast({ color: "green", message: `Deleted ${themeId}` });
      if (themeId === activeId) {
        writeCachedThemeId("one-dark-pro");
      }
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Delete failed";
      showToast({ color: "red", message });
    },
  });

  const themes = themesQuery.data ?? BUILTIN_THEMES.map((t) => ({
    id: t.id,
    name: t.name,
    source: "builtin" as const,
  }));

  async function handleFile(file: File | null) {
    if (!file) return;
    const css = await file.text();
    uploadMutation.mutate({ css, filename: file.name });
  }

  return (
    <Paper
      id="settings-theme"
      withBorder
      p="md"
      data-settings-section="Theme"
      style={{ scrollMarginTop: 80 }}
    >
      <Stack gap="lg">
        <SettingsSectionTitle icon={<PaletteIcon size={18} />}>Theme</SettingsSectionTitle>
        <Text size="sm" c="dimmed">
          Choose a built-in palette or upload a custom CSS theme. Active theme is stored in
          settings and applied for this install. Optional host volume:{" "}
          <code>/data/themes</code>.
        </Text>

        <SimpleGrid cols={{ base: 1, xs: 2, md: 4 }} spacing="sm">
          {themes.map((theme) => (
            <ThemeSwatch
              key={theme.id}
              theme={theme}
              active={theme.id === activeId}
              onSelect={() => {
                if (theme.id !== activeId) {
                  activateMutation.mutate(theme.id);
                }
              }}
              onDelete={
                theme.source === "custom"
                  ? () => deleteMutation.mutate(theme.id)
                  : undefined
              }
            />
          ))}
        </SimpleGrid>

        <Group gap="sm">
          <Button
            variant="light"
            loading={themesQuery.isFetching}
            onClick={() => void themesQuery.refetch()}
          >
            Refresh themes
          </Button>
          <FileButton onChange={(file) => void handleFile(file)} accept=".css,text/css">
            {(props) => (
              <Button variant="light" loading={uploadMutation.isPending} {...props}>
                Upload CSS
              </Button>
            )}
          </FileButton>
        </Group>

        <Stack gap="xs">
          <Text fw={500}>Paste custom CSS</Text>
          <Text size="sm" c="dimmed">
            Include <code>/* @name: … */</code> and <code>/* @id: … */</code> headers. See{" "}
            <code>frontend/src/themes/README.md</code>.
          </Text>
          <Textarea
            minRows={6}
            autosize
            maxRows={14}
            value={pasteCss}
            onChange={(event) => setPasteCss(event.currentTarget.value)}
            placeholder={"/* @name: My Theme */\n/* @id: my-theme */\n:root[data-ptb-theme=\"my-theme\"] {\n  --mantine-color-dark-9: #111;\n}\n"}
            styles={{ input: { fontFamily: "var(--mantine-font-family-monospace)" } }}
          />
          <Group align="flex-end">
            <Button
              disabled={!pasteCss.trim()}
              loading={uploadMutation.isPending}
              onClick={() =>
                uploadMutation.mutate({ css: pasteCss, filename: pasteName || undefined })
              }
            >
              Save pasted theme
            </Button>
            <TextInput
              label="Filename hint"
              value={pasteName}
              onChange={(event) => setPasteName(event.currentTarget.value)}
              w={220}
            />
          </Group>
        </Stack>
      </Stack>
    </Paper>
  );
}

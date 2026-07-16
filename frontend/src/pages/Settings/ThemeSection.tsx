import {
  ActionIcon,
  Anchor,
  Box,
  Button,
  FileButton,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
  Tooltip,
  UnstyledButton,
} from "@mantine/core"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { getSettings } from "src/api/settings"
import { deleteTheme, listThemes, type ThemeInfo, updateActiveTheme, uploadTheme } from "src/api/themes"
import { PaletteIcon } from "src/components/icons/PaletteIcon"
import { SaveIcon } from "src/components/icons/SaveIcon"
import { SyncIcon } from "src/components/icons/SyncIcon"
import { TrashIcon } from "src/components/icons/TrashIcon"
import { UploadIcon } from "src/components/icons/UploadIcon"
import { SettingsSectionTitle } from "src/components/SettingsSectionTitle"
import exampleThemeCss from "src/themes/example-theme.css?raw"
import { BUILTIN_THEMES, DEFAULT_THEME_ID, getBuiltinTheme } from "src/themes/registry"
import { writeCachedThemeId } from "src/themes/themePreference"
import { iconForToastColor, showToast } from "src/toast"

/** Keep the refresh spinner visible on fast local refetches. */
const MIN_REFRESH_SPIN_MS = 500
const FALLBACK_SWATCHES = ["#282C34", "#3E4452", "#61AFEF"]

function ThemeSwatch({
  theme,
  active,
  onSelect,
  onDelete,
}: {
  theme: ThemeInfo
  active: boolean
  onSelect: () => void
  onDelete?: () => void
}) {
  const builtin = getBuiltinTheme(theme.id)
  const swatches = builtin?.swatches ?? theme.swatches ?? FALLBACK_SWATCHES

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
          border: active ? "2px solid var(--mantine-primary-color-filled)" : "1px solid var(--mantine-color-dark-4)",
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
              event.stopPropagation()
              onDelete()
            }}
          >
            <TrashIcon size={14} />
          </ActionIcon>
        </Tooltip>
      ) : null}
    </Box>
  )
}

export function ThemeSection() {
  const queryClient = useQueryClient()
  const [pasteCss, setPasteCss] = useState("")
  /** Basename fallback for save when CSS lacks `@id` (set by Import file only). */
  const [importFilename, setImportFilename] = useState<string | undefined>(undefined)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const themesQuery = useQuery({
    queryKey: ["themes"],
    queryFn: listThemes,
  })

  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  })

  const activeId = settingsQuery.data?.ui_theme ?? DEFAULT_THEME_ID

  const activateMutation = useMutation({
    mutationFn: updateActiveTheme,
    onSuccess: async (result) => {
      writeCachedThemeId(result.theme_id)
      queryClient.setQueryData(["settings"], (prev: { ui_theme?: string } | undefined) =>
        prev ? { ...prev, ui_theme: result.theme_id } : prev,
      )
      await queryClient.invalidateQueries({ queryKey: ["settings"] })
      showToast({ color: "green", message: `Theme set to ${result.theme_id}` })
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Failed to set theme"
      showToast({ color: "red", message })
    },
  })

  const uploadMutation = useMutation({
    mutationFn: ({ css, filename }: { css: string; filename?: string }) => uploadTheme(css, filename),
    onSuccess: async (info) => {
      setPasteCss("")
      setImportFilename(undefined)
      queryClient.setQueryData<ThemeInfo[]>(["themes"], (prev) => {
        const current = prev ?? []
        const without = current.filter((t) => t.id !== info.id)
        return [...without, info]
      })
      await queryClient.invalidateQueries({ queryKey: ["themes"] })
      try {
        const active = await updateActiveTheme(info.id)
        writeCachedThemeId(active.theme_id)
        queryClient.setQueryData(["settings"], (prev: { ui_theme?: string } | undefined) =>
          prev ? { ...prev, ui_theme: active.theme_id } : prev,
        )
        await queryClient.invalidateQueries({ queryKey: ["settings"] })
        showToast({ color: "green", message: `Saved and applied ${info.name}` })
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : "Theme saved but failed to activate"
        showToast({ color: "orange", message })
      }
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Failed to save theme"
      showToast({ color: "red", message })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTheme,
    onSuccess: async (_void, themeId) => {
      await queryClient.invalidateQueries({ queryKey: ["themes"] })
      await queryClient.invalidateQueries({ queryKey: ["settings"] })
      showToast({ color: "green", message: `Deleted ${themeId}` })
      if (themeId === activeId) {
        writeCachedThemeId(DEFAULT_THEME_ID)
      }
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Delete failed"
      showToast({ color: "red", message })
    },
  })

  const themes =
    themesQuery.data ??
    BUILTIN_THEMES.map((t) => ({
      id: t.id,
      name: t.name,
      source: "builtin" as const,
      swatches: t.swatches,
    }))

  async function handleImportFile(file: File | null) {
    if (!file) return
    const css = await file.text()
    setPasteCss(css)
    setImportFilename(file.name)
  }

  async function handleRefreshThemes() {
    if (isRefreshing) return
    setIsRefreshing(true)
    const started = performance.now()
    try {
      const result = await themesQuery.refetch()
      if (result.error) {
        const message = result.error instanceof Error ? result.error.message : "Failed to refresh themes"
        showToast({ color: "red", message })
        return
      }
      showToast({ color: "green", message: "Themes refreshed" })
    } finally {
      const remaining = Math.max(0, MIN_REFRESH_SPIN_MS - (performance.now() - started))
      if (remaining > 0) {
        await new Promise<void>((resolve) => {
          window.setTimeout(resolve, remaining)
        })
      }
      setIsRefreshing(false)
    }
  }

  return (
    <Paper id="settings-theme" withBorder p="md" data-settings-section="Theme" style={{ scrollMarginTop: 80 }}>
      <Stack gap="lg">
        <SettingsSectionTitle icon={<PaletteIcon size={18} />}>Theme</SettingsSectionTitle>
        <Text size="sm" c="dimmed">
          Choose a built-in palette or save a custom CSS theme. Active theme is stored in settings and applied for this install. Optional
          host volume: <code>/data/themes</code>.
        </Text>

        <SimpleGrid cols={{ base: 1, xs: 2, md: 4 }} spacing="sm">
          {themes.map((theme) => (
            <ThemeSwatch
              key={theme.id}
              theme={theme}
              active={theme.id === activeId}
              onSelect={() => {
                if (theme.id !== activeId) {
                  activateMutation.mutate(theme.id)
                }
              }}
              onDelete={theme.source === "custom" ? () => deleteMutation.mutate(theme.id) : undefined}
            />
          ))}
        </SimpleGrid>

        <Group gap="sm">
          <Button variant="light" loading={isRefreshing} onClick={() => void handleRefreshThemes()} leftSection={<SyncIcon />}>
            Refresh themes
          </Button>
        </Group>

        <Stack gap="xs">
          <Text fw={500}>Test toasts</Text>
          <Text size="sm" c="dimmed">
            Preview success, info, warning, and error notifications with the active theme.
          </Text>
          <Group gap="sm">
            <Button
              variant="light"
              color="green"
              leftSection={iconForToastColor("green")}
              onClick={() => showToast({ color: "green", title: "Success", message: "Theme preview: success toast" })}
            >
              Success
            </Button>
            <Button
              variant="light"
              color="blue"
              leftSection={iconForToastColor("blue")}
              onClick={() => showToast({ color: "blue", title: "Info", message: "Theme preview: info toast" })}
            >
              Info
            </Button>
            <Button
              variant="light"
              color="orange"
              leftSection={iconForToastColor("orange")}
              onClick={() => showToast({ color: "orange", title: "Warning", message: "Theme preview: warning toast" })}
            >
              Warning
            </Button>
            <Button
              variant="light"
              color="red"
              leftSection={iconForToastColor("red")}
              onClick={() => showToast({ color: "red", title: "Error", message: "Theme preview: error toast" })}
            >
              Error
            </Button>
          </Group>
        </Stack>

        <Stack gap="xs">
          <Text fw={500}>Custom CSS</Text>
          <Text size="sm" c="dimmed">
            Include <code>/* @name: … */</code> and <code>/* @id: … */</code> headers — the id becomes <code>{`{id}.css`}</code> under{" "}
            <code>/data/themes</code>. Load the starter to tweak colors, import a file into the editor, or see{" "}
            <Anchor
              href="https://github.com/CampAsAChamp/plextraktbox/blob/main/frontend/src/themes/README.md"
              target="_blank"
              rel="noopener noreferrer"
              size="sm"
            >
              <code>frontend/src/themes/README.md</code>
            </Anchor>
            .
          </Text>
          <Textarea
            minRows={8}
            autosize
            maxRows={18}
            value={pasteCss}
            onChange={(event) => {
              setPasteCss(event.currentTarget.value)
              setImportFilename(undefined)
            }}
            placeholder={exampleThemeCss}
            styles={{ input: { fontFamily: "var(--mantine-font-family-monospace)" } }}
          />
          <Group>
            <Button
              variant="light"
              onClick={() => {
                setPasteCss(exampleThemeCss)
                setImportFilename(undefined)
              }}
            >
              Load example
            </Button>
            <FileButton onChange={(file) => void handleImportFile(file)} accept=".css,text/css">
              {(props) => (
                <Button variant="light" leftSection={<UploadIcon />} {...props}>
                  Import file
                </Button>
              )}
            </FileButton>
            <Button
              disabled={!pasteCss.trim()}
              loading={uploadMutation.isPending}
              leftSection={<SaveIcon />}
              onClick={() => uploadMutation.mutate({ css: pasteCss, filename: importFilename })}
            >
              Save theme
            </Button>
          </Group>
        </Stack>
      </Stack>
    </Paper>
  )
}

import { Group, SimpleGrid, Skeleton, Stack } from "@mantine/core"

export function ListPageSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <Stack gap="sm" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, index) => (
        <Skeleton key={index} height={48} radius="md" />
      ))}
    </Stack>
  )
}

export function GlanceStripSkeleton() {
  return <Skeleton height={88} radius="md" aria-busy="true" aria-label="Loading overview" />
}

export function FiltersSkeleton() {
  return (
    <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="sm" aria-busy="true" aria-label="Loading filters">
      <Skeleton height={54} radius="md" />
      <Skeleton height={54} radius="md" />
      <Skeleton height={54} radius="md" />
    </SimpleGrid>
  )
}

export function RunDetailSkeleton() {
  return (
    <Stack gap="md" aria-busy="true" aria-label="Loading run">
      <Skeleton height={28} width={160} radius="md" />
      <SimpleGrid cols={{ base: 2, sm: 4 }}>
        {Array.from({ length: 4 }, (_, index) => (
          <Skeleton key={index} height={64} radius="md" />
        ))}
      </SimpleGrid>
      <Skeleton height={280} radius="md" />
    </Stack>
  )
}

export function JobFormSkeleton() {
  return (
    <Stack gap="md" aria-busy="true" aria-label="Loading job">
      <Skeleton height={16} width={72} radius="sm" />
      <Skeleton height={36} radius="xl" />
      <Skeleton height={16} width={96} radius="sm" />
      <Skeleton height={72} radius="md" />
      <Skeleton height={16} width={88} radius="sm" />
      <Skeleton height={36} radius="xl" />
      <Skeleton height={100} radius="md" />
      <Group gap="sm">
        <Skeleton height={36} width={100} radius="xl" />
        <Skeleton height={36} width={80} radius="xl" />
      </Group>
    </Stack>
  )
}

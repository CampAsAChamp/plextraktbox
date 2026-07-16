import { Button, Group, Loader, Stack, Text, Title } from "@mantine/core"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link, useNavigate, useParams } from "react-router-dom"

import { ApiError } from "src/api/client"
import { getJob, updateJob } from "src/api/jobApi"
import type { JobInput } from "src/api/jobs"
import { JobForm } from "src/components/JobForm/JobForm"
import { showToast } from "src/toast"

export function JobEditPage() {
  const { jobId } = useParams()
  const id = Number(jobId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const jobQuery = useQuery({
    queryKey: ["jobs", id],
    queryFn: () => getJob(id),
    enabled: Number.isFinite(id),
  })

  const updateMutation = useMutation({
    mutationFn: (input: JobInput) => updateJob(id, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["jobs"] })
      showToast({ color: "green", message: "Job updated" })
      navigate("/jobs", { replace: true })
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Update failed"
      showToast({ color: "red", message })
    },
  })

  if (!Number.isFinite(id)) {
    return <Text c="red">Invalid job id.</Text>
  }

  if (jobQuery.isLoading) {
    return (
      <Group>
        <Loader size="sm" />
        <Text>Loading job…</Text>
      </Group>
    )
  }

  if (jobQuery.isError || !jobQuery.data) {
    return <Text c="red">Job not found.</Text>
  }

  return (
    <Stack gap="md">
      <Stack gap="xs">
        <Button component={Link} to="/jobs" variant="subtle" w="fit-content">
          Back to jobs
        </Button>
        <Title order={3}>Edit job</Title>
      </Stack>
      <JobForm
        initial={jobQuery.data}
        loading={updateMutation.isPending}
        onSubmit={(input) => updateMutation.mutate(input)}
        onCancel={() => navigate("/jobs")}
      />
    </Stack>
  )
}

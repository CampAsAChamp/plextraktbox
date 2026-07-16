import { Button, Group, Stack, Title } from "@mantine/core";
import { showToast } from "src/toast";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import type { JobInput } from "src/api/jobs";
import { ApiError } from "src/api/client";
import { createJob } from "src/api/jobApi";
import { JobForm } from "src/components/JobForm/JobForm";

export function JobCreatePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (input: JobInput) => createJob(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["jobs"] });
      showToast({ color: "green", message: "Job created" });
      navigate("/jobs", { replace: true });
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Create failed";
      showToast({ color: "red", message });
    },
  });

  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="wrap" gap="sm">
        <Title order={3}>New sync job</Title>
        <Button component={Link} to="/jobs" variant="subtle">
          Back to jobs
        </Button>
      </Group>
      <JobForm
        loading={createMutation.isPending}
        onSubmit={(input) => createMutation.mutate(input)}
        onCancel={() => navigate("/jobs")}
      />
    </Stack>
  );
}

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useLocation, useNavigate } from "react-router-dom"

import { ApiError } from "src/api/client"
import { runJob } from "src/api/jobApi"
import type { Job } from "src/api/jobs"
import { showToast } from "src/toast"

export type RunMode = "run" | "dry-run"

export function useRunJob() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const location = useLocation()

  const runMutation = useMutation({
    mutationFn: ({ job, mode }: { job: Job; mode: RunMode }) => runJob(job.id, mode === "dry-run" ? true : undefined),
    onSuccess: (run) => {
      void queryClient.invalidateQueries({ queryKey: ["jobs"] })
      void queryClient.invalidateQueries({ queryKey: ["runs"] })
      showToast({
        color: "blue",
        message: `Run #${run.id} started`,
      })
      navigate(`/runs/${run.id}`, { state: { from: `${location.pathname}${location.search}` } })
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Run failed"
      showToast({ color: "red", message })
    },
  })

  function isRunning(job: Job, mode: RunMode): boolean {
    return runMutation.isPending && runMutation.variables?.job.id === job.id && runMutation.variables.mode === mode
  }

  function onRun(job: Job, mode: RunMode) {
    runMutation.mutate({ job, mode })
  }

  return { runMutation, isRunning, onRun }
}

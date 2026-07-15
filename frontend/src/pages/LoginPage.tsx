import {
  Button,
  Center,
  Loader,
  Paper,
  PasswordInput,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { api } from "../api/client";
import type { LoginInput, User } from "../api/auth";
import { ApiError } from "../api/client";

const loginSchema = z.object({
  username: z.string().min(1, "Username or email is required"),
  password: z.string().min(1, "Password is required"),
});

export function LoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const login = useMutation({
    mutationFn: (body: LoginInput) => api.post<User>("/auth/login", body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      navigate("/", { replace: true });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof ApiError ? String(error.message) : "Login failed";
      notifications.show({ color: "red", message });
    },
  });

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const parsed = loginSchema.safeParse({ username, password });
    if (!parsed.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        const key = issue.path[0];
        if (typeof key === "string") fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }
    setErrors({});
    login.mutate(parsed.data);
  }

  return (
    <Center mih="60vh" px="md">
      <Paper withBorder p="xl" maw={420} w="100%">
        <Stack gap="md">
          <Title order={3}>Sign in</Title>
          <Text c="dimmed" size="sm">
            Log in to manage Plex, Letterboxd, and Trakt sync jobs.
          </Text>
          <form onSubmit={handleSubmit}>
            <Stack gap="sm">
              <TextInput
                label="Username or email"
                value={username}
                onChange={(event) => setUsername(event.currentTarget.value)}
                error={errors.username}
                autoComplete="username"
              />
              <PasswordInput
                label="Password"
                value={password}
                onChange={(event) => setPassword(event.currentTarget.value)}
                error={errors.password}
                autoComplete="current-password"
              />
              <Button type="submit" loading={login.isPending}>
                Sign in
              </Button>
            </Stack>
          </form>
        </Stack>
      </Paper>
    </Center>
  );
}

export function LoginLoading() {
  return (
    <Center mih="60vh">
      <Loader />
    </Center>
  );
}

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
import { showToast } from "../toast";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { api } from "../api/client";
import type { SetupUserInput, User } from "../api/auth";
import { ApiError } from "../api/client";

const setupSchema = z
  .object({
    username: z.string().min(2, "Username must be at least 2 characters"),
    email: z.string().email("Enter a valid email"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export function SetupWizardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const setup = useMutation({
    mutationFn: (body: SetupUserInput) => api.post<User>("/setup/user", body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["setup", "status"] });
      navigate("/login", { replace: true });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof ApiError ? String(error.message) : "Setup failed";
      showToast({ color: "red", message });
    },
  });

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const parsed = setupSchema.safeParse({
      username,
      email,
      password,
      confirmPassword,
    });
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
    setup.mutate({
      username: parsed.data.username,
      email: parsed.data.email,
      password: parsed.data.password,
    });
  }

  return (
    <Center mih="60vh" px="md">
      <Paper withBorder p="xl" maw={420} w="100%">
        <Stack gap="md">
          <Title order={3}>Welcome to plextraktbox</Title>
          <Text c="dimmed" size="sm">
            Create the local admin account. This app supports a single user.
          </Text>
          <form onSubmit={handleSubmit}>
            <Stack gap="sm">
              <TextInput
                label="Username"
                value={username}
                onChange={(event) => setUsername(event.currentTarget.value)}
                error={errors.username}
                autoComplete="username"
              />
              <TextInput
                label="Email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.currentTarget.value)}
                error={errors.email}
                autoComplete="email"
              />
              <PasswordInput
                label="Password"
                value={password}
                onChange={(event) => setPassword(event.currentTarget.value)}
                error={errors.password}
                autoComplete="new-password"
              />
              <PasswordInput
                label="Confirm password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.currentTarget.value)}
                error={errors.confirmPassword}
                autoComplete="new-password"
              />
              <Button type="submit" loading={setup.isPending}>
                Create account
              </Button>
            </Stack>
          </form>
        </Stack>
      </Paper>
    </Center>
  );
}

export function SetupLoading() {
  return (
    <Center mih="60vh">
      <Loader />
    </Center>
  );
}

import {
  Anchor,
  Avatar,
  Button,
  Group,
  Paper,
  PasswordInput,
  Stack,
  Text,
} from "@mantine/core";
import { showToast } from "../../toast";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { z } from "zod";
import type { User } from "../../api/auth";
import { ApiError } from "../../api/client";
import { changePassword } from "../../api/settings";
import { SettingsSectionTitle } from "../../components/SettingsSectionTitle";
import { UserIcon } from "../../components/icons/UserIcon";

const passwordSchema = z
  .object({
    currentPassword: z.string().min(1, "Current password is required"),
    newPassword: z.string().min(8, "New password must be at least 8 characters"),
    confirmPassword: z.string().min(1, "Confirm your new password"),
  })
  .refine((value) => value.newPassword === value.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  })
  .refine((value) => value.currentPassword !== value.newPassword, {
    message: "New password must differ from the current password",
    path: ["newPassword"],
  });

interface AccountSectionProps {
  user: User;
}

export function AccountSection({ user }: AccountSectionProps) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const mutation = useMutation({
    mutationFn: () => changePassword(currentPassword, newPassword),
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setErrors({});
      showToast({ color: "green", message: "Password updated" });
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Password change failed";
      showToast({ color: "red", message });
    },
  });

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const parsed = passwordSchema.safeParse({
      currentPassword,
      newPassword,
      confirmPassword,
    });
    if (!parsed.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        const key = String(issue.path[0] ?? "form");
        fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }
    setErrors({});
    mutation.mutate();
  }

  return (
    <Paper
      id="settings-account"
      withBorder
      p="md"
      data-settings-section="Account"
      style={{ scrollMarginTop: 80 }}
    >
      <Stack gap="md">
        <SettingsSectionTitle icon={<UserIcon size={18} />}>Account</SettingsSectionTitle>
        <Group gap="md" align="flex-start" wrap="nowrap">
          <Avatar src={user.avatar_url} alt="" size={64} radius="xl" />
          <Stack gap={4}>
            <Text fw={600}>{user.username}</Text>
            <Text size="sm" c="dimmed">
              {user.email}
            </Text>
            <Anchor
              href="https://gravatar.com"
              target="_blank"
              rel="noopener noreferrer"
              size="sm"
            >
              Manage avatar at Gravatar
            </Anchor>
          </Stack>
        </Group>

        <form onSubmit={handleSubmit}>
          <Stack gap="sm">
            <Text fw={500}>Change password</Text>
            <PasswordInput
              label="Current password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.currentTarget.value)}
              error={errors.currentPassword}
              required
            />
            <PasswordInput
              label="New password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.currentTarget.value)}
              error={errors.newPassword}
              required
            />
            <PasswordInput
              label="Confirm new password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.currentTarget.value)}
              error={errors.confirmPassword}
              required
            />
            <Group>
              <Button type="submit" loading={mutation.isPending}>
                Update password
              </Button>
            </Group>
          </Stack>
        </form>
      </Stack>
    </Paper>
  );
}

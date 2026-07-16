import { isValidCron } from "cron-validator"

export function isValidCronExpression(expression: string): boolean {
  const trimmed = expression.trim()
  if (!trimmed) return false
  return isValidCron(trimmed, { seconds: false })
}

export const CRON_INVALID_MESSAGE = "Invalid cron expression (expected 5 fields: minute hour day month weekday)"

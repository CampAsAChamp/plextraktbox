import { createLogger, type Logger } from "vite"

const RESET = "\x1b[0m"
const DIM = "\x1b[2m"

const LEVEL_COLOR: Record<"info" | "warn" | "error", string> = {
  info: "\x1b[36m",
  warn: "\x1b[33m",
  error: "\x1b[31m",
}

function colorize(level: keyof typeof LEVEL_COLOR, message: string): string {
  return `${LEVEL_COLOR[level]}${message}${RESET}`
}

function wrapLevel(logger: Logger, level: keyof typeof LEVEL_COLOR, log: Logger["info"]): Logger["info"] {
  return (message, options) => {
    log.call(logger, colorize(level, message), options)
  }
}

/** Vite dev-server logger with ANSI level colors (works in docker compose output). */
export function createColoredViteLogger(): Logger {
  const logger = createLogger(undefined, { prefix: "[vite]" })

  logger.info = wrapLevel(logger, "info", logger.info.bind(logger))
  logger.warn = wrapLevel(logger, "warn", logger.warn.bind(logger))
  logger.error = wrapLevel(logger, "error", logger.error.bind(logger))

  const baseClearScreen = logger.clearScreen.bind(logger)
  logger.clearScreen = (type) => {
    baseClearScreen(type)
    if (type === "error") {
      process.stderr.write(`${DIM}---${RESET}\n`)
    }
  }

  return logger
}

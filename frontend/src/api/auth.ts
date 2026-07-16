import type { components } from "src/api/generated/schema"

type Schemas = components["schemas"]

export type User = Schemas["UserResponse"]
export type SetupStatus = Schemas["SetupStatusResponse"]
export type SetupUserInput = Schemas["SetupUserRequest"]
export type LoginInput = Schemas["LoginRequest"]

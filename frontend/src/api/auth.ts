export interface User {
  id: number
  username: string
  email: string
  avatar_url: string
}

export interface SetupStatus {
  needs_setup: boolean
}

export interface SetupUserInput {
  username: string
  email: string
  password: string
}

export interface LoginInput {
  username: string
  password: string
}

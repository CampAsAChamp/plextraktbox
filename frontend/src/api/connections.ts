import type { components } from "src/api/generated/schema"

type Schemas = components["schemas"]

export type Service = Schemas["Service"]
export type ConnectionStatus = Schemas["ConnectionStatus"]
export type ConnectionSummary = Schemas["ConnectionSummary"]
/** UI-facing alias for ConnectionsStatusResponse. */
export type ConnectionsStatus = Schemas["ConnectionsStatusResponse"]
export type ConnectionTestResult = Schemas["ConnectionTestResponse"]
export type PlexPinStart = Schemas["PlexPinStartResponse"]
export type PlexPinPollInput = Schemas["PlexPinPollRequest"]
export type PlexPinPollResult = Schemas["PlexPinPollResponse"]
export type LetterboxdConnectionInput = Schemas["LetterboxdConnectionRequest"]
export type TmdbConnectionInput = Schemas["TmdbConnectionRequest"]
export type TraktDeviceStart = Schemas["TraktDeviceStartResponse"]
export type TraktDevicePollInput = Schemas["TraktDevicePollRequest"]
export type TraktDevicePollResult = Schemas["TraktDevicePollResponse"]
export type PlexLibraryInfo = Schemas["PlexLibraryInfo"]
export type PlexLibrariesResponse = Schemas["PlexLibrariesResponse"]

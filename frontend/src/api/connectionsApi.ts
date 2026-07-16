import { api } from "src/api/client"
import type {
  ConnectionsStatus,
  ConnectionSummary,
  ConnectionTestResult,
  LetterboxdConnectionInput,
  PlexLibrariesResponse,
  PlexPinPollInput,
  PlexPinPollResult,
  PlexPinStart,
  Service,
  TmdbConnectionInput,
  TraktDevicePollInput,
  TraktDevicePollResult,
  TraktDeviceStart,
} from "src/api/connections"

export function getConnectionsStatus() {
  return api.get<ConnectionsStatus>("/connections/status")
}

export function clearConnection(service: Service) {
  return api.del<void>(`/connections/${service}`)
}

export function clearAllConnections() {
  return api.del<void>("/connections")
}

export function getPlexLibraries() {
  return api.get<PlexLibrariesResponse>("/connections/plex/libraries")
}

export function updatePlexLibraries(libraryIds: string[]) {
  return api.put<ConnectionSummary>("/connections/plex/libraries", { library_ids: libraryIds })
}

export function startPlexPin() {
  return api.post<PlexPinStart>("/connections/plex/pin/start")
}

export function pollPlexPin(body: PlexPinPollInput) {
  return api.post<PlexPinPollResult>("/connections/plex/pin/poll", body)
}

export function testPlexConnection() {
  return api.post<ConnectionTestResult>("/connections/plex/test", {})
}

export function startTraktDevice() {
  return api.post<TraktDeviceStart>("/connections/trakt/device/start")
}

export function pollTraktDevice(body: TraktDevicePollInput) {
  return api.post<TraktDevicePollResult>("/connections/trakt/device/poll", body)
}

export function testTraktConnection() {
  return api.post<ConnectionTestResult>("/connections/trakt/test", {})
}

export function saveLetterboxdConnection(body: LetterboxdConnectionInput) {
  return api.post<ConnectionSummary>("/connections/letterboxd", body)
}

export function testLetterboxdConnection(body?: LetterboxdConnectionInput) {
  return api.post<ConnectionTestResult>("/connections/letterboxd/test", body ?? {})
}

export function saveTmdbConnection(body: TmdbConnectionInput) {
  return api.post<ConnectionSummary>("/connections/tmdb", body)
}

export function testTmdbConnection(body?: TmdbConnectionInput) {
  return api.post<ConnectionTestResult>("/connections/tmdb/test", body ?? {})
}

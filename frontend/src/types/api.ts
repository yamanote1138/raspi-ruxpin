/**
 * API response types
 */

export interface HealthResponse {
  status: string
  version: string
}

export interface SystemStatus {
  version: string
  environment: string
  platform: string
  bear: {
    eyes: string
    mouth: string
    is_busy: boolean
    volume: number
  }
  phrases_count: number
}

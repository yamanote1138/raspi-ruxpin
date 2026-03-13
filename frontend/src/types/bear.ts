/**
 * Bear state and position types
 */

export enum State {
  OPEN = 'open',
  CLOSED = 'closed',
  UNKNOWN = 'unknown',
}

export enum SyncMode {
  AMPLITUDE = 'amplitude',
  PHONEME = 'phoneme',
  REALTIME = 'realtime',
}

export enum MouthCode {
  C = 'C',
  T = 'T',
  S = 'S',
  N = 'N',
  M = 'M',
  L = 'L',
  W = 'W',
}

export interface BearState {
  eyes: State
  mouth: State
  eyes_position: number // 0-100
  mouth_position: number // 0-100
  is_busy: boolean
  volume: number
  blink_enabled: boolean
  character: string // 'teddy' or 'grubby'
  sync_mode: SyncMode
  mouth_code: MouthCode
  arduino_connected: boolean
  arduino_port: string
  arduino_baud_rate: number
  arduino_connection_type: string // 'serial' or 'mock'
  status_text: string
  servo_type: string // 'hbridge' or 'standard'
  tts_engine: string // 'espeak' or 'piper'
  tts_voice: string
  environment: string // 'development' or 'production'
  platform: string // 'Darwin' or 'Linux'
  sound_count: number
  phoneme_available: boolean
}

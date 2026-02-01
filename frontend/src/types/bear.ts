/**
 * Bear state and position types
 */

export enum State {
  OPEN = 'open',
  CLOSED = 'closed',
  UNKNOWN = 'unknown',
}

export enum Mode {
  CONTROL = 'control',
  CONFIG = 'config',
}

export interface BearPosition {
  eyes: State
  mouth: State
}

export interface BearState extends BearPosition {
  eyes_position: number // 0-100
  mouth_position: number // 0-100
  is_busy: boolean
  volume: number
  blink_enabled: boolean
}

export interface CharacterInfo {
  name: string
  image: string
}

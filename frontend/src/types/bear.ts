/**
 * Bear state and position types
 */

export enum State {
  OPEN = 'open',
  CLOSED = 'closed',
  UNKNOWN = 'unknown',
}

export enum Mode {
  PUPPET = 'puppet',
  SPEAK = 'speak',
  CONFIG = 'config',
}

export interface BearPosition {
  eyes: State
  mouth: State
}

export interface BearState extends BearPosition {
  is_busy: boolean
  volume: number
  blink_enabled: boolean
}

export interface CharacterInfo {
  name: string
  image: string
}

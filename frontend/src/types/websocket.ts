/**
 * WebSocket message types
 */

import type { State } from './bear'

export enum MessageType {
  UPDATE_BEAR = 'update_bear',
  SPEAK = 'speak',
  PLAY = 'play',
  SET_VOLUME = 'set_volume',
  FETCH_PHRASES = 'fetch_phrases',
  SET_BLINK_ENABLED = 'set_blink_enabled',
  SET_CHARACTER = 'set_character',
  SET_SYNC_MODE = 'set_sync_mode',
  ANALYZE_AUDIO = 'analyze_audio',
  BEAR_STATE = 'bear_state',
  PHRASES = 'phrases',
  ERROR = 'error',
  SUCCESS = 'success',
}

// Incoming messages
export interface BearStateMessage {
  type: MessageType.BEAR_STATE
  data: {
    eyes: State
    mouth: State
    eyes_position: number
    mouth_position: number
    is_busy: boolean
    volume: number
    blink_enabled: boolean
    character: string
    sync_mode: string
    mouth_code: string
    arduino_connected: boolean
    arduino_port: string
    arduino_baud_rate: number
    arduino_connection_type: string
    status_text: string
  }
}

export interface PhrasesMessage {
  type: MessageType.PHRASES
  data: Phrases
}

export interface ErrorMessage {
  type: MessageType.ERROR
  message: string
}

export interface SuccessMessage {
  type: MessageType.SUCCESS
  message: string
}

export type WebSocketMessage =
  | BearStateMessage
  | PhrasesMessage
  | ErrorMessage
  | SuccessMessage

export type Phrases = Record<string, string>

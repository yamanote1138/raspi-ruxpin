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
  SET_LOG_LEVEL = 'set_log_level',
  GET_GPIO_STATUS = 'get_gpio_status',
  BEAR_STATE = 'bear_state',
  PHRASES = 'phrases',
  GPIO_STATUS = 'gpio_status',
  ERROR = 'error',
  SUCCESS = 'success',
  LOG = 'log',
}

// Outgoing messages
export interface UpdateBearMessage {
  type: MessageType.UPDATE_BEAR
  eyes?: State
  mouth?: State
}

export interface SpeakMessage {
  type: MessageType.SPEAK
  text: string
}

export interface PlayMessage {
  type: MessageType.PLAY
  sound: string
}

export interface SetVolumeMessage {
  type: MessageType.SET_VOLUME
  level: number
}

export interface FetchPhrasesMessage {
  type: MessageType.FETCH_PHRASES
}

export interface SetBlinkEnabledMessage {
  type: MessageType.SET_BLINK_ENABLED
  enabled: boolean
}

export interface SetLogLevelMessage {
  type: MessageType.SET_LOG_LEVEL
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
}

export interface GetGPIOStatusMessage {
  type: MessageType.GET_GPIO_STATUS
}

// Incoming messages
export interface LogMessage {
  timestamp: number
  level: string
  logger: string
  message: string
  module: string
  function: string
  line: number
  exception?: string
}
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

export interface LogMessageResponse {
  type: MessageType.LOG
  data: LogMessage
}

export interface GPIOStatusMessage {
  type: MessageType.GPIO_STATUS
  data: {
    pins: Record<number, boolean>
  }
}

export type WebSocketMessage =
  | BearStateMessage
  | PhrasesMessage
  | GPIOStatusMessage
  | ErrorMessage
  | SuccessMessage
  | LogMessageResponse

export type Phrases = Record<string, string>

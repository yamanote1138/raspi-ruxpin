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
  BEAR_STATE = 'bear_state',
  PHRASES = 'phrases',
  ERROR = 'error',
  SUCCESS = 'success',
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

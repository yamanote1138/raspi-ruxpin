/**
 * Bear state management composable
 */

import { ref, computed, onMounted, type Ref, type ComputedRef } from 'vue'
import { useWebSocket } from './useWebSocket'
import { State, Mode, type BearState } from '@/types/bear'
import type {
  MessageType,
  Phrases,
  WebSocketMessage,
  BearStateMessage,
  PhrasesMessage,
  ErrorMessage,
} from '@/types/websocket'

export interface BearComposable {
  // State
  bearState: Ref<BearState>
  phrases: Ref<Phrases>
  currentMode: Ref<Mode>
  isConnected: Ref<boolean>
  errorMessage: Ref<string | null>

  // Computed
  isBusy: ComputedRef<boolean>
  bearImage: ComputedRef<string>

  // Actions
  updateBear: (eyes?: State, mouth?: State) => void
  speak: (text: string) => Promise<void>
  play: (sound: string) => Promise<void>
  setVolume: (level: number) => void
  fetchPhrases: () => void
  setMode: (mode: Mode) => void
}

/**
 * Composable for managing bear state and WebSocket communication
 */
export function useBear(): BearComposable {
  // WebSocket connection
  const ws = useWebSocket()

  // Bear state
  const bearState = ref<BearState>({
    eyes: State.UNKNOWN,
    mouth: State.UNKNOWN,
    is_busy: false,
    volume: 100,
    blink_enabled: true,
  })

  // UI state
  const phrases = ref<Phrases>({})
  const currentMode = ref<Mode>(Mode.PUPPET)
  const errorMessage = ref<string | null>(null)

  // Computed properties
  const isBusy = computed(() => bearState.value.is_busy)

  const bearImage = computed(() => {
    const eyes = bearState.value.eyes === State.OPEN ? 'eo' : 'ec'
    const mouth = bearState.value.mouth === State.OPEN ? 'mo' : 'mc'
    return `/img/teddy_${eyes}${mouth}.png`
  })

  /**
   * Update bear positions
   */
  const updateBear = (eyes?: State, mouth?: State) => {
    if (isBusy.value) {
      console.warn('Bear is busy')
      return
    }

    const message: any = {
      type: 'update_bear',
    }

    if (eyes !== undefined) {
      message.eyes = eyes
    }

    if (mouth !== undefined) {
      message.mouth = mouth
    }

    ws.send(message)
  }

  /**
   * Speak text with TTS
   */
  const speak = async (text: string): Promise<void> => {
    if (isBusy.value) {
      throw new Error('Bear is busy')
    }

    if (!text.trim()) {
      throw new Error('Text cannot be empty')
    }

    const message = {
      type: 'speak',
      text: text.trim(),
    }

    ws.send(message)
  }

  /**
   * Play audio file
   */
  const play = async (sound: string): Promise<void> => {
    if (isBusy.value) {
      throw new Error('Bear is busy')
    }

    const message = {
      type: 'play',
      sound,
    }

    ws.send(message)
  }

  /**
   * Set volume level
   */
  const setVolume = (level: number) => {
    if (level < 0 || level > 100) {
      throw new Error('Volume must be between 0 and 100')
    }

    const message = {
      type: 'set_volume',
      level,
    }

    ws.send(message)
  }

  /**
   * Fetch available phrases
   */
  const fetchPhrases = () => {
    const message = {
      type: 'fetch_phrases',
    }

    ws.send(message)
  }

  /**
   * Set UI mode
   */
  const setMode = (mode: Mode) => {
    currentMode.value = mode
  }

  /**
   * Enable or disable eye blinking
   */
  const setBlinkEnabled = (enabled: boolean) => {
    const message = {
      type: 'set_blink_enabled',
      enabled,
    }

    ws.send(message)
  }

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = (data: WebSocketMessage) => {
    console.log('Received message:', data)

    switch (data.type) {
      case 'bear_state':
        const stateMsg = data as BearStateMessage
        bearState.value = {
          eyes: stateMsg.data.eyes,
          mouth: stateMsg.data.mouth,
          is_busy: stateMsg.data.is_busy,
          volume: stateMsg.data.volume,
          blink_enabled: stateMsg.data.blink_enabled ?? true,
        }
        break

      case 'phrases':
        const phrasesMsg = data as PhrasesMessage
        phrases.value = phrasesMsg.data
        break

      case 'error':
        const errorMsg = data as ErrorMessage
        errorMessage.value = errorMsg.message
        console.error('Bear error:', errorMsg.message)
        setTimeout(() => {
          errorMessage.value = null
        }, 5000)
        break

      case 'success':
        // Handle success if needed
        break

      default:
        console.warn('Unknown message type:', (data as any).type)
    }
  }

  /**
   * Initialize WebSocket connection and event handlers
   */
  onMounted(() => {
    // Connect to WebSocket
    ws.connect()

    // Register message handler
    ws.on('message', handleMessage)

    // Fetch phrases once connected
    const checkConnection = setInterval(() => {
      if (ws.isConnected.value) {
        fetchPhrases()
        clearInterval(checkConnection)
      }
    }, 100)
  })

  return {
    // State
    bearState,
    phrases,
    currentMode,
    isConnected: ws.isConnected,
    errorMessage,

    // Computed
    isBusy,
    bearImage,

    // Actions
    updateBear,
    speak,
    play,
    setVolume,
    fetchPhrases,
    setMode,
    setBlinkEnabled,
  }
}

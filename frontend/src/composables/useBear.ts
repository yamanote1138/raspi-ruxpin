/**
 * Bear state management composable
 */

import { ref, computed, watch, onMounted, onUnmounted, type Ref, type ComputedRef } from 'vue'
import { useWebSocket } from './useWebSocket'
import { State, Mode, SyncMode, MouthCode, type BearState } from '@/types/bear'
import type {
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
  headerImage: ComputedRef<string>

  // Actions
  updateBear: (eyes?: State, mouth?: State) => void
  speak: (text: string) => Promise<void>
  play: (sound: string) => Promise<void>
  setVolume: (level: number) => void
  fetchPhrases: () => void
  setMode: (mode: Mode) => void
  setBlinkEnabled: (enabled: boolean) => void
  setCharacter: (character: string) => void
  setSyncMode: (mode: string) => void
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
    eyes_position: 0,
    mouth_position: 0,
    is_busy: false,
    volume: 100,
    blink_enabled: false,
    character: 'teddy',
  } as BearState)

  // UI state
  const phrases = ref<Phrases>({})
  const currentMode = ref<Mode>(Mode.CONTROL)
  const errorMessage = ref<string | null>(null)

  // Computed properties
  const isBusy = computed(() => bearState.value.is_busy)

  /**
   * Map position percentage to nearest of 5 discrete states
   */
  const getPositionLabel = (position: number): number => {
    // Map to nearest: 0, 25, 50, 75, 100
    if (position <= 12) return 0
    if (position <= 37) return 25
    if (position <= 62) return 50
    if (position <= 87) return 75
    return 100
  }

  const bearImage = computed(() => {
    const eyePos = getPositionLabel(bearState.value.eyes_position)
    const mouthPos = getPositionLabel(bearState.value.mouth_position)
    const char = bearState.value.character || 'teddy'
    return `/img/${char}_e${eyePos}m${mouthPos}.png`
  })

  const headerImage = computed(() => {
    const char = bearState.value.character || 'teddy'
    return `/img/header_${char === 'teddy' ? 't' : 'g'}.png`
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
    if (level < 0 || level > 90) {
      throw new Error('Volume must be between 0 and 90')
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
   * Set character (teddy or grubby)
   */
  const setCharacter = (character: string) => {
    const message = {
      type: 'set_character',
      character,
    }

    ws.send(message)
  }

  /**
   * Set sync mode (amplitude or phoneme)
   */
  const setSyncMode = (mode: string) => {
    const message = {
      type: 'set_sync_mode',
      mode,
    }

    ws.send(message)
  }

  /**
   * Handle incoming WebSocket messages
   */
  let lastMouthPosition = 0
  let lastSyncMode = ''
  let lastBusy = false
  let lastStatusText = ''

  const handleMessage = (data: WebSocketMessage) => {
    switch (data.type) {
      case 'bear_state':
        const stateMsg = data as BearStateMessage
        const newMouthPos = stateMsg.data.mouth_position ?? 0
        const newSyncMode = stateMsg.data.sync_mode ?? 'amplitude'
        const newBusy = stateMsg.data.is_busy ?? false
        const newStatusText = stateMsg.data.status_text ?? ''

        if (newSyncMode !== lastSyncMode) {
          if (lastSyncMode) {
            console.log(`Sync mode: ${lastSyncMode} → ${newSyncMode}`)
          }
          lastSyncMode = newSyncMode
        }
        if (newMouthPos !== lastMouthPosition) {
          console.log(`Mouth: ${lastMouthPosition} → ${newMouthPos} (code: ${stateMsg.data.mouth_code ?? '?'})`)
          lastMouthPosition = newMouthPos
        }
        if (newBusy !== lastBusy) {
          console.log(`Bear ${newBusy ? 'busy' : 'idle'}${newStatusText ? ': ' + newStatusText : ''}`)
          lastBusy = newBusy
        } else if (newStatusText !== lastStatusText && newStatusText) {
          console.log(`Status: ${newStatusText}`)
        }
        lastStatusText = newStatusText
        bearState.value = {
          eyes: stateMsg.data.eyes,
          mouth: stateMsg.data.mouth,
          eyes_position: stateMsg.data.eyes_position ?? 0,
          mouth_position: newMouthPos,
          is_busy: stateMsg.data.is_busy,
          volume: stateMsg.data.volume,
          blink_enabled: stateMsg.data.blink_enabled ?? true,
          character: stateMsg.data.character ?? 'teddy',
          sync_mode: (stateMsg.data.sync_mode ?? 'amplitude') as SyncMode,
          mouth_code: (stateMsg.data.mouth_code ?? 'C') as MouthCode,
          arduino_connected: stateMsg.data.arduino_connected ?? false,
          arduino_port: stateMsg.data.arduino_port ?? '',
          arduino_baud_rate: stateMsg.data.arduino_baud_rate ?? 0,
          arduino_connection_type: stateMsg.data.arduino_connection_type ?? 'unknown',
          status_text: stateMsg.data.status_text ?? '',
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

    // Watch connection state and fetch phrases when connected
    watch(
      () => ws.isConnected.value,
      (connected) => {
        if (connected) {
          console.log('WebSocket connected, fetching phrases...')
          fetchPhrases()
        }
      },
      { immediate: true }
    )
  })

  // Clean up handler on unmount (prevents HMR duplicates)
  onUnmounted(() => {
    ws.off('message', handleMessage)
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
    headerImage,

    // Actions
    updateBear,
    speak,
    play,
    setVolume,
    fetchPhrases,
    setMode,
    setBlinkEnabled,
    setCharacter,
    setSyncMode,
  }
}

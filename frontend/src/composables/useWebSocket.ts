/**
 * WebSocket connection composable
 */

import { ref, onUnmounted, type Ref } from 'vue'
import type { WebSocketMessage } from '@/types/websocket'

export interface WebSocketComposable {
  socket: Ref<WebSocket | null>
  isConnected: Ref<boolean>
  connect: () => void
  disconnect: () => void
  send: (message: any) => void
  on: (event: string, callback: (data: any) => void) => void
  off: (event: string, callback?: (data: any) => void) => void
}

// Shared WebSocket instance (singleton)
let sharedSocket: WebSocket | null = null
let sharedIsConnected = ref(false)
let sharedEventHandlers = new Map<string, Set<(data: any) => void>>()
let reconnectTimeout: number | null = null
let reconnectAttempts = 0
const maxReconnectDelay = 5000
const baseReconnectDelay = 1000
let shouldReconnect = true

/**
 * Composable for managing WebSocket connection (singleton pattern)
 */
export function useWebSocket(url: string = '/ws'): WebSocketComposable {
  const socket = ref<WebSocket | null>(sharedSocket)
  const isConnected = sharedIsConnected

  /**
   * Connect to WebSocket server
   */
  const connect = () => {
    if (sharedSocket && sharedSocket.readyState !== WebSocket.CLOSED) {
      return
    }

    // Enable auto-reconnect
    shouldReconnect = true

    // Build WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}${url}`

    console.log('Connecting to WebSocket:', wsUrl)

    // Create WebSocket connection
    sharedSocket = new WebSocket(wsUrl)
    socket.value = sharedSocket

    // Connection opened
    sharedSocket.onopen = () => {
      console.log('WebSocket connected')
      sharedIsConnected.value = true
      reconnectAttempts = 0
    }

    // Message received
    sharedSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        // Emit to generic 'message' handlers
        const messageHandlers = sharedEventHandlers.get('message')
        if (messageHandlers) {
          messageHandlers.forEach(callback => callback(data))
        }

        // Route to type-specific handlers
        if (data.type) {
          const typeHandlers = sharedEventHandlers.get(data.type)
          if (typeHandlers) {
            typeHandlers.forEach(callback => callback(data.data || data))
          }
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    // Connection closed
    sharedSocket.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason)
      sharedIsConnected.value = false
      sharedSocket = null
      socket.value = null

      // Always attempt to reconnect unless explicitly disconnected
      if (shouldReconnect) {
        const delay = Math.min(
          baseReconnectDelay * Math.pow(2, reconnectAttempts),
          maxReconnectDelay
        )
        reconnectAttempts++

        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`)
        reconnectTimeout = window.setTimeout(() => {
          connect()
        }, delay)
      }
    }

    // Connection error
    sharedSocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = () => {
    // Disable auto-reconnect
    shouldReconnect = false

    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }

    if (sharedSocket) {
      sharedSocket.close()
      sharedSocket = null
      socket.value = null
      sharedIsConnected.value = false
    }
  }

  /**
   * Send a message to the server
   */
  const send = (message: any) => {
    if (sharedSocket && sharedIsConnected.value) {
      sharedSocket.send(JSON.stringify(message))
    } else {
      console.error('Cannot send message: WebSocket not connected')
    }
  }

  /**
   * Register an event listener
   */
  const on = (event: string, callback: (data: any) => void) => {
    if (!sharedEventHandlers.has(event)) {
      sharedEventHandlers.set(event, new Set())
    }
    sharedEventHandlers.get(event)!.add(callback)
  }

  /**
   * Unregister an event listener
   */
  const off = (event: string, callback?: (data: any) => void) => {
    if (callback) {
      const handlers = sharedEventHandlers.get(event)
      if (handlers) {
        handlers.delete(callback)
      }
    } else {
      sharedEventHandlers.delete(event)
    }
  }

  // Note: Don't auto-disconnect on unmount for singleton pattern
  // The connection should persist across component lifecycle

  return {
    socket,
    isConnected,
    connect,
    disconnect,
    send,
    on,
    off,
  }
}

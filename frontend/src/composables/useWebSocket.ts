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

/**
 * Composable for managing WebSocket connection
 */
export function useWebSocket(url: string = '/ws'): WebSocketComposable {
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const eventHandlers = new Map<string, Set<(data: any) => void>>()
  let reconnectTimeout: number | null = null
  let reconnectAttempts = 0
  const maxReconnectDelay = 5000
  const baseReconnectDelay = 1000

  /**
   * Connect to WebSocket server
   */
  const connect = () => {
    if (socket.value && socket.value.readyState !== WebSocket.CLOSED) {
      return
    }

    // Build WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}${url}`

    console.log('Connecting to WebSocket:', wsUrl)

    // Create WebSocket connection
    socket.value = new WebSocket(wsUrl)

    // Connection opened
    socket.value.onopen = () => {
      console.log('WebSocket connected')
      isConnected.value = true
      reconnectAttempts = 0
    }

    // Message received
    socket.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        // Emit to all registered handlers
        const handlers = eventHandlers.get('message')
        if (handlers) {
          handlers.forEach(callback => callback(data))
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    // Connection closed
    socket.value.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason)
      isConnected.value = false
      socket.value = null

      // Attempt to reconnect with exponential backoff
      if (!event.wasClean) {
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
    socket.value.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }

    if (socket.value) {
      socket.value.close()
      socket.value = null
      isConnected.value = false
    }
  }

  /**
   * Send a message to the server
   */
  const send = (message: any) => {
    if (socket.value && isConnected.value) {
      socket.value.send(JSON.stringify(message))
    } else {
      console.error('Cannot send message: WebSocket not connected')
    }
  }

  /**
   * Register an event listener
   */
  const on = (event: string, callback: (data: any) => void) => {
    if (!eventHandlers.has(event)) {
      eventHandlers.set(event, new Set())
    }
    eventHandlers.get(event)!.add(callback)
  }

  /**
   * Unregister an event listener
   */
  const off = (event: string, callback?: (data: any) => void) => {
    if (callback) {
      const handlers = eventHandlers.get(event)
      if (handlers) {
        handlers.delete(callback)
      }
    } else {
      eventHandlers.delete(event)
    }
  }

  // Auto-disconnect on unmount
  onUnmounted(() => {
    disconnect()
  })

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

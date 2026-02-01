<template>
  <div class="log-viewer card bg-panel">
    <div class="card-body">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="card-title mb-0 text-dark">Logs</h5>
        <div class="d-flex gap-2 align-items-center">
          <!-- Log level dropdown -->
          <select
            v-model="currentLevel"
            class="form-select form-select-sm"
            style="width: auto;"
            @change="setLogLevel(currentLevel)"
            title="Log level filter"
          >
            <option v-for="level in logLevels" :key="level" :value="level">
              {{ level }}
            </option>
          </select>

          <!-- Button bar for controls -->
          <div class="btn-group" role="group">
            <button
              type="button"
              class="btn btn-sm"
              :class="autoScroll ? 'btn-success' : 'btn-secondary'"
              @click="autoScroll = !autoScroll"
              title="Toggle auto-scroll"
            >
              <i class="bi me-1" :class="autoScroll ? 'bi-unlock' : 'bi-lock'"></i>
              Auto-scroll
            </button>
            <button
              type="button"
              class="btn btn-sm btn-danger"
              @click="clearLogs"
              title="Clear logs"
            >
              <i class="bi bi-trash me-1"></i>
              Clear
            </button>
          </div>
        </div>
      </div>

      <div class="log-container" ref="logContainer">
        <div
          v-for="(log, index) in filteredLogs"
          :key="`${log.timestamp}-${index}`"
          class="log-entry"
          :class="`log-${log.level.toLowerCase()}`"
        >
          <span class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</span>
          <span class="log-level" :class="`badge bg-${getLevelClass(log.level)}`">
            {{ log.level }}
          </span>
          <span class="log-logger">{{ log.logger }}</span>
          <span class="log-message">{{ log.message }}</span>
          <span class="log-location" v-if="currentLevel === 'DEBUG'">
            ({{ log.module }}:{{ log.function }}:{{ log.line }})
          </span>
          <pre v-if="log.exception" class="log-exception">{{ log.exception }}</pre>
        </div>

        <div v-if="filteredLogs.length === 0" class="text-center text-muted p-4">
          No logs to display
        </div>
      </div>

      <div class="text-muted small mt-2">
        Showing {{ filteredLogs.length }} of {{ logs.length }} logs
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import type { LogMessage } from '@/types/websocket'
import { useWebSocket } from '@/composables/useWebSocket'

const ws = useWebSocket()

// State
const logs = ref<LogMessage[]>([])
const currentLevel = ref<string>('INFO') // Default log level
const autoScroll = ref<boolean>(true)
const logContainer = ref<HTMLElement | null>(null)

const logLevels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

// Log level priority for filtering
const levelPriority: Record<string, number> = {
  DEBUG: 0,
  INFO: 1,
  WARNING: 2,
  ERROR: 3,
  CRITICAL: 4,
}

// Computed
const filteredLogs = computed(() => {
  const currentPriority = levelPriority[currentLevel.value] || 0
  return logs.value.filter(log => {
    const logPriority = levelPriority[log.level] || 0
    return logPriority >= currentPriority
  })
})

// Methods
function addLog(log: LogMessage) {
  logs.value.push(log)

  // Keep only last 1000 logs
  if (logs.value.length > 1000) {
    logs.value = logs.value.slice(-1000)
  }

  // Auto-scroll if enabled
  if (autoScroll.value) {
    nextTick(() => {
      scrollToBottom()
    })
  }
}

function clearLogs() {
  logs.value = []
}

function setLogLevel(level: string) {
  currentLevel.value = level

  // Send to backend to change server log level
  ws.send({
    type: 'set_log_level',
    level,
  })
}

function scrollToBottom() {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp * 1000)
  return date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
  })
}

function getLevelClass(level: string): string {
  const classes: Record<string, string> = {
    DEBUG: 'secondary',
    INFO: 'info',
    WARNING: 'warning',
    ERROR: 'danger',
    CRITICAL: 'danger',
  }
  return classes[level] || 'secondary'
}

// Watch for log messages from WebSocket
onMounted(() => {
  ws.on('log', (data: LogMessage) => {
    addLog(data)
  })
})

// Auto-scroll when filtered logs change
watch(filteredLogs, () => {
  if (autoScroll.value) {
    nextTick(() => {
      scrollToBottom()
    })
  }
})

// Expose for parent component if needed
defineExpose({
  addLog,
  clearLogs,
})
</script>

<style scoped>
.log-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.log-container {
  height: 500px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 0.5rem;
}

.log-entry {
  padding: 0.25rem 0.5rem;
  border-bottom: 1px solid #333;
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
  flex-wrap: wrap;
}

.log-entry:hover {
  background-color: #2a2a2a;
}

.log-timestamp {
  color: #808080;
  flex-shrink: 0;
  font-size: 0.8rem;
}

.log-level {
  flex-shrink: 0;
  font-size: 0.7rem;
  min-width: 70px;
  text-align: center;
}

.log-logger {
  color: #4ec9b0;
  flex-shrink: 0;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-message {
  flex-grow: 1;
  word-break: break-word;
}

.log-location {
  color: #808080;
  font-size: 0.75rem;
  flex-basis: 100%;
  margin-left: calc(70px + 1rem); /* Align with message */
}

.log-exception {
  flex-basis: 100%;
  margin-left: calc(70px + 1rem);
  margin-top: 0.5rem;
  padding: 0.5rem;
  background-color: #2a1a1a;
  border-left: 3px solid #dc3545;
  color: #ff6b6b;
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-all;
}

/* Log level colors */
.log-debug {
  opacity: 0.7;
}

.log-info {
  /* Default */
}

.log-warning .log-message {
  color: #ffc107;
}

.log-error .log-message {
  color: #ff6b6b;
  font-weight: bold;
}

.log-critical .log-message {
  color: #ff3838;
  font-weight: bold;
}

/* Scrollbar styling for webkit browsers */
.log-container::-webkit-scrollbar {
  width: 8px;
}

.log-container::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.log-container::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.log-container::-webkit-scrollbar-thumb:hover {
  background: #777;
}
</style>

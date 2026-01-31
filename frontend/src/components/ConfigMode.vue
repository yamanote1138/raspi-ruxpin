<template>
  <div class="config-mode">
    <div class="row">
      <!-- Configuration Panel -->
      <div class="col-lg-4 mb-4">
        <div class="card bg-secondary">
          <div class="card-body">
            <h5 class="card-title mb-3">Settings</h5>

            <!-- Blink Toggle -->
            <div class="mb-4">
              <div class="form-check form-switch">
                <input
                  id="blink-toggle"
                  type="checkbox"
                  class="form-check-input"
                  role="switch"
                  :checked="bearState.blink_enabled"
                  @change="handleBlinkToggle"
                />
                <label class="form-check-label" for="blink-toggle">
                  <strong>Automatic Eye Blinking</strong>
                </label>
              </div>
              <small class="text-muted d-block mt-2">
                {{ bearState.blink_enabled ? 'Eyes will blink randomly when idle' : 'Eye blinking disabled (saves motor wear)' }}
              </small>
            </div>

            <!-- System Info -->
            <div class="mt-4">
              <h6 class="mb-2">System Status</h6>
              <table class="table table-sm table-dark">
                <tbody>
                  <tr>
                    <td>Eyes</td>
                    <td>
                      <span class="badge" :class="eyesBadgeClass">
                        {{ bearState.eyes }}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td>Mouth</td>
                    <td>
                      <span class="badge" :class="mouthBadgeClass">
                        {{ bearState.mouth }}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td>Volume</td>
                    <td>{{ bearState.volume }}%</td>
                  </tr>
                  <tr>
                    <td>Status</td>
                    <td>
                      <span v-if="bearState.is_busy" class="badge bg-warning">Busy</span>
                      <span v-else class="badge bg-success">Idle</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Live Log Viewer -->
      <div class="col-lg-8 mb-4">
        <div class="card bg-secondary">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h5 class="card-title mb-0">Activity Log</h5>
              <button
                type="button"
                class="btn btn-sm btn-outline-light"
                @click="clearLogs"
              >
                Clear
              </button>
            </div>

            <div class="log-viewer">
              <div
                v-for="(log, index) in logs"
                :key="index"
                class="log-entry"
                :class="log.type"
              >
                <span class="log-time">{{ log.time }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
              <div v-if="logs.length === 0" class="text-muted text-center py-4">
                No activity yet. Activity will appear here as you interact with the bear.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { State, type BearState } from '@/types/bear'

const props = defineProps<{
  bearState: BearState
}>()

const emit = defineEmits<{
  'set-blink-enabled': [enabled: boolean]
}>()

interface LogEntry {
  time: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}

const logs = ref<LogEntry[]>([])
const maxLogs = 100

// Badge styling
const eyesBadgeClass = computed(() =>
  props.bearState.eyes === State.OPEN ? 'bg-success' : 'bg-danger'
)

const mouthBadgeClass = computed(() =>
  props.bearState.mouth === State.OPEN ? 'bg-success' : 'bg-danger'
)

// Handlers
const handleBlinkToggle = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('set-blink-enabled', target.checked)
  addLog(
    target.checked ? 'Eye blinking enabled' : 'Eye blinking disabled',
    'info'
  )
}

const addLog = (message: string, type: LogEntry['type'] = 'info') => {
  const now = new Date()
  const time = now.toLocaleTimeString('en-US', { hour12: false })

  logs.value.unshift({
    time,
    message,
    type,
  })

  // Keep only the most recent logs
  if (logs.value.length > maxLogs) {
    logs.value = logs.value.slice(0, maxLogs)
  }
}

const clearLogs = () => {
  logs.value = []
  addLog('Logs cleared', 'info')
}

// Watch for state changes and log them
watch(
  () => props.bearState.eyes,
  (newVal, oldVal) => {
    if (oldVal && newVal !== oldVal) {
      addLog(`Eyes ${newVal}`, newVal === State.OPEN ? 'success' : 'info')
    }
  }
)

watch(
  () => props.bearState.mouth,
  (newVal, oldVal) => {
    if (oldVal && newVal !== oldVal) {
      addLog(`Mouth ${newVal}`, newVal === State.OPEN ? 'success' : 'info')
    }
  }
)

watch(
  () => props.bearState.is_busy,
  (newVal, oldVal) => {
    if (oldVal !== undefined && newVal !== oldVal) {
      addLog(newVal ? 'Bear busy - playing audio' : 'Bear idle', newVal ? 'warning' : 'success')
    }
  }
)

watch(
  () => props.bearState.volume,
  (newVal, oldVal) => {
    if (oldVal && newVal !== oldVal) {
      addLog(`Volume changed to ${newVal}%`, 'info')
    }
  }
)
</script>

<style scoped>
.form-check-input {
  cursor: pointer;
  width: 3rem;
  height: 1.5rem;
}

.form-check-label {
  cursor: pointer;
  padding-left: 0.5rem;
}

.log-viewer {
  background-color: #1a1d20;
  border: 1px solid #495057;
  border-radius: 0.25rem;
  padding: 1rem;
  height: 500px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
}

.log-entry {
  padding: 0.25rem 0;
  border-bottom: 1px solid #343a40;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-time {
  color: #6c757d;
  margin-right: 0.5rem;
}

.log-message {
  color: #f8f9fa;
}

.log-entry.success .log-message {
  color: #28a745;
}

.log-entry.warning .log-message {
  color: #ffc107;
}

.log-entry.error .log-message {
  color: #dc3545;
}

.log-entry.info .log-message {
  color: #17a2b8;
}

/* Scrollbar styling */
.log-viewer::-webkit-scrollbar {
  width: 8px;
}

.log-viewer::-webkit-scrollbar-track {
  background: #212529;
}

.log-viewer::-webkit-scrollbar-thumb {
  background: #495057;
  border-radius: 4px;
}

.log-viewer::-webkit-scrollbar-thumb:hover {
  background: #6c757d;
}
</style>

<template>
  <div class="config-mode">
    <div class="card bg-panel">
      <div class="card-body">
        <h6 class="card-title mb-3">Arduino</h6>

        <div class="d-flex align-items-center gap-2 mb-3 small">
          <span class="badge" :class="arduinoConnected ? 'bg-success' : 'bg-danger'">
            {{ arduinoConnected ? 'Connected' : 'Disconnected' }}
          </span>
          <span v-if="connectionType === 'mock'" class="text-muted">Mock serial</span>
          <span v-else class="text-muted">
            {{ port }} · {{ baudRate }} baud
          </span>
        </div>

        <table class="table table-sm table-borderless text-dark mb-0">
          <tbody>
            <tr>
              <td class="text-muted fw-bold" style="width: 80px;">Sync</td>
              <td><span class="badge bg-info text-dark">{{ syncMode }}</span></td>
            </tr>
            <tr>
              <td class="text-muted fw-bold">Eyes</td>
              <td>
                <span class="badge" :class="eyes === 'open' ? 'bg-warning text-dark' : 'bg-secondary'">
                  {{ eyes }}
                </span>
              </td>
            </tr>
            <tr>
              <td class="text-muted fw-bold">Mouth</td>
              <td>
                <div class="d-flex align-items-center gap-2">
                  <div class="progress flex-grow-1" style="max-width: 120px; height: 8px;">
                    <div
                      class="progress-bar"
                      :class="mouthPercent > 0 ? 'bg-primary' : 'bg-secondary'"
                      role="progressbar"
                      :style="{ width: mouthPercent + '%' }"
                    ></div>
                  </div>
                  <span class="badge bg-dark font-monospace">{{ mouthCode }}</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { BearState } from '@/types/bear'

const props = defineProps<{
  bearState: BearState
}>()

const arduinoConnected = computed(() => props.bearState?.arduino_connected ?? false)
const connectionType = computed(() => props.bearState?.arduino_connection_type ?? 'unknown')
const port = computed(() => props.bearState?.arduino_port ?? '')
const baudRate = computed(() => props.bearState?.arduino_baud_rate ?? 0)
const syncMode = computed(() => props.bearState?.sync_mode ?? 'amplitude')
const eyes = computed(() => props.bearState?.eyes ?? 'unknown')
const mouthCode = computed(() => props.bearState?.mouth_code ?? 'C')
const mouthPercent = computed(() => props.bearState?.mouth_position ?? 0)
</script>

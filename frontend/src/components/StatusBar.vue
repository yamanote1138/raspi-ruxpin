<template>
  <div class="status-bar d-flex align-items-center gap-3">
    <!-- Connection Status -->
    <div class="d-flex align-items-center">
      <span
        class="status-indicator me-2"
        :class="isConnected ? 'connected' : 'disconnected'"
      ></span>
      <span class="small text-dark">
        {{ isConnected ? 'Connected' : 'Disconnected' }}
      </span>
    </div>

    <!-- Mode Toggle -->
    <div class="btn-group" role="group">
      <button
        type="button"
        class="btn btn-sm mode-btn"
        :class="currentMode === Mode.CONTROL ? 'btn-primary' : 'btn-light'"
        @click="$emit('set-mode', Mode.CONTROL)"
      >
        Control
      </button>
      <button
        type="button"
        class="btn btn-sm mode-btn"
        :class="currentMode === Mode.SYSTEM ? 'btn-primary' : 'btn-light'"
        @click="$emit('set-mode', Mode.SYSTEM)"
      >
        System
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Mode } from '@/types/bear'

defineProps<{
  isConnected: boolean
  currentMode: Mode
}>()

defineEmits<{
  'set-mode': [mode: Mode]
}>()
</script>

<style scoped>
.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-indicator.connected {
  background-color: #28a745;
  box-shadow: 0 0 8px #28a745;
}

.status-indicator.disconnected {
  background-color: #dc3545;
  box-shadow: 0 0 8px #dc3545;
}
</style>

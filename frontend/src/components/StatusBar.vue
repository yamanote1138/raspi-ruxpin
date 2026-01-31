<template>
  <div class="status-bar d-flex align-items-center gap-3">
    <!-- Connection Status -->
    <div class="d-flex align-items-center">
      <span
        class="status-indicator me-2"
        :class="isConnected ? 'connected' : 'disconnected'"
      ></span>
      <span class="small">
        {{ isConnected ? 'Connected' : 'Disconnected' }}
      </span>
    </div>

    <!-- Mode Toggle -->
    <div class="btn-group" role="group">
      <button
        type="button"
        class="btn btn-sm"
        :class="currentMode === Mode.PUPPET ? 'btn-primary' : 'btn-outline-primary'"
        @click="$emit('set-mode', Mode.PUPPET)"
      >
        Puppet
      </button>
      <button
        type="button"
        class="btn btn-sm"
        :class="currentMode === Mode.SPEAK ? 'btn-primary' : 'btn-outline-primary'"
        @click="$emit('set-mode', Mode.SPEAK)"
      >
        Speak
      </button>
      <button
        type="button"
        class="btn btn-sm"
        :class="currentMode === Mode.CONFIG ? 'btn-primary' : 'btn-outline-primary'"
        @click="$emit('set-mode', Mode.CONFIG)"
      >
        Config
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
  display: inline-block;
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

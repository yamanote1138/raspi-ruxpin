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

    <!-- Character Toggle -->
    <div class="btn-group" role="group">
      <button
        type="button"
        class="btn btn-sm mode-btn"
        :class="character === 'teddy' ? 'btn-success' : 'btn-light'"
        @click="$emit('set-character', 'teddy')"
        :disabled="!isConnected"
      >
        Teddy
      </button>
      <button
        type="button"
        class="btn btn-sm mode-btn"
        :class="character === 'grubby' ? 'btn-success' : 'btn-light'"
        @click="$emit('set-character', 'grubby')"
        :disabled="!isConnected"
      >
        Grubby
      </button>
    </div>

    <!-- Info Button -->
    <button
      type="button"
      class="btn btn-sm btn-outline-dark rounded-circle d-flex align-items-center justify-content-center"
      style="width: 28px; height: 28px;"
      @click="$emit('show-info')"
      title="System info"
    >
      <i class="bi bi-info-lg"></i>
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  isConnected: boolean
  character: string
}>()

defineEmits<{
  'set-character': [character: string]
  'show-info': []
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

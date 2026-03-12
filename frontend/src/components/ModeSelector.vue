<template>
  <div class="mode-selector d-flex align-items-center gap-2">
    <span class="text-light small fw-bold">Sync:</span>
    <div class="btn-group btn-group-sm" role="group">
      <button
        type="button"
        class="btn"
        :class="syncMode === 'amplitude' ? 'btn-active-mode' : 'btn-inactive-mode'"
        @click="$emit('change', 'amplitude')"
        title="Pi pre-analyzes WAV amplitude, sends timed commands"
      >
        Amplitude
      </button>
      <button
        type="button"
        class="btn"
        :class="syncMode === 'phoneme' ? 'btn-active-mode' : 'btn-inactive-mode'"
        @click="$emit('change', 'phoneme')"
        title="Pi analyzes phonemes (requires extra deps), sends timed commands"
      >
        Phoneme
      </button>
      <button
        type="button"
        class="btn"
        :class="syncMode === 'realtime' ? 'btn-active-mode' : 'btn-inactive-mode'"
        @click="$emit('change', 'realtime')"
        title="Arduino reads audio signal and drives servos in real-time"
      >
        Realtime
      </button>
    </div>
    <span
      class="badge"
      :class="arduinoConnected ? 'bg-success' : 'bg-secondary'"
    >
      {{ arduinoConnected ? 'Arduino' : 'Mock' }}
    </span>
    <span v-if="mouthCode !== 'C'" class="badge bg-info">
      Mouth: {{ mouthCode }}
    </span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  syncMode: string
  arduinoConnected: boolean
  mouthCode: string
}>()

defineEmits<{
  change: [mode: string]
}>()
</script>

<style scoped>
.btn-active-mode {
  background-color: #0d6efd;
  border-color: #0d6efd;
  color: #fff;
  font-weight: 600;
  box-shadow: 0 0 0 2px rgba(13, 110, 253, 0.5);
}

.btn-inactive-mode {
  background-color: #2b2b2b;
  border-color: #555;
  color: #999;
}

.btn-inactive-mode:hover {
  background-color: #3a3a3a;
  border-color: #777;
  color: #ccc;
}
</style>

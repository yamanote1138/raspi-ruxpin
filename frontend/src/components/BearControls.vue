<template>
  <div class="bear-controls">
    <div class="card-body">
      <!-- Bear Controls Row -->
      <div class="d-flex justify-content-center">
        <div class="btn-group" role="group">
          <button
            type="button"
            class="btn btn-sm"
            :class="bearState.eyes === 'open' ? 'btn-success' : 'btn-danger'"
            :disabled="bearState.is_busy"
            @click="toggleEyes"
          >
            <i class="bi" :class="bearState.eyes === 'open' ? 'bi-eye-fill' : 'bi-eye-slash-fill'"></i>
            Eyes: {{ bearState.eyes }}
          </button>
          <button
            type="button"
            class="btn btn-sm"
            :class="bearState.mouth === 'open' ? 'btn-success' : 'btn-danger'"
            :disabled="bearState.is_busy"
            @click="toggleMouth"
          >
            <i class="bi" :class="bearState.mouth === 'open' ? 'bi-emoji-laughing-fill' : 'bi-emoji-smile-fill'"></i>
            Mouth: {{ bearState.mouth }}
          </button>
          <button
            type="button"
            class="btn btn-sm"
            :class="bearState.blink_enabled ? 'btn-success' : 'btn-secondary'"
            :disabled="bearState.is_busy"
            @click="toggleBlink"
          >
            <i class="bi" :class="bearState.blink_enabled ? 'bi-stars' : 'bi-dash-circle'"></i>
            Blink: {{ bearState.blink_enabled ? 'on' : 'off' }}
          </button>
          <select
            v-model.number="localVolume"
            class="btn btn-sm btn-secondary"
            :disabled="bearState.is_busy"
            @change="handleVolumeChange"
          >
            <option v-for="v in volumeSteps" :key="v" :value="v">
              Vol: {{ v }}%
            </option>
          </select>
        </div>
      </div>

      <!-- Status Row -->
      <div class="d-flex flex-wrap justify-content-center align-items-center gap-2 mt-2">
        <div class="btn-group" role="group">
          <button
            type="button"
            class="btn btn-sm"
            :class="isConnected ? 'btn-success' : 'btn-danger'"
            disabled
          >
            <i class="bi" :class="isConnected ? 'bi-wifi' : 'bi-wifi-off'"></i>
            Socket
          </button>
          <button
            type="button"
            class="btn btn-sm"
            :class="bearState.arduino_connected ? 'btn-success' : 'btn-danger'"
            disabled
          >
            <i class="bi bi-cpu"></i>
            Arduino
          </button>
          <button
            type="button"
            class="btn btn-sm btn-info"
            :disabled="bearState.is_busy"
            @click="cycleSync"
            :title="syncTitle"
          >
            <i class="bi" :class="syncIcon"></i>
            {{ syncLabel }}
          </button>
          <button
            type="button"
            class="btn btn-sm"
            :class="bearState.is_busy ? 'btn-warning' : 'btn-success'"
            disabled
          >
            <span v-if="bearState.is_busy">
              <span class="spinner-border spinner-border-sm me-1" role="status"></span>
              Busy
            </span>
            <span v-else>Idle</span>
          </button>
          <button
            type="button"
            class="btn btn-sm btn-primary"
            @click="$emit('show-info')"
            title="System info"
          >
            <i class="bi bi-info-circle"></i>
          </button>
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
  isConnected: boolean
}>()

const emit = defineEmits<{
  'update-bear': [eyes?: State, mouth?: State]
  'set-blink-enabled': [enabled: boolean]
  'set-volume': [level: number]
  'set-sync-mode': [mode: string]
  'show-info': []
}>()

const allSyncModes = ['amplitude', 'phoneme', 'realtime'] as const
const syncConfig: Record<string, { label: string; icon: string; title: string }> = {
  amplitude: { label: 'Amplitude', icon: 'bi-soundwave', title: 'Pi pre-analyzes WAV amplitude' },
  phoneme: { label: 'Phoneme', icon: 'bi-chat-dots', title: 'Pi analyzes phonemes (requires extra deps)' },
  realtime: { label: 'Realtime', icon: 'bi-lightning', title: 'Arduino reads audio signal in real-time' },
}

const availableSyncModes = computed(() =>
  allSyncModes.filter(m => m !== 'phoneme' || props.bearState.phoneme_available)
)
const currentSync = computed(() => props.bearState.sync_mode || 'amplitude')
const syncLabel = computed(() => syncConfig[currentSync.value]?.label ?? 'Amplitude')
const syncIcon = computed(() => syncConfig[currentSync.value]?.icon ?? 'bi-soundwave')
const syncTitle = computed(() => syncConfig[currentSync.value]?.title ?? '')

const cycleSync = () => {
  const modes = availableSyncModes.value
  const idx = modes.indexOf(currentSync.value)
  const next = modes[(idx + 1) % modes.length]
  emit('set-sync-mode', next)
}

const volumeSteps = [10, 20, 30, 40, 50, 60, 70, 80, 90]
const localVolume = ref(props.bearState.volume)

watch(() => props.bearState.volume, (newVolume) => {
  localVolume.value = newVolume
})

const toggleEyes = () => {
  if (props.bearState.is_busy) return
  const newState = props.bearState.eyes === State.OPEN ? State.CLOSED : State.OPEN
  emit('update-bear', newState, undefined)
}

const toggleMouth = () => {
  if (props.bearState.is_busy) return
  const newState = props.bearState.mouth === State.OPEN ? State.CLOSED : State.OPEN
  emit('update-bear', undefined, newState)
}

const toggleBlink = () => {
  if (props.bearState.is_busy) return
  emit('set-blink-enabled', !props.bearState.blink_enabled)
}

const handleVolumeChange = () => {
  emit('set-volume', localVolume.value)
}
</script>

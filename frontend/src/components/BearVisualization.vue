<template>
  <div class="bear-visualization-panel">
    <div class="card bg-panel">
      <div class="card-body text-center">
        <!-- Bear Image -->
        <div class="bear-container position-relative d-inline-block">
          <img
            :key="bearImage"
            :src="bearImage"
            alt="Bear"
            class="bear-image img-fluid"
            usemap="#bearmap"
          />

          <!-- Image map for clicking (only active in puppet mode) -->
          <map v-if="clickable" name="bearmap">
            <area
              shape="rect"
              coords="50,30,150,80"
              alt="Eyes"
              @click="$emit('click-eyes')"
              style="cursor: pointer"
            />
            <area
              shape="rect"
              coords="60,100,140,150"
              alt="Mouth"
              @click="$emit('click-mouth')"
              style="cursor: pointer"
            />
          </map>
        </div>

        <!-- Status Controls -->
        <div class="mt-3 d-flex flex-wrap justify-content-center align-items-center gap-2">
          <!-- Toggle Button Group -->
          <div class="btn-group" role="group">
            <button
              type="button"
              class="btn btn-sm"
              :class="bearState.eyes === 'open' ? 'btn-success' : 'btn-danger'"
              :disabled="bearState.is_busy"
              @click="toggleEyes"
            >
              Eyes: {{ bearState.eyes }}
            </button>
            <button
              type="button"
              class="btn btn-sm"
              :class="bearState.mouth === 'open' ? 'btn-success' : 'btn-danger'"
              :disabled="bearState.is_busy"
              @click="toggleMouth"
            >
              Mouth: {{ bearState.mouth }}
            </button>
            <button
              type="button"
              class="btn btn-sm"
              :class="bearState.blink_enabled ? 'btn-success' : 'btn-secondary'"
              :disabled="bearState.is_busy"
              @click="toggleBlink"
            >
              Blink: {{ bearState.blink_enabled ? 'on' : 'off' }}
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
          </div>

          <!-- Volume Dropdown -->
          <select
            v-model.number="localVolume"
            class="form-select form-select-sm bg-dark text-light status-control"
            style="width: auto;"
            :disabled="bearState.is_busy"
            @change="handleVolumeChange"
          >
            <option :value="0">Vol: 0%</option>
            <option :value="20">Vol: 20%</option>
            <option :value="40">Vol: 40%</option>
            <option :value="60">Vol: 60%</option>
            <option :value="80">Vol: 80%</option>
            <option :value="100">Vol: 100%</option>
          </select>
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
  isBusy: boolean
  bearImage: string
  clickable?: boolean
}>()

const emit = defineEmits<{
  'click-eyes': []
  'click-mouth': []
  'update-bear': [eyes?: State, mouth?: State]
  'set-blink-enabled': [enabled: boolean]
  'set-volume': [level: number]
}>()

const localVolume = ref(props.bearState.volume)

// Watch for volume changes from backend
watch(() => props.bearState.volume, (newVolume) => {
  localVolume.value = newVolume
})

// Badge styling
const eyesBadgeClass = computed(() =>
  props.bearState.eyes === State.OPEN ? 'bg-success' : 'bg-danger'
)

const mouthBadgeClass = computed(() =>
  props.bearState.mouth === State.OPEN ? 'bg-success' : 'bg-danger'
)

const blinkBadgeClass = computed(() =>
  props.bearState.blink_enabled ? 'bg-success' : 'bg-secondary'
)

// Handlers
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

<style scoped>
.bear-container {
  max-width: 400px;
  margin: 0 auto;
}

.bear-image {
  transition: none !important; /* Disable ALL transitions */
  animation: none !important; /* Disable ALL animations */
  image-rendering: pixelated; /* Prevent anti-aliasing blur */
  backface-visibility: hidden; /* Prevent rendering artifacts */
  transform: translateZ(0); /* Force GPU acceleration */
  -webkit-font-smoothing: antialiased; /* Better rendering on webkit */
  opacity: 1 !important; /* Force full opacity always */
  filter: none !important; /* Remove any filters */
}

area {
  cursor: pointer;
}

/* Uniform height for status controls */
.status-control {
  height: 32px;
}
</style>

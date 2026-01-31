<template>
  <div class="bear-visualization-panel">
    <div class="card bg-secondary">
      <div class="card-body text-center">
        <h5 class="card-title mb-3">Bear Status</h5>

        <!-- Bear Image -->
        <div class="bear-container position-relative d-inline-block">
          <img
            :src="bearImage"
            alt="Bear"
            class="bear-image img-fluid"
            :class="{ 'opacity-50': isBusy }"
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

          <!-- Busy overlay -->
          <div v-if="isBusy" class="busy-overlay">
            <div class="spinner-border text-light" role="status">
              <span class="visually-hidden">Working...</span>
            </div>
          </div>
        </div>

        <!-- Status Badges -->
        <div class="mt-3">
          <span class="badge me-2" :class="eyesBadgeClass">
            Eyes: {{ bearState.eyes }}
          </span>
          <span class="badge me-2" :class="mouthBadgeClass">
            Mouth: {{ bearState.mouth }}
          </span>
          <span v-if="bearState.is_busy" class="badge bg-warning">
            <span class="spinner-border spinner-border-sm me-1" role="status"></span>
            Busy
          </span>
          <span v-else class="badge bg-success">Idle</span>
        </div>

        <!-- Additional Info -->
        <div class="mt-2">
          <small class="text-muted">
            Volume: {{ bearState.volume }}%
            <span v-if="bearState.blink_enabled" class="ms-2">
              <i class="bi bi-eye"></i> Auto-blink ON
            </span>
            <span v-else class="ms-2 text-warning">
              <i class="bi bi-eye-slash"></i> Auto-blink OFF
            </span>
          </small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { State, type BearState } from '@/types/bear'

const props = defineProps<{
  bearState: BearState
  isBusy: boolean
  bearImage: string
  clickable?: boolean
}>()

defineEmits<{
  'click-eyes': []
  'click-mouth': []
}>()

// Badge styling
const eyesBadgeClass = computed(() =>
  props.bearState.eyes === State.OPEN ? 'bg-success' : 'bg-danger'
)

const mouthBadgeClass = computed(() =>
  props.bearState.mouth === State.OPEN ? 'bg-success' : 'bg-danger'
)
</script>

<style scoped>
.bear-container {
  max-width: 400px;
  margin: 0 auto;
}

.bear-image {
  transition: opacity 0.3s ease;
}

.busy-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 0.25rem;
}

area {
  cursor: pointer;
}
</style>

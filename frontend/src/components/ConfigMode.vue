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

      <!-- System Log Viewer -->
      <div class="col-lg-8 mb-4">
        <LogViewer />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { State, type BearState } from '@/types/bear'
import LogViewer from './LogViewer.vue'

const props = defineProps<{
  bearState: BearState
}>()

const emit = defineEmits<{
  'set-blink-enabled': [enabled: boolean]
}>()

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
}
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
</style>

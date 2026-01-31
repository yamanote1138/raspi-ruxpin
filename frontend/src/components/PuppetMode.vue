<template>
  <div class="puppet-mode">
    <div class="row">
      <!-- Manual Controls -->
      <div class="col-lg-6 mb-4">
        <div class="card bg-secondary">
          <div class="card-body">
            <h5 class="card-title mb-3">Manual Controls</h5>

            <!-- Eyes Controls -->
            <div class="mb-4">
              <h6 class="mb-2">Eyes</h6>
              <div class="btn-group w-100" role="group">
                <button
                  type="button"
                  class="btn btn-outline-light"
                  :disabled="isBusy"
                  @click="setEyes(State.OPEN)"
                >
                  Open Eyes
                </button>
                <button
                  type="button"
                  class="btn btn-outline-light"
                  :disabled="isBusy"
                  @click="setEyes(State.CLOSED)"
                >
                  Close Eyes
                </button>
              </div>
            </div>

            <!-- Mouth Controls -->
            <div class="mb-4">
              <h6 class="mb-2">Mouth</h6>
              <div class="btn-group w-100" role="group">
                <button
                  type="button"
                  class="btn btn-outline-light"
                  :disabled="isBusy"
                  @click="setMouth(State.OPEN)"
                >
                  Open Mouth
                </button>
                <button
                  type="button"
                  class="btn btn-outline-light"
                  :disabled="isBusy"
                  @click="setMouth(State.CLOSED)"
                >
                  Close Mouth
                </button>
              </div>
            </div>

            <!-- Quick Actions -->
            <div>
              <h6 class="mb-2">Quick Actions</h6>
              <div class="d-grid gap-2">
                <button
                  type="button"
                  class="btn btn-success"
                  :disabled="isBusy"
                  @click="wakeUp"
                >
                  Wake Up (Open Eyes & Mouth)
                </button>
                <button
                  type="button"
                  class="btn btn-warning"
                  :disabled="isBusy"
                  @click="sleep"
                >
                  Sleep (Close Eyes & Mouth)
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Info Card -->
        <div class="card bg-secondary mt-3">
          <div class="card-body">
            <h6 class="card-title">
              <i class="bi bi-info-circle"></i>
              Tips
            </h6>
            <ul class="small mb-0">
              <li>Click on the bear image above to toggle eyes or mouth</li>
              <li>Use the buttons below for precise control</li>
              <li>Quick actions let you control both at once</li>
              <li>Controls are disabled when bear is busy</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Spacer column for layout balance -->
      <div class="col-lg-6 mb-4">
        <div class="card bg-secondary">
          <div class="card-body text-center text-muted">
            <h5 class="card-title">Manual Control Mode</h5>
            <p>Use the controls on the left to manually operate the bear's eyes and mouth.</p>
            <p class="mb-0">
              <small>
                The bear visualization above shows the current state and is clickable in this mode.
              </small>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { State, type BearState } from '@/types/bear'

const props = defineProps<{
  bearState: BearState
  isBusy: boolean
}>()

const emit = defineEmits<{
  'update-bear': [eyes?: State, mouth?: State]
}>()

// Actions
const setEyes = (state: State) => {
  emit('update-bear', state, undefined)
}

const setMouth = (state: State) => {
  emit('update-bear', undefined, state)
}

const wakeUp = () => {
  emit('update-bear', State.OPEN, State.OPEN)
}

const sleep = () => {
  emit('update-bear', State.CLOSED, State.CLOSED)
}
</script>

<style scoped>
/* Puppet mode specific styles */
</style>

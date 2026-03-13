<template>
  <div id="app" class="min-vh-100 bg-dark text-light">
    <!-- Header -->
    <header class="bg-panel py-3 mb-4">
      <div class="container-fluid px-3 px-md-4">
        <div class="row justify-content-center">
          <div class="col-12 col-xxl-10">
            <div class="row align-items-center">
              <div class="col">
                <h1 class="mb-0">
                  <img :src="headerImage" alt="Raspi" height="40" />
                </h1>
              </div>
              <div class="col-auto">
                <StatusBar
                  :is-connected="isConnected"
                  :character="bearState.character"
                  @set-character="setCharacter"
                  @show-info="showInfo = true"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Error Alert -->
    <div v-if="errorMessage" class="container-fluid px-3 px-md-4 mb-3">
      <div class="row justify-content-center">
        <div class="col-12 col-xxl-10">
          <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <strong>Error:</strong> {{ errorMessage }}
            <button
              type="button"
              class="btn-close"
              @click="errorMessage = null"
              aria-label="Close"
            ></button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="container-fluid px-3 px-md-4">
      <div class="row justify-content-center">
        <div class="col-12 col-xxl-10">
          <!-- Bear Visualization - Always Visible -->
          <div class="row mb-4">
            <div class="col-12">
              <BearVisualization
                :bear-state="bearState"
                :bear-image="bearImage"
                :clickable="true"
                @click-eyes="toggleEyes"
                @click-mouth="toggleMouth"
                @update-bear="updateBear"
                @set-blink-enabled="setBlinkEnabled"
                @set-volume="setVolume"
              />
            </div>
          </div>

          <!-- Control Mode -->
          <ControlMode
            :bear-state="bearState"
            :is-busy="isBusy"
            :phrases="phrases"
            @speak="speak"
            @play="play"
            @set-sync-mode="setSyncMode"
          />
        </div>
      </div>
    </div>

    <!-- Info Modal -->
    <div v-if="showInfo" class="modal show d-block" tabindex="-1" @click.self="showInfo = false">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content bg-dark text-light border-secondary">
          <div class="modal-header border-secondary">
            <h5 class="modal-title">System Info</h5>
            <button
              type="button"
              class="btn-close btn-close-white"
              @click="showInfo = false"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body p-0">
            <table class="table table-striped table-sm mb-0 info-table">
              <tbody>
                <tr>
                  <td class="fw-bold">Arduino</td>
                  <td>{{ bearState.arduino_connected ? 'Connected' : 'Disconnected' }}</td>
                </tr>
                <tr>
                  <td class="fw-bold">Connection</td>
                  <td>
                    <template v-if="bearState.arduino_connection_type === 'mock'">
                      Mock serial
                    </template>
                    <template v-else>
                      {{ bearState.arduino_port }} · {{ bearState.arduino_baud_rate }} baud
                    </template>
                  </td>
                </tr>
                <tr>
                  <td class="fw-bold">Servo Type</td>
                  <td>{{ bearState.servo_type === 'hbridge' ? 'H-Bridge (5-wire)' : 'Standard (3-wire)' }}</td>
                </tr>
                <tr>
                  <td class="fw-bold">Sync Mode</td>
                  <td>{{ bearState.sync_mode }}</td>
                </tr>
                <tr>
                  <td class="fw-bold">Phoneme</td>
                  <td>{{ bearState.phoneme_available ? 'Available' : 'Not available' }}</td>
                </tr>
                <tr>
                  <td class="fw-bold">TTS Engine</td>
                  <td>{{ bearState.tts_engine }} ({{ bearState.tts_voice }})</td>
                </tr>
                <tr>
                  <td class="fw-bold">Audio Files</td>
                  <td>{{ bearState.sound_count }} phrases loaded</td>
                </tr>
                <tr>
                  <td class="fw-bold">Platform</td>
                  <td>{{ bearState.platform === 'Darwin' ? 'macOS' : bearState.platform }}</td>
                </tr>
                <tr>
                  <td class="fw-bold">Environment</td>
                  <td>{{ bearState.environment }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showInfo" class="modal-backdrop show" @click="showInfo = false"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { State } from '@/types/bear'
import { useBear } from '@/composables/useBear'
import StatusBar from '@/components/StatusBar.vue'
import BearVisualization from '@/components/BearVisualization.vue'
import ControlMode from '@/components/ControlMode.vue'

const {
  bearState,
  phrases,
  isConnected,
  errorMessage,
  isBusy,
  bearImage,
  headerImage,
  updateBear,
  speak,
  play,
  setVolume,
  setBlinkEnabled,
  setCharacter,
  setSyncMode,
} = useBear()

// Info modal state
const showInfo = ref(false)

// Toggle functions for clicking bear image in puppet mode
const toggleEyes = () => {
  if (isBusy.value) return
  const newState = bearState.value.eyes === State.OPEN ? State.CLOSED : State.OPEN
  updateBear(newState, undefined)
}

const toggleMouth = () => {
  if (isBusy.value) return
  const newState = bearState.value.mouth === State.OPEN ? State.CLOSED : State.OPEN
  updateBear(undefined, newState)
}

// Preload all bear images to prevent stuttering
onMounted(() => {
  const positions = [0, 25, 50, 75, 100]
  const characters = ['teddy', 'grubby']
  const imagePromises: Promise<void>[] = []

  characters.forEach(character => {
    positions.forEach(eyePos => {
      positions.forEach(mouthPos => {
        const img = new Image()
        const promise = new Promise<void>((resolve, reject) => {
          img.onload = () => resolve()
          img.onerror = () => {
            // Grubby images may not exist yet, ignore errors
            console.debug(`Image not found: ${character}_e${eyePos}m${mouthPos}.png`)
            resolve()
          }
        })
        img.src = `/img/${character}_e${eyePos}m${mouthPos}.png`
        imagePromises.push(promise)
      })
    })
  })

  // Wait for all images to load
  Promise.all(imagePromises).then(() => {
    console.log('All bear images preloaded (50 images: 25 teddy + 25 grubby)')
  }).catch(err => {
    console.warn('Some bear images failed to preload:', err)
  })
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700&display=swap');

#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-image: url(/img/bg.png);
  background-size: cover;
  background-attachment: fixed;
  background-position: center;
}

/* Rounded, modern headers for all card titles */
.card-title {
  font-family: 'Nunito', 'Verdana', 'Trebuchet MS', sans-serif !important;
  color: white !important;
  font-weight: 700;
}

/* Custom very light grey background for panels */
.bg-panel {
  background-color: #bababa !important;
}

/* Override text colors for light panel background */
.bg-panel .text-muted {
  color: #000000 !important;
}

/* Info modal table styling */
.info-table {
  color: #e0e0e0;
}

.info-table td:first-child {
  width: 130px;
  white-space: nowrap;
  padding-left: 1rem;
}

.info-table td {
  padding: 0.5rem 0.75rem;
  vertical-align: middle;
}

.info-table tr:nth-child(odd) {
  background-color: rgba(255, 255, 255, 0.05);
}

.info-table tr:nth-child(even) {
  background-color: rgba(255, 255, 255, 0.02);
}
</style>

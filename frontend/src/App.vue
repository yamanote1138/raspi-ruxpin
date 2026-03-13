<template>
  <div id="app" class="min-vh-100 text-light">
    <!-- Header -->
    <header class="bg-panel py-3 mb-4">
      <div class="container-fluid px-3 px-md-4">
        <div class="row justify-content-center">
          <div class="col-12 col-xxl-10 text-center">
            <h1 class="mb-0">
              <img :src="headerImage" alt="Raspi" class="header-logo" />
            </h1>
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

    <!-- Main Content — 4-Pane Layout -->
    <div class="container-fluid px-3 px-md-4">
      <div class="row justify-content-center">
        <div class="col-12 col-xxl-10">
          <div class="row">
            <!-- Bear Image -->
            <div class="col-lg-6 mb-3">
              <div class="card bg-panel h-100">
                <BearVisualization :bear-image="bearImage" />
              </div>
            </div>

            <!-- Right Column: Controls, Phrases, TTS stacked -->
            <div class="col-lg-6 mb-3">
              <div class="card bg-panel mb-3">
                <BearControls
                  :bear-state="bearState"
                  :is-connected="isConnected"
                  @update-bear="updateBear"
                  @set-blink-enabled="setBlinkEnabled"
                  @set-volume="setVolume"
                  @set-sync-mode="setSyncMode"
                  @show-info="showInfo = true"
                />
              </div>
              <div class="card bg-panel mb-3">
                <PhrasePlayer
                  :bear-state="bearState"
                  :is-busy="isBusy"
                  :phrases="phrases"
                  @play="play"
                />
              </div>
              <div class="card bg-panel">
                <TTSControls
                  :is-busy="isBusy"
                  :bear-state="bearState"
                  @speak="speak"
                />
              </div>
            </div>
          </div>
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
                  <td class="fw-bold">Character</td>
                  <td>{{ bearState.character === 'grubby' ? 'Grubby' : 'Teddy' }}</td>
                </tr>
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
import { useBear } from '@/composables/useBear'
import BearVisualization from '@/components/BearVisualization.vue'
import BearControls from '@/components/BearControls.vue'
import PhrasePlayer from '@/components/PhrasePlayer.vue'
import TTSControls from '@/components/TTSControls.vue'

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
  setSyncMode,
} = useBear()

// Info modal state
const showInfo = ref(false)

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
  background-color: #3d2b1f;
}

header.bg-panel {
  background-color: #c4ad8f !important;
  background-image: url(/img/bg.png) !important;
  background-size: auto;
  background-repeat: repeat;
  background-position: center;
}

/* Rounded, modern headers for all card titles */
.card-title {
  font-family: 'Nunito', 'Verdana', 'Trebuchet MS', sans-serif !important;
  color: white !important;
  font-weight: 700;
}

/* Dark pink button */
.btn.btn-dark-pink {
  background-color: #e05580 !important;
  border-color: #e05580 !important;
  color: #fff !important;
}
.btn.btn-dark-pink:hover {
  background-color: #d4406a !important;
  border-color: #d4406a !important;
}
.btn.btn-dark-pink:disabled {
  background-color: #e05580 !important;
  border-color: #e05580 !important;
  opacity: 0.65;
}

/* Header logo — scale with viewport */
.header-logo {
  height: 50px;
}

@media (min-width: 576px) {
  .header-logo {
    height: 70px;
  }
}

@media (min-width: 992px) {
  .header-logo {
    height: 90px;
  }
}

/* Custom very light grey background for panels */
.bg-panel {
  background-color: #3a3a3a !important;
  border: 3px solid #c4ad8f !important;
}

/* Override text colors for light panel background */
.bg-panel .text-muted {
  color: #aaaaaa !important;
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

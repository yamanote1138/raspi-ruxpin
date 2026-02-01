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
                  <img src="/img/header_t.png" alt="Raspi" height="40" />
                </h1>
              </div>
              <div class="col-auto">
                <StatusBar
                  :is-connected="isConnected"
                  :current-mode="currentMode"
                  @set-mode="setMode"
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
                :is-busy="isBusy"
                :bear-image="bearImage"
                :clickable="currentMode === Mode.CONTROL"
                @click-eyes="toggleEyes"
                @click-mouth="toggleMouth"
                @update-bear="updateBear"
                @set-blink-enabled="setBlinkEnabled"
                @set-volume="setVolume"
              />
            </div>
          </div>

          <!-- Mode-Specific Content -->
          <ControlMode
            v-if="currentMode === Mode.CONTROL"
            :bear-state="bearState"
            :is-busy="isBusy"
            :phrases="phrases"
            @speak="speak"
            @play="play"
          />

          <ConfigMode
            v-else-if="currentMode === Mode.SYSTEM"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Mode, State } from '@/types/bear'
import { useBear } from '@/composables/useBear'
import StatusBar from '@/components/StatusBar.vue'
import BearVisualization from '@/components/BearVisualization.vue'
import ControlMode from '@/components/ControlMode.vue'
import ConfigMode from '@/components/ConfigMode.vue'

const {
  bearState,
  phrases,
  currentMode,
  isConnected,
  errorMessage,
  isBusy,
  bearImage,
  updateBear,
  speak,
  play,
  setVolume,
  setMode,
  setBlinkEnabled,
} = useBear()

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
</style>

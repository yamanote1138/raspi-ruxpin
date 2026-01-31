<template>
  <div id="app" class="min-vh-100 bg-dark text-light">
    <!-- Header -->
    <header class="bg-secondary py-3 mb-4">
      <div class="container">
        <div class="row align-items-center">
          <div class="col">
            <h1 class="mb-0">
              <img src="/img/header_t.png" alt="Raspi" height="40" class="me-2" />
              Raspi Ruxpin
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
    </header>

    <!-- Error Alert -->
    <div v-if="errorMessage" class="container mb-3">
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

    <!-- Main Content -->
    <div class="container">
      <!-- Bear Visualization - Always Visible -->
      <div class="row mb-4">
        <div class="col-12">
          <BearVisualization
            :bear-state="bearState"
            :is-busy="isBusy"
            :bear-image="bearImage"
            :clickable="currentMode === Mode.PUPPET"
            @click-eyes="toggleEyes"
            @click-mouth="toggleMouth"
          />
        </div>
      </div>

      <!-- Mode-Specific Content -->
      <PuppetMode
        v-if="currentMode === Mode.PUPPET"
        :bear-state="bearState"
        :is-busy="isBusy"
        @update-bear="updateBear"
      />

      <SpeakMode
        v-else-if="currentMode === Mode.SPEAK"
        :bear-state="bearState"
        :is-busy="isBusy"
        :phrases="phrases"
        @speak="speak"
        @play="play"
        @set-volume="setVolume"
      />

      <ConfigMode
        v-else
        :bear-state="bearState"
        @set-blink-enabled="setBlinkEnabled"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Mode, State } from '@/types/bear'
import { useBear } from '@/composables/useBear'
import StatusBar from '@/components/StatusBar.vue'
import BearVisualization from '@/components/BearVisualization.vue'
import PuppetMode from '@/components/PuppetMode.vue'
import SpeakMode from '@/components/SpeakMode.vue'
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

<style scoped>
#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-image: url(/img/bg.png);
  background-size: cover;
  background-attachment: fixed;
  background-position: center;
}
</style>

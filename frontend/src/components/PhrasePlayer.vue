<template>
  <div class="phrase-player">
    <div class="card-body">
      <!-- Phrase Selection -->
      <div class="mb-3">
        <select
          id="phrase-select"
          v-model="selectedPhrase"
          class="form-select bg-dark text-light"
          :disabled="isBusy"
        >
          <option value="">-- Choose a phrase --</option>
          <option
            v-for="(description, key) in sortedPhrases"
            :key="key"
            :value="key"
          >
            {{ description }}
          </option>
        </select>
      </div>

      <!-- Button Row -->
      <div class="btn-group w-100" role="group">
        <button
          type="button"
          class="btn btn-primary"
          :disabled="isBusy || phraseKeys.length === 0"
          @click="selectRandom"
          title="Select a random phrase"
        >
          <i class="bi bi-shuffle"></i>
          Random
        </button>
        <button
          type="button"
          class="btn btn-success flex-grow-1"
          :disabled="isBusy || !selectedPhrase"
          @click="handlePlay"
        >
          <span v-if="isBusy">
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            {{ bearState.status_text || 'Playing...' }}
          </span>
          <span v-else>
            <i class="bi bi-play-fill me-2"></i>
            Play Phrase
          </span>
        </button>
      </div>

      <!-- Warning if no phrases -->
      <div v-if="Object.keys(phrases).length === 0" class="alert alert-warning mb-0 mt-3">
        No phrases loaded. Check your configuration.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { BearState } from '@/types/bear'
import type { Phrases } from '@/types/websocket'

const props = defineProps<{
  bearState: BearState
  isBusy: boolean
  phrases: Phrases
}>()

const emit = defineEmits<{
  play: [sound: string]
}>()

const selectedPhrase = ref('')

const sortedPhrases = computed(() => {
  const entries = Object.entries(props.phrases)
  entries.sort((a, b) => a[1].localeCompare(b[1]))
  return Object.fromEntries(entries)
})

const phraseKeys = computed(() => Object.keys(props.phrases))

const selectRandom = () => {
  if (phraseKeys.value.length === 0) return
  let key: string
  do {
    key = phraseKeys.value[Math.floor(Math.random() * phraseKeys.value.length)]
  } while (key === selectedPhrase.value && phraseKeys.value.length > 1)
  selectedPhrase.value = key
}

const handlePlay = async () => {
  if (!selectedPhrase.value) return
  try {
    await emit('play', selectedPhrase.value)
  } catch (error) {
    console.error('Play error:', error)
  }
}
</script>

<style scoped>
.form-select:focus {
  background-color: #343a40;
  color: #f8f9fa;
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}
</style>

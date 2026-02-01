<template>
  <div class="control-mode">
    <div class="row">
      <!-- Phrases -->
      <div class="col-lg-6 mb-4">
        <div class="card bg-panel">
          <div class="card-body">
            <!-- Phrase Selection -->
            <div class="mb-3">
              <div v-if="Object.keys(phrases).length > 0" class="mb-2">
                <small class="text-muted">
                  {{ Object.keys(phrases).length }} phrases available
                </small>
              </div>
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

            <!-- Play Button -->
            <button
              type="button"
              class="btn btn-success w-100"
              :disabled="isBusy || !selectedPhrase"
              @click="handlePlay"
            >
              <span v-if="isBusy">
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                Playing...
              </span>
              <span v-else>
                <i class="bi bi-play-fill me-2"></i>
                Play Phrase
              </span>
            </button>

            <!-- Warning if no phrases -->
            <div v-if="Object.keys(phrases).length === 0" class="alert alert-warning mb-0 mt-3">
              No phrases loaded. Check your configuration.
            </div>
          </div>
        </div>
      </div>

      <!-- Text-to-Speech -->
      <div class="col-lg-6 mb-4">
        <div class="card bg-panel">
          <div class="card-body">
            <!-- Text Input with Button Bar -->
            <div class="mb-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <label for="tts-text" class="form-label mb-0">Enter Text</label>
                <div class="btn-group" role="group">
                  <button
                    type="button"
                    class="btn btn-sm btn-light"
                    :disabled="isBusy"
                    @click="loadRandomPhrase"
                    title="Load random example phrase"
                  >
                    Random
                  </button>
                  <button
                    type="button"
                    class="btn btn-sm btn-light"
                    :disabled="isBusy || !ttsText.trim()"
                    @click="clearText"
                    title="Clear text"
                  >
                    Clear
                  </button>
                </div>
              </div>
              <textarea
                id="tts-text"
                v-model="ttsText"
                class="form-control bg-dark text-light"
                rows="2"
                placeholder="Type something for the bear to say..."
                :disabled="isBusy"
                maxlength="500"
                @keydown.enter="handleKeyDown"
              ></textarea>
              <div class="form-text text-dark">
                {{ ttsText.length }} / 500 characters (Shift+Enter for new line)
              </div>
            </div>

            <!-- Speak Button -->
            <button
              type="button"
              class="btn btn-primary w-100"
              :disabled="isBusy || !ttsText.trim()"
              @click="handleSpeak"
            >
              <span v-if="isBusy">
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                Speaking...
              </span>
              <span v-else>
                <i class="bi bi-mic-fill me-2"></i>
                Speak
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { BearState } from '@/types/bear'
import type { Phrases } from '@/types/websocket'

const props = defineProps<{
  bearState: BearState
  isBusy: boolean
  phrases: Phrases
}>()

const emit = defineEmits<{
  speak: [text: string]
  play: [sound: string]
}>()

// Example phrases for TTS
const examplePhrases = [
  "Hello! I'm Teddy Ruxpin, and I love telling stories!",
  "Did you know that I'm the world's first animated talking toy?",
  "Let's go on an adventure together through the magical land of Grundo!",
  "I've got tales of friendship, courage, and wonder to share with you!",
  "My friends Newton Gimmick and Grubby are the best companions anyone could ask for!"
]

// State
const ttsText = ref('')
const selectedPhrase = ref('')
const lastRandomIndex = ref(-1)

// Computed
const sortedPhrases = computed(() => {
  const entries = Object.entries(props.phrases)
  entries.sort((a, b) => a[1].localeCompare(b[1]))
  return Object.fromEntries(entries)
})

const handleKeyDown = (event: KeyboardEvent) => {
  // If Enter is pressed without Shift, submit the form
  if (!event.shiftKey) {
    event.preventDefault()
    handleSpeak()
  }
  // If Shift+Enter, allow default behavior (new line)
}

const handleSpeak = async () => {
  if (!ttsText.value.trim()) return

  try {
    await emit('speak', ttsText.value)
    // Don't clear text automatically - let user decide
  } catch (error) {
    console.error('Speak error:', error)
  }
}

const handlePlay = async () => {
  if (!selectedPhrase.value) return

  try {
    await emit('play', selectedPhrase.value)
  } catch (error) {
    console.error('Play error:', error)
  }
}

const loadRandomPhrase = () => {
  // Get a random phrase that's different from the last one
  let randomIndex: number
  do {
    randomIndex = Math.floor(Math.random() * examplePhrases.length)
  } while (randomIndex === lastRandomIndex.value && examplePhrases.length > 1)

  lastRandomIndex.value = randomIndex
  ttsText.value = examplePhrases[randomIndex]
}

const clearText = () => {
  ttsText.value = ''
}

// Load a random phrase on mount
onMounted(() => {
  loadRandomPhrase()
})
</script>

<style scoped>
.form-control:focus,
.form-select:focus {
  background-color: #343a40;
  color: #f8f9fa;
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}
</style>

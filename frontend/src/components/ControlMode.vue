<template>
  <div class="control-mode">
    <div class="row">
      <!-- Text-to-Speech -->
      <div class="col-lg-6 mb-4">
        <div class="card bg-secondary">
          <div class="card-body">
            <h5 class="card-title mb-3">Text-to-Speech</h5>

            <!-- Text Input -->
            <div class="mb-3">
              <label for="tts-text" class="form-label">Enter Text</label>
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
              <div class="form-text">
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

      <!-- Phrases -->
      <div class="col-lg-6 mb-4">
        <div class="card bg-secondary">
          <div class="card-body">
            <h5 class="card-title mb-3">Phrase Library</h5>

            <!-- Phrase Selection -->
            <div class="mb-3">
              <label for="phrase-select" class="form-label">Select a Phrase</label>
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
              class="btn btn-success w-100 mb-3"
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

            <!-- Phrase Info -->
            <div v-if="Object.keys(phrases).length > 0">
              <small class="text-muted">
                {{ Object.keys(phrases).length }} phrases available
              </small>
            </div>
            <div v-else>
              <div class="alert alert-warning mb-0">
                No phrases loaded. Check your configuration.
              </div>
            </div>
          </div>
        </div>
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
  speak: [text: string]
  play: [sound: string]
}>()

// State
const ttsText = ref('')
const selectedPhrase = ref('')

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

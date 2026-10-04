<template>
  <div class="tts-controls">
    <div class="card-body">
      <!-- Text Input -->
      <div class="mb-3">
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
        <div class="form-text text-muted">
          {{ ttsText.length }} / 500 characters (Shift+Enter for new line)
        </div>
      </div>

      <!-- Button Row -->
      <div class="btn-group w-100" role="group">
        <button
          type="button"
          class="btn btn-primary"
          :disabled="isBusy"
          @click="loadRandomPhrase"
          title="Load random example phrase"
        >
          <i class="bi bi-shuffle"></i>
          Random
        </button>
        <button
          type="button"
          class="btn btn-dark-pink"
          :disabled="isBusy || !ttsText.trim()"
          @click="clearText"
          title="Clear text"
        >
          <i class="bi bi-eraser"></i>
          Clear
        </button>
        <button
          type="button"
          class="btn btn-success flex-grow-1"
          :disabled="isBusy || !ttsText.trim()"
          @click="handleSpeak"
        >
          <span v-if="isBusy">
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            {{ bearState.status_text || 'Speaking...' }}
          </span>
          <span v-else>
            <i class="bi bi-mic-fill me-2"></i>
            Speak
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { BearState } from '@/types/bear'

const props = defineProps<{
  isBusy: boolean
  bearState: BearState
}>()

const emit = defineEmits<{
  speak: [text: string]
}>()

const examplePhrases = [
  "Hello! I'm Teddy Ruxpin, and I love telling stories!",
  "Did you know that I'm the world's first animated talking toy?",
  "Let's go on an adventure together through the magical land of Grundo!",
  "I've got tales of friendship, courage, and wonder to share with you!",
  "My friends Newton Gimmick and Grubby are the best companions anyone could ask for!"
]

const ttsText = ref('')
const lastRandomIndex = ref(-1)

const handleKeyDown = (event: KeyboardEvent) => {
  if (!event.shiftKey) {
    event.preventDefault()
    handleSpeak()
  }
}

const handleSpeak = async () => {
  if (!ttsText.value.trim()) return
  try {
    await emit('speak', ttsText.value)
  } catch (error) {
    console.error('Speak error:', error)
  }
}

const loadRandomPhrase = () => {
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

onMounted(() => {
  loadRandomPhrase()
})
</script>

<style scoped>
.form-control:focus {
  background-color: #343a40;
  color: #f8f9fa;
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}
</style>

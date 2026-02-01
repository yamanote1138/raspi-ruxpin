<template>
  <div class="gpio-status card bg-panel mb-3">
    <div class="card-body">
      <h5 class="card-title mb-3 text-dark">GPIO Status</h5>

      <!-- GPIO Pin Status Button Bar -->
      <div class="btn-group" role="group">
        <button
          v-for="pin in gpioPins"
          :key="pin.number"
          type="button"
          class="btn btn-sm gpio-pin-btn"
          :class="pin.state ? 'btn-success' : 'btn-danger'"
          :title="`${pin.name} - ${pin.state ? 'HIGH' : 'LOW'}`"
        >
          <span class="d-none d-md-inline">{{ pin.number }}: {{ pin.name }}</span>
          <span class="d-md-none">{{ pin.number }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'

const ws = useWebSocket()

interface GPIOPin {
  number: number
  name: string
  label: string
  state: boolean  // true = HIGH, false = LOW
}

// GPIO pins based on hardware configuration
const gpioPins = ref<GPIOPin[]>([
  { number: 21, name: 'Eyes PWM', label: 'Eyes PWM control pin', state: false },
  { number: 16, name: 'Eyes DIR', label: 'Eyes direction pin', state: false },
  { number: 20, name: 'Eyes CDIR', label: 'Eyes counter-direction pin', state: false },
  { number: 25, name: 'Mouth PWM', label: 'Mouth PWM control pin', state: false },
  { number: 7, name: 'Mouth DIR', label: 'Mouth direction pin', state: false },
  { number: 8, name: 'Mouth CDIR', label: 'Mouth counter-direction pin', state: false },
])

// Watch for GPIO status updates from WebSocket
onMounted(() => {
  ws.on('gpio_status', (data: { pins: Record<number, boolean> }) => {
    // Update pin status based on backend data
    gpioPins.value.forEach(pin => {
      if (pin.number in data.pins) {
        pin.state = data.pins[pin.number]
      }
    })
  })

  // Request initial GPIO status
  ws.send({
    type: 'get_gpio_status',
  })
})
</script>

<style scoped>
.gpio-status .btn {
  min-width: auto;
}

/* Make GPIO buttons non-interactive but still show tooltips */
.gpio-pin-btn {
  pointer-events: auto;
  cursor: default;
  opacity: 1;
}

/* On medium and larger screens, make buttons wider for full text */
@media (min-width: 768px) {
  .gpio-status .btn {
    min-width: 120px;
  }
}
</style>

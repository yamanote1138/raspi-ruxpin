<template>
  <div class="bear-visualization-panel">
    <div class="bear-container">
      <img
        :key="bearImage"
        :src="bearImage"
        alt="Bear"
        class="bear-image"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  bearImage: string
}>()
</script>

<style scoped>
.bear-container {
  width: 100%;
  aspect-ratio: 1 / 1;
  position: relative;
}

.bear-image {
  transition: none !important;
  animation: none !important;
  image-rendering: pixelated;
  backface-visibility: hidden;
  transform: translateZ(0);
  -webkit-font-smoothing: antialiased;
  opacity: 1 !important;
  filter: none !important;
  object-fit: contain;
  display: block;
  position: absolute;
  top: 8%;
  left: 8%;
  width: 84%;
  height: 84%;
}
</style>

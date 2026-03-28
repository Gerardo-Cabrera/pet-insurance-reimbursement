<script setup>
import { computed } from "vue";

const props = defineProps({
  count: { type: Number, required: true },
  pageSize: { type: Number, default: 10 },
  currentPage: { type: Number, required: true },
});

const emit = defineEmits(["update:currentPage"]);

const totalPages = computed(() => Math.max(1, Math.ceil(props.count / props.pageSize)));

const hasPrev = computed(() => props.currentPage > 1);
const hasNext = computed(() => props.currentPage < totalPages.value);

function goTo(page) {
  if (page >= 1 && page <= totalPages.value) {
    emit("update:currentPage", page);
  }
}
</script>

<template>
  <div v-if="totalPages > 1" class="pagination-bar">
    <button
      class="ghost-button"
      type="button"
      :disabled="!hasPrev"
      @click="goTo(currentPage - 1)"
    >
      Previous
    </button>
    <span class="pagination-info">Page {{ currentPage }} of {{ totalPages }}</span>
    <button
      class="ghost-button"
      type="button"
      :disabled="!hasNext"
      @click="goTo(currentPage + 1)"
    >
      Next
    </button>
  </div>
</template>

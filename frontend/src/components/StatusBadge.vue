<script setup>
import { computed } from "vue";

const props = defineProps({
  status: {
    type: String,
    required: true,
  },
});

const className = computed(() => {
  return {
    PROCESSING: "amber",
    IN_REVIEW: "blue",
    APPROVED: "green",
    REJECTED: "red",
    SUBMITTED: "slate",
  }[props.status] || "slate";
});
</script>

<template>
  <span class="status-badge" :class="className">{{ status.replaceAll("_", " ") }}</span>
</template>

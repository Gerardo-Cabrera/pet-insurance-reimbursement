<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";

import api from "../api";
import PaginationBar from "../components/PaginationBar.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { useAuthStore } from "../store";

const auth = useAuthStore();
const claims = ref([]);
const totalCount = ref(0);
const currentPage = ref(1);
const pets = ref([]);
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const form = reactive({
  pet: "",
  invoice: null,
  invoice_date: "",
  date_of_event: "",
  amount: "",
});
let refreshTimer = null;

const statusMetrics = computed(() => [
  {
    label: "Total claims",
    value: totalCount.value,
  },
  {
    label: "Processing",
    value: claims.value.filter((claim) => claim.status === "PROCESSING").length,
  },
  {
    label: "In review",
    value: claims.value.filter((claim) => claim.status === "IN_REVIEW").length,
  },
  {
    label: "Closed",
    value: claims.value.filter((claim) =>
      ["APPROVED", "REJECTED"].includes(claim.status),
    ).length,
  },
]);

async function loadClaims() {
  loading.value = true;
  try {
    const { data } = await api.get("/claims/", { params: { page: currentPage.value } });
    claims.value = data.results;
    totalCount.value = data.count;
  } catch (error) {
    errorMessage.value = "Unable to load claims.";
  } finally {
    loading.value = false;
  }
}

watch(currentPage, loadClaims);

async function loadPets() {
  if (!auth.canManagePets.value) {
    return;
  }
  const { data } = await api.get("/pets/");
  pets.value = data.results;
  if (!form.pet && pets.value.length > 0) {
    form.pet = pets.value[0].id;
  }
}

async function createClaim() {
  saving.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const payload = new FormData();
    payload.append("pet", form.pet);
    payload.append("invoice", form.invoice);
    payload.append("invoice_date", form.invoice_date);
    payload.append("date_of_event", form.date_of_event);
    payload.append("amount", form.amount);

    const { data } = await api.post("/claims/", payload, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    successMessage.value =
      data.status === "PROCESSING"
        ? "Claim queued and waiting for automatic validation."
        : "Claim submitted successfully.";

    Object.assign(form, {
      pet: pets.value[0]?.id || "",
      invoice: null,
      invoice_date: "",
      date_of_event: "",
      amount: "",
    });
    currentPage.value = 1;
    await loadClaims();
  } catch (error) {
    errorMessage.value =
      error.response?.data?.invoice?.[0] ||
      error.response?.data?.pet?.[0] ||
      error.response?.data?.detail ||
      "Unable to create the claim.";
  } finally {
    saving.value = false;
  }
}

function startPolling() {
  refreshTimer = window.setInterval(loadClaims, 5000);
}

function stopPolling() {
  if (refreshTimer) {
    window.clearInterval(refreshTimer);
    refreshTimer = null;
  }
}

onMounted(async () => {
  await Promise.all([loadClaims(), loadPets()]);
  startPolling();
});

onUnmounted(stopPolling);
</script>

<template>
  <section class="stack-grid">
    <article class="hero-panel">
      <div>
        <p class="eyebrow">Claims</p>
        <h2>Reimbursement flow at a glance</h2>
        <p class="muted">
          Claims enter processing first, then move to review or automatic rejection once validation finishes.
        </p>
      </div>
      <div class="stat-grid">
        <article v-for="metric in statusMetrics" :key="metric.label" class="stat-card">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
        </article>
      </div>
    </article>

    <article class="panel panel-stack">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Submission</p>
          <h2>Submit reimbursement requests</h2>
          <p class="muted">Create a claim, upload the invoice and track each transition from the same screen.</p>
        </div>
      </div>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success-text">{{ successMessage }}</p>

      <div v-if="auth.canManagePets.value && !pets.length" class="empty-state">
        <strong>No eligible pets yet</strong>
        <p class="muted">Create at least one pet first so a reimbursement claim can be attached to it.</p>
      </div>

      <form
        v-if="auth.canManagePets.value && pets.length"
        class="form-grid two-columns"
        @submit.prevent="createClaim"
      >
        <label>
          <span>Pet</span>
          <select v-model="form.pet" required>
            <option v-for="pet in pets" :key="pet.id" :value="pet.id">{{ pet.name }}</option>
          </select>
        </label>

        <label>
          <span>Amount</span>
          <input v-model="form.amount" type="number" step="0.01" min="0.01" required />
        </label>

        <label>
          <span>Invoice date</span>
          <input v-model="form.invoice_date" type="date" required />
        </label>

        <label>
          <span>Date of event</span>
          <input v-model="form.date_of_event" type="date" required />
        </label>

        <label class="full-span">
          <span>Invoice file</span>
          <input type="file" accept=".pdf,.png,.jpg,.jpeg" required @change="form.invoice = $event.target.files?.[0] || null" />
        </label>

        <button class="primary-button" type="submit" :disabled="saving || !form.invoice">
          {{ saving ? "Submitting..." : "Create claim" }}
        </button>
      </form>
    </article>

    <article class="panel panel-stack">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Timeline</p>
          <h2>Claim history</h2>
        </div>
      </div>

      <div v-if="loading" class="muted">Loading claims...</div>

      <div v-else-if="claims.length === 0" class="empty-state">
        <strong>No claims yet</strong>
        <p class="muted">Once a claim is created, its status updates will appear here automatically.</p>
      </div>

      <div v-else class="card-list">
        <article v-for="claim in claims" :key="claim.id" class="data-card">
          <div class="card-header">
            <div>
              <h3>{{ claim.pet_name }}</h3>
              <p class="muted">{{ claim.owner_email }}</p>
            </div>
            <StatusBadge :status="claim.status" />
          </div>
          <p>Amount: ${{ claim.amount }}</p>
          <p>Invoice date: {{ claim.invoice_date }}</p>
          <p>Event date: {{ claim.date_of_event }}</p>
          <p v-if="claim.processing_summary" class="muted">{{ claim.processing_summary }}</p>
          <p v-if="claim.review_notes"><strong>Notes:</strong> {{ claim.review_notes }}</p>
        </article>
      </div>

      <PaginationBar
        :count="totalCount"
        :current-page="currentPage"
        @update:current-page="currentPage = $event"
      />
    </article>
  </section>
</template>

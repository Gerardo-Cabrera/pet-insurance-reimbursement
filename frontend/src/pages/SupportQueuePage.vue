<script setup>
import { onMounted, reactive, ref } from "vue";

import api from "../api";
import StatusBadge from "../components/StatusBadge.vue";

const claims = ref([]);
const notes = reactive({});
const loading = ref(false);
const busyId = ref(null);
const errorMessage = ref("");

async function loadClaims() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const { data } = await api.get("/claims/", {
      params: { status: "IN_REVIEW" },
    });
    claims.value = data.results;
  } catch (error) {
    errorMessage.value = "Unable to load support queue.";
  } finally {
    loading.value = false;
  }
}

async function submitDecision(claimId, action) {
  busyId.value = claimId;
  errorMessage.value = "";
  try {
    await api.post(`/claims/${claimId}/${action}/`, {
      review_notes: notes[claimId] || "",
    });
    notes[claimId] = "";
    await loadClaims();
  } catch (error) {
    errorMessage.value =
      error.response?.data?.detail || "Unable to update the claim.";
  } finally {
    busyId.value = null;
  }
}

onMounted(loadClaims);
</script>

<template>
  <section class="stack-grid">
    <article class="hero-panel">
      <div>
        <p class="eyebrow">Support</p>
        <h2>Decision queue</h2>
        <p class="muted">
          Review only the claims that already passed automatic validation and are waiting for a human decision.
        </p>
      </div>
      <div class="stat-grid">
        <article class="stat-card">
          <span>Pending review</span>
          <strong>{{ claims.length }}</strong>
        </article>
      </div>
    </article>

    <article class="panel panel-stack">
      <div class="section-heading">
        <div>
          <h2>Review queue</h2>
          <p class="muted">Approve or reject claims once they complete automatic validation.</p>
        </div>
      </div>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-if="loading" class="muted">Loading queue...</p>

      <div v-else-if="claims.length === 0" class="empty-state">
        <strong>Nothing waiting right now</strong>
        <p class="muted">As soon as a claim reaches `IN_REVIEW`, it will appear here.</p>
      </div>

      <div v-else class="card-list">
        <article v-for="claim in claims" :key="claim.id" class="data-card support-card">
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
          <p class="muted">{{ claim.processing_summary }}</p>

          <label>
            <span>Review notes</span>
            <textarea v-model="notes[claim.id]" rows="4" placeholder="Explain the decision if needed." />
          </label>

          <div class="button-row">
            <button
              class="primary-button"
              type="button"
              :disabled="busyId === claim.id"
              @click="submitDecision(claim.id, 'approve')"
            >
              Approve
            </button>
            <button
              class="danger-button"
              type="button"
              :disabled="busyId === claim.id"
              @click="submitDecision(claim.id, 'reject')"
            >
              Reject
            </button>
          </div>
        </article>
      </div>
    </article>
  </section>
</template>

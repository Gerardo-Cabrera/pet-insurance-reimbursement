<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";

import api from "../api";
import PaginationBar from "../components/PaginationBar.vue";
import { useAuthStore } from "../store";

const auth = useAuthStore();
const pets = ref([]);
const totalCount = ref(0);
const currentPage = ref(1);
const loading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const saving = ref(false);
const deletingId = ref(null);
const editingId = ref(null);
const form = reactive({
  name: "",
  species: "DOG",
  birth_date: "",
  coverage_start: "",
});

const metrics = computed(() => [
  {
    label: "Registered pets",
    value: pets.value.length,
  },
  {
    label: "Protected by history",
    value: pets.value.filter((pet) => pet.claim_count > 0).length,
  },
  {
    label: "Editable today",
    value: pets.value.filter((pet) => pet.claim_count === 0).length,
  },
]);

const formTitle = computed(() =>
  editingId.value ? "Update pet profile" : "Create a new insured pet",
);
const formButtonLabel = computed(() =>
  editingId.value ? "Save changes" : "Add pet",
);

async function loadPets() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const { data } = await api.get("/pets/", { params: { page: currentPage.value } });
    pets.value = data.results;
    totalCount.value = data.count;
  } catch (error) {
    errorMessage.value = "Unable to load pets.";
  } finally {
    loading.value = false;
  }
}

watch(currentPage, loadPets);

function resetForm() {
  editingId.value = null;
  Object.assign(form, {
    name: "",
    species: "DOG",
    birth_date: "",
    coverage_start: "",
  });
}

function beginEdit(pet) {
  editingId.value = pet.id;
  successMessage.value = "";
  errorMessage.value = "";
  Object.assign(form, {
    name: pet.name,
    species: pet.species,
    birth_date: pet.birth_date,
    coverage_start: pet.coverage_start,
  });
}

async function submitPet() {
  saving.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    if (editingId.value) {
      await api.put(`/pets/${editingId.value}/`, form);
      successMessage.value = "Pet updated successfully.";
    } else {
      await api.post("/pets/", form);
      successMessage.value = "Pet created successfully.";
    }
    resetForm();
    currentPage.value = 1;
    await loadPets();
  } catch (error) {
    errorMessage.value =
      error.response?.data?.detail || "Unable to save the pet.";
  } finally {
    saving.value = false;
  }
}

async function deletePet(pet) {
  if (
    !window.confirm(
      `Delete ${pet.name}? This is only allowed for pets without claim history.`,
    )
  ) {
    return;
  }

  deletingId.value = pet.id;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    await api.delete(`/pets/${pet.id}/`);
    successMessage.value = "Pet deleted successfully.";
    if (editingId.value === pet.id) {
      resetForm();
    }
    await loadPets();
  } catch (error) {
    errorMessage.value =
      error.response?.data?.detail || "Unable to delete the pet.";
  } finally {
    deletingId.value = null;
  }
}

onMounted(loadPets);
</script>

<template>
  <section class="stack-grid">
    <article class="hero-panel">
      <div>
        <p class="eyebrow">Pets</p>
        <h2>Coverage-ready pet registry</h2>
        <p class="muted">
          Keep the insured roster clean, editable and safe from accidental claim-history loss.
        </p>
      </div>
      <div class="stat-grid">
        <article v-for="metric in metrics" :key="metric.label" class="stat-card">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
        </article>
      </div>
    </article>

    <div class="dashboard-grid">
      <article class="panel panel-stack">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Editor</p>
            <h2>{{ formTitle }}</h2>
          </div>
          <button
            v-if="editingId"
            class="ghost-button"
            type="button"
            @click="resetForm"
          >
            Cancel edit
          </button>
        </div>

        <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
        <p v-if="successMessage" class="success-text">{{ successMessage }}</p>

        <form
          v-if="auth.canManagePets.value"
          class="form-grid two-columns"
          @submit.prevent="submitPet"
        >
          <label>
            <span>Name</span>
            <input v-model="form.name" type="text" required />
          </label>

          <label>
            <span>Species</span>
            <select v-model="form.species">
              <option value="DOG">Dog</option>
              <option value="CAT">Cat</option>
              <option value="OTHER">Other</option>
            </select>
          </label>

          <label>
            <span>Birth date</span>
            <input v-model="form.birth_date" type="date" required />
          </label>

          <label>
            <span>Coverage start</span>
            <input v-model="form.coverage_start" type="date" required />
          </label>

          <button class="primary-button" type="submit" :disabled="saving">
            {{ saving ? "Saving..." : formButtonLabel }}
          </button>
        </form>

        <p v-else class="muted">
          Support users can inspect the registry but only customer/admin users can modify it.
        </p>
      </article>

      <article class="panel panel-stack">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Registry</p>
            <h2>Insured pets</h2>
          </div>
        </div>

        <div v-if="loading" class="muted">Loading pets...</div>

        <div v-else-if="pets.length === 0" class="empty-state">
          <strong>No pets yet</strong>
          <p class="muted">Create the first pet record to start submitting reimbursement claims.</p>
        </div>

        <div v-else class="card-list">
          <article v-for="pet in pets" :key="pet.id" class="data-card">
            <div class="card-header">
              <div>
                <h3>{{ pet.name }}</h3>
                <p class="muted">{{ pet.owner_email }}</p>
              </div>
              <div class="chip-row">
                <span class="mini-tag">{{ pet.species }}</span>
                <span class="mini-tag subtle-tag">{{ pet.claim_count }} claims</span>
              </div>
            </div>

            <div class="data-meta">
              <p><strong>Birth date:</strong> {{ pet.birth_date }}</p>
              <p><strong>Coverage:</strong> {{ pet.coverage_start }} to {{ pet.coverage_end }}</p>
            </div>

            <div v-if="auth.canManagePets.value" class="button-row">
              <button class="ghost-button" type="button" @click="beginEdit(pet)">
                Edit
              </button>
              <button
                class="danger-button"
                type="button"
                :disabled="pet.claim_count > 0 || deletingId === pet.id"
                @click="deletePet(pet)"
              >
                {{
                  pet.claim_count > 0
                    ? "Protected"
                    : deletingId === pet.id
                      ? "Deleting..."
                      : "Delete"
                }}
              </button>
            </div>

            <p v-if="pet.claim_count > 0" class="helper-text">
              This pet cannot be deleted because it already has claim history.
            </p>
          </article>
        </div>

        <PaginationBar
          :count="totalCount"
          :current-page="currentPage"
          @update:current-page="currentPage = $event"
        />
      </article>
    </div>
  </section>
</template>

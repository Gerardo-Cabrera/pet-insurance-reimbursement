<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "../store";

const auth = useAuthStore();
const router = useRouter();
const errorMessage = ref("");
const submitting = ref(false);
const form = reactive({
  first_name: "",
  last_name: "",
  email: "",
  password: "",
});

async function handleSubmit() {
  submitting.value = true;
  errorMessage.value = "";

  try {
    await auth.register(form);
    await router.push("/claims");
  } catch (error) {
    errorMessage.value =
      error.response?.data?.email?.[0] ||
      error.response?.data?.detail ||
      "Unable to create the account.";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <section class="panel auth-panel">
    <div>
      <p class="eyebrow">Registration</p>
      <h2>Create your customer account</h2>
      <p class="muted">New accounts are created as CUSTOMER users by default.</p>
    </div>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label>
        <span>First name</span>
        <input v-model="form.first_name" type="text" />
      </label>

      <label>
        <span>Last name</span>
        <input v-model="form.last_name" type="text" />
      </label>

      <label>
        <span>Email</span>
        <input v-model="form.email" type="email" required />
      </label>

      <label>
        <span>Password</span>
        <input v-model="form.password" type="password" minlength="8" required />
      </label>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

      <button class="primary-button" type="submit" :disabled="submitting">
        {{ submitting ? "Creating..." : "Register" }}
      </button>
    </form>

    <RouterLink class="inline-link" to="/login">Already have an account?</RouterLink>
  </section>
</template>

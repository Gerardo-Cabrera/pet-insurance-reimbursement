<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "../store";

const auth = useAuthStore();
const router = useRouter();
const errorMessage = ref("");
const submitting = ref(false);
const form = reactive({
  email: "",
  password: "",
});

async function handleSubmit() {
  submitting.value = true;
  errorMessage.value = "";

  try {
    await auth.login(form);
    await router.push(auth.isSupport.value ? "/support" : "/claims");
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || "Unable to login.";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <section class="panel auth-panel">
    <div>
      <p class="eyebrow">Access</p>
      <h2>Welcome back</h2>
      <p class="muted">Use your email and password to manage pets and reimbursement claims.</p>
    </div>

    <form class="form-grid" @submit.prevent="handleSubmit">
      <label>
        <span>Email</span>
        <input v-model="form.email" type="email" required />
      </label>

      <label>
        <span>Password</span>
        <input v-model="form.password" type="password" required />
      </label>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

      <button class="primary-button" type="submit" :disabled="submitting">
        {{ submitting ? "Signing in..." : "Login" }}
      </button>
    </form>

    <RouterLink class="inline-link" to="/register">Create an account</RouterLink>
  </section>
</template>

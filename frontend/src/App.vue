<script setup>
import { computed } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";

import { useAuthStore } from "./store";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const navigation = computed(() => {
  if (!auth.state.user) {
    return [];
  }

  const items = [
    { label: "Claims", to: "/claims" },
    { label: "Pets", to: "/pets" },
  ];

  if (auth.isSupport.value) {
    items.push({ label: "Support Queue", to: "/support" });
  }

  return items;
});

async function handleLogout() {
  auth.logout();
  await router.push("/login");
}
</script>

<template>
  <div class="page-shell">
    <header class="app-header">
      <div class="header-copy">
        <p class="eyebrow">Pet Insurance Reimbursement</p>
        <h1>Claims that move with clarity.</h1>
        <p class="header-description">
          Register pets, submit reimbursements and keep support decisions visible from the
          same operational workspace.
        </p>
      </div>
      <div v-if="auth.state.user" class="user-chip">
        <span>{{ auth.state.user.email }}</span>
        <strong>{{ auth.state.user.role }}</strong>
      </div>
    </header>

    <nav v-if="auth.state.user" class="app-nav">
      <RouterLink
        v-for="item in navigation"
        :key="item.to"
        :to="item.to"
        class="nav-link"
        :class="{ active: route.path === item.to }"
      >
        {{ item.label }}
      </RouterLink>
      <button class="ghost-button" type="button" @click="handleLogout">Logout</button>
    </nav>

    <main class="content-grid">
      <RouterView />
    </main>
  </div>
</template>

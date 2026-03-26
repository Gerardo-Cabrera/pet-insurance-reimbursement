import { createRouter, createWebHistory } from "vue-router";

import ClaimsPage from "../pages/ClaimsPage.vue";
import LoginPage from "../pages/LoginPage.vue";
import PetsPage from "../pages/PetsPage.vue";
import RegisterPage from "../pages/RegisterPage.vue";
import SupportQueuePage from "../pages/SupportQueuePage.vue";
import { useAuthStore } from "../store";

const routes = [
  {
    path: "/",
    redirect: "/claims",
  },
  {
    path: "/login",
    name: "login",
    component: LoginPage,
    meta: { guestOnly: true },
  },
  {
    path: "/register",
    name: "register",
    component: RegisterPage,
    meta: { guestOnly: true },
  },
  {
    path: "/pets",
    name: "pets",
    component: PetsPage,
    meta: { requiresAuth: true },
  },
  {
    path: "/claims",
    name: "claims",
    component: ClaimsPage,
    meta: { requiresAuth: true },
  },
  {
    path: "/support",
    name: "support",
    component: SupportQueuePage,
    meta: { requiresAuth: true, roles: ["SUPPORT", "ADMIN"] },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  const hasSession = Boolean(auth.state.accessToken);

  if (to.meta.requiresAuth && !hasSession) {
    return { name: "login" };
  }

  if (to.meta.guestOnly && hasSession) {
    return auth.isSupport.value ? { name: "support" } : { name: "claims" };
  }

  if (to.meta.roles && !to.meta.roles.includes(auth.state.user?.role)) {
    return { name: "claims" };
  }

  return true;
});

export default router;

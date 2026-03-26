import { createApp } from "vue";

import App from "./App.vue";
import router from "./router";
import { hydrateSession } from "./store";
import "./styles.css";

async function bootstrap() {
  await hydrateSession();
  createApp(App).use(router).mount("#app");
}

bootstrap();

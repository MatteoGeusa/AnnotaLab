import { createRouter, createWebHistory } from "vue-router";
import LoginView from "./views/LoginView.vue";
import ConsentView from "./views/ConsentView.vue";
import ScreeningView from "./views/ScreeningView.vue";
import InstructionsView from "./views/InstructionsView.vue";
import AnnotatorView from "./views/AnnotatorView.vue";
import ConsentFullPage from "./views/ConsensFullPage.vue";

const routes = [
  { path: "/", component: LoginView },
  { path: "/:projectSlug", component: LoginView },
  { path: "/:projectSlug/consent", component: ConsentView },
  { path: "/:projectSlug/screening", component: ScreeningView },
  { path: "/:projectSlug/instructions", component: InstructionsView },
  { path: "/:projectSlug/annotate", component: AnnotatorView },
  { path: "/consent-form", component: ConsentFullPage },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;

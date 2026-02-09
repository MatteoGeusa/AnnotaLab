import { createRouter, createWebHistory } from 'vue-router'
import LoginView from './views/LoginView.vue'
import ConsentView from './views/ConsentView.vue'
import InstructionsView from './views/InstructionsView.vue'
import AnnotatorView from './views/AnnotatorView.vue'

const routes = [
    { path: '/', component: LoginView },
    { path: '/consent', component: ConsentView },
    { path: '/instructions', component: InstructionsView },
    { path: '/annotate', component: AnnotatorView }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
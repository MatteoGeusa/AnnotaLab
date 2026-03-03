<template>
    <div class="login-container">
        <div class="card">
            <h1>Annotation Task</h1>
            <p class="subtitle">Please join from your Prolific account with ID and project ID in the URL to start the
                annotation task.
            </p>
            <p v-if="!projectId || !prolificPid" class="error-text">⚠️ Warning: Missing Parameters in URL</p>
            <p v-if="!projectId" class="error-text small">No Project ID found</p>
            <p v-if="!prolificPid" class="error-text small">No Prolific ID found</p>
            <p v-if="prolificPid && prolificPid.length <= 3" class="error-text small">⚠️ Prolific ID is too short
                (minimum 4 characters)</p>

            <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '../axios';

const router = useRouter();
const route = useRoute();

const prolificPid = ref('');
const projectId = ref(null);

const isLoading = ref(false);
const projectSlug = ref(null);
const errorMessage = ref('');

const startSession = async () => {
    if (!isValid.value) return;

    isLoading.value = true;
    errorMessage.value = '';

    try {
        // Collect all query parameters as metadata, but exclude internal/redundant keys
        const metadata = { ...route.query };
        delete metadata.project_id;
        delete metadata.project_slug;
        delete metadata.PROLIFIC_PID;

        const response = await api.post('session/', {
            prolific_pid: prolificPid.value,
            project_id: projectId.value,
            project_slug: projectSlug.value,
            metadata: metadata
        });

        // Salvataggio dati critici
        localStorage.setItem('prolific_pid', prolificPid.value);
        if (projectId.value) localStorage.setItem('project_id', projectId.value);
        if (projectSlug.value) localStorage.setItem('project_slug', projectSlug.value);

        // Routing
        const step = response.data.step;
        const slug = projectSlug.value || projectId.value; // Fallback if no slug

        if (step === 'CONSENT') router.push(`/${slug}/consent`);
        else if (step === 'SCREENING') router.push(`/${slug}/screening`);
        else if (step === 'ONBOARDING') router.push(`/${slug}/instructions`);
        else if (step === 'ANNOTATION') router.push(`/${slug}/annotate`);
        else if (step === 'COMPLETED') router.push(`/${slug}/annotate`);

    } catch (err) {
        if (err.response && err.response.status === 404) {
            errorMessage.value = "Project not found or inactive. Please contact the administrator.";
        } else if (err.response && err.response.data && err.response.data.error) {
            errorMessage.value = err.response.data.error;
        } else {
            errorMessage.value = "Connection error. Please check your internet or retry later.";
        }
        console.error("Login Error:", err);
    } finally {
        isLoading.value = false;
    }
};

onMounted(() => {
    // 1. Cerca il projectSlug nei parametri del percorso (es. /nome-studio)
    if (route.params.projectSlug) {
        projectSlug.value = route.params.projectSlug;
        localStorage.setItem('project_slug', projectSlug.value);
    } else if (route.query.project_id) {
        // Fallback: cerca il project_id nella query string (es. ?project_id=1)
        projectId.value = route.query.project_id;
        localStorage.setItem('project_id', projectId.value);
    } else {
        // Fallback: prova a vedere se erano salvati in precedenza
        const savedSlug = localStorage.getItem('project_slug');
        if (savedSlug) projectSlug.value = savedSlug;

        const savedId = localStorage.getItem('project_id');
        if (savedId) projectId.value = savedId;
    }

    // Auto-fill PID se presente nell'URL (comodo per Prolific)
    if (route.query.PROLIFIC_PID) {
        prolificPid.value = route.query.PROLIFIC_PID;
    }

    // Auto-login if we have everything
    if (isValid.value) {
        startSession();
    }
});

const isValid = computed(() => {
    return prolificPid.value.length > 3 && (projectId.value || projectSlug.value);
});

</script>

<style scoped>
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background-color: #f0f2f5;
}

.card {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
    text-align: center;
}

.subtitle {
    color: #666;
    margin-bottom: 2rem;
}

.form-group {
    margin-bottom: 1.5rem;
    text-align: left;
}

input {
    width: 100%;
    padding: 10px;
    margin-top: 5px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
    box-sizing: border-box;
    /* Important for padding */
}

button {
    width: 100%;
    padding: 12px;
    background-color: #42b983;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
    transition: background 0.2s;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

button:hover:not(:disabled) {
    background-color: #3aa876;
}

.error {
    color: red;
    margin-top: 10px;
    font-size: 0.9rem;
}
</style>
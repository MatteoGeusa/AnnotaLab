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
const errorMessage = ref('');

const startSession = async () => {
    if (!isValid.value) return;

    isLoading.value = true;
    errorMessage.value = '';

    try {
        const metadata = { ...route.query };

        const response = await api.post('session/', {
            prolific_pid: prolificPid.value,
            project_id: projectId.value,
            metadata: metadata
        });

        // Salvataggio dati critici
        localStorage.setItem('prolific_pid', prolificPid.value);

        // Routing
        const step = response.data.step;
        if (step === 'CONSENT') router.push('/consent');
        else if (step === 'INSTRUCTIONS') router.push('/instructions');
        else if (step === 'ANNOTATION') router.push('/annotate');
        else if (step === 'COMPLETED') router.push('/annotate');

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
    // 1. Cerca il project_id nella query string (es. ?project_id=1)
    if (route.query.project_id) {
        projectId.value = route.query.project_id;
        localStorage.setItem('project_id', projectId.value);
    } else {
        // Fallback: prova a vedere se era salvato in precedenza
        const saved = localStorage.getItem('project_id');
        if (saved) projectId.value = saved;
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
    return prolificPid.value.length > 3 && projectId.value;
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
<template>
    <div class="login-container">
        <div class="card">
            <h1>Annotation Task</h1>
            <p class="subtitle">Please join from your Prolific account with ID in the URL to start the annotation task.
            </p>

            <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '../axios';

const router = useRouter();
const route = useRoute();
const prolificPid = ref('');
const isLoading = ref(false);
const errorMessage = ref('');

const startSession = async () => {
    isLoading.value = true;
    errorMessage.value = '';

    try {
        const response = await api.post('session/', { prolific_pid: prolificPid.value });
        localStorage.setItem('prolific_pid', response.data.pid);

        // DYNAMIC REDIRECT
        const step = response.data.step;
        if (step === 'CONSENT') router.push('/consent');
        else if (step === 'INSTRUCTIONS') router.push('/instructions');
        else if (step === 'ANNOTATION') router.push('/annotate');
        else if (step === 'COMPLETED') router.push('/annotate'); // Annotator view will handle the final message

    } catch (error) {
        console.error(error);
        errorMessage.value = "Connection error.";
    } finally {
        isLoading.value = false;
    }
};

onMounted(() => {
    // 1. Prolific uses 'PROLIFIC_PID' parameter (usually all caps)
    if (route.query.PROLIFIC_PID) {
        console.log("Auto-login detecting for:", route.query.PROLIFIC_PID);
        prolificPid.value = route.query.PROLIFIC_PID;

        // Start session immediately!
        startSession();
        return;
    }

    // 2. Check Recent Session in LocalStorage
    const storedPID = localStorage.getItem('prolific_pid');
    if (storedPID) {
        console.log("Resuming session for:", storedPID);
        prolificPid.value = storedPID;
        startSession();
    }
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
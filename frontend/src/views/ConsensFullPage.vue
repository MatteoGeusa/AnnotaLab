<template>
    <div class="page-container">
        <div class="card">
            <button class="back-btn" @click="router.back()">← Back</button>

            <h1>Informed Consent</h1>
            <p class="subtitle">Full informed consent document. Please read carefully.</p>

            <div class="scroll-box">
                <p v-if="loading" class="state-text">Loading...</p>
                <div v-else-if="errorMsg" class="error">{{ errorMsg }}</div>
                <p v-else class="consent-body">{{ consentText }}</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../axios';

const route = useRoute();
const router = useRouter();

const pid = localStorage.getItem('prolific_pid');
const projectId = route.query.project_id ?? localStorage.getItem('project_id');
const projectSlug = route.query.project_slug ?? localStorage.getItem('project_slug');

const consentText = ref('');
const loading = ref(true);
const errorMsg = ref('');

const getConsent = async () => {
    try {
        const res = await api.get('get-consent/', {
            params: { pid, project_id: projectId, project_slug: projectSlug }
        });
        consentText.value = res.data.consent_text;
    } catch (err) {
        errorMsg.value = "Error getting consent. " + (err.response?.data?.error || err.message);
    } finally {
        loading.value = false;
    }
};

onMounted(getConsent);
</script>

<style scoped>
.page-container {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    height: 100vh;
    overflow: hidden;
    padding: 50px 20px;
    box-sizing: border-box;
    background-color: #f0f2f5;
}

.card {
    background: white;
    padding: 40px;
    width: 100%;
    max-width: 760px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.back-btn {
    background: none;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 6px 14px;
    cursor: pointer;
    font-size: 0.88rem;
    color: #555;
    margin-bottom: 24px;
    transition: background 0.2s, border-color 0.2s;
}

.back-btn:hover {
    background: #f5f5f5;
    border-color: #bbb;
}

h1 {
    margin: 0 0 6px;
    font-size: 1.6rem;
    color: #1a1a2e;
}

.subtitle {
    color: #666;
    margin: 0 0 20px;
    font-size: 0.95rem;
}

.scroll-box {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 20px 24px;
    background: #fafafa;
    max-height: 70vh;
    overflow-y: auto;
}

.consent-body {
    margin: 0;
    line-height: 1.8;
    color: #333;
    font-size: 0.95rem;
    white-space: pre-wrap;
}

.state-text {
    margin: 0;
    color: #999;
    font-style: italic;
}

.error {
    color: #dc3545;
}
</style>

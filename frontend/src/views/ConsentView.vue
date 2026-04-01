<template>
    <div class="page-container">
        <div class="card">
            <h1>Informed Consent</h1>
            <p class="subtitle">Please read the following information carefully before proceeding.</p>

            <div class="scroll-box">
                <p v-if="loading" class="state-text">Loading...</p>
                <p v-else-if="errorMsg" class="error">{{ errorMsg }}</p>
                <p v-else class="consent-body">{{ truncatedConsent }}</p>
            </div>

            <a v-if="isLong" class="read-more-link" @click="full_consent_form_url">
                Read the full consent form →
            </a>

            <div class="actions">
                <label class="checkbox-label">
                    <input type="checkbox" v-model="accepted">
                    I have read and understood the information above.
                </label>
                <button @click="submitConsent" :disabled="!accepted">I Agree</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '../axios';

const router = useRouter();
const route = useRoute();

const accepted = ref(false);
const pid = localStorage.getItem('prolific_pid');
const projectId = route.query.project_id ?? localStorage.getItem('project_id');
const projectSlug = route.params.projectSlug ?? localStorage.getItem('project_slug');

const consentText = ref('');
const loading = ref(true);
const errorMsg = ref('');

const TRUNCATE_LIMIT = 500;
const isLong = computed(() => consentText.value.length > TRUNCATE_LIMIT);
const truncatedConsent = computed(() =>
    isLong.value ? consentText.value.slice(0, TRUNCATE_LIMIT) + '…' : consentText.value
);

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

const full_consent_form_url = () => {
    router.push({ path: '/consent-form', query: { project_id: projectId, project_slug: projectSlug } });
};

const submitConsent = async () => {
    await api.post('consent/', { pid, project_id: projectId, project_slug: projectSlug });
    const slug = projectSlug || projectId;
    router.push(`/${slug}/screening`);
};
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
    max-width: 640px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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
    padding: 16px 20px;
    background: #fafafa;
    min-height: 120px;
}

.consent-body {
    margin: 0;
    line-height: 1.7;
    color: #333;
    font-size: 0.95rem;
    white-space: pre-wrap;
}

.state-text {
    margin: 0;
    color: #999;
    font-style: italic;
}

.read-more-link {
    display: inline-block;
    margin-top: 10px;
    font-size: 0.88rem;
    color: #007bff;
    cursor: pointer;
    text-decoration: none;
}

.read-more-link:hover {
    text-decoration: underline;
}

.actions {
    margin-top: 28px;
    border-top: 1px solid #eee;
    padding-top: 20px;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.95rem;
    color: #444;
    margin-bottom: 18px;
    cursor: pointer;
}

.checkbox-label input {
    width: 16px;
    height: 16px;
    cursor: pointer;
    flex-shrink: 0;
}

button {
    width: 100%;
    padding: 12px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.2s;
}

button:hover:not(:disabled) {
    background-color: #0069d9;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.error {
    color: #dc3545;
    margin: 0;
}
</style>
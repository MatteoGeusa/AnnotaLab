<template>
    <div class="page-container">
        <div class="card">
            <div class="card-header">
                <h1>📖 Study Materials</h1>
                <p class="subtitle">Please read the following materials carefully before proceeding to the task.</p>
            </div>

            <div v-if="loading" class="state-text" style="padding: 40px;">Loading codebook...</div>
            <div v-else-if="errorMsg" class="error">{{ errorMsg }}</div>
            <div v-else-if="shouldSkip" class="state-text" style="padding: 40px;">No codebook for this project. Redirecting...</div>

            <div v-else class="markdown-body" v-html="rendered"></div>

            <div v-if="!loading && !shouldSkip && rendered" class="actions">
                <label class="checkbox-label">
                    <input type="checkbox" v-model="hasRead">
                    I have read and understood the materials above.
                </label>
                <button @click="completeCodebook" :disabled="!hasRead || submitting">
                    {{ submitting ? 'Saving...' : 'Continue to Instructions' }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../axios';
import { useProjectContext } from '../composables/useProjectContext';
import { useMarkdownRenderer } from '../composables/useMarkdownRenderer';

const router = useRouter();
const { pid, projectSlug, projectId } = useProjectContext();

const loading = ref(true);
const errorMsg = ref('');
const shouldSkip = ref(false);
const submitting = ref(false);
const hasRead = ref(false);
const rawContent = ref('');

const { rendered } = useMarkdownRenderer(rawContent);

const fetchCodebook = async () => {
    try {
        const res = await api.get('get-codebook/', {
            params: { pid, project_id: projectId, project_slug: projectSlug }
        });

        if (res.data.skip) {
            shouldSkip.value = true;
            const slug = projectSlug || projectId;
            setTimeout(() => router.push(`/${slug}/instructions`), 500);
            return;
        }

        rawContent.value = res.data.content || '';
    } catch (err) {
        errorMsg.value = "Error loading codebook. " + (err.response?.data?.error || err.message);
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    if (!pid) {
        router.push('/');
        return;
    }
    fetchCodebook();
});

const completeCodebook = async () => {
    submitting.value = true;
    try {
        await api.post('codebook/', {
            pid,
            project_slug: projectSlug,
            project_id: projectId
        });
        const slug = projectSlug || projectId;
        router.push(`/${slug}/instructions`);
    } catch (err) {
        errorMsg.value = err.response?.data?.error || "Error saving. Please try again.";
    } finally {
        submitting.value = false;
    }
};
</script>

<style scoped>
@import '../assets/shared.css';
</style>

<template>
    <div class="page-container">
        <div class="card">
            <div class="card-header">
                <h1>📖 Study Materials</h1>
                <p class="subtitle">Please read the following materials carefully before proceeding to the task.</p>
            </div>

            <div v-if="loading" class="state-text">Loading codebook...</div>
            <div v-else-if="errorMsg" class="error">{{ errorMsg }}</div>
            <div v-else-if="shouldSkip" class="state-text">No codebook for this project. Redirecting...</div>

            <div v-else class="codebook-body" v-html="renderedContent"></div>

            <div v-if="!loading && !shouldSkip && renderedContent" class="actions">
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
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '../axios';

const router = useRouter();
const route = useRoute();

const pid = localStorage.getItem('prolific_pid');
const projectSlug = route.params.projectSlug ?? localStorage.getItem('project_slug');
const projectId = localStorage.getItem('project_id');

const loading = ref(true);
const errorMsg = ref('');
const shouldSkip = ref(false);
const submitting = ref(false);
const hasRead = ref(false);

const rawContent = ref('');

// Simple Markdown-to-HTML renderer (no external dependency)
const renderedContent = computed(() => {
    let text = rawContent.value;
    if (!text) return '';

    // Escape HTML entities
    text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Headers
    text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    // Bold and italic
    text = text.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Inline code
    text = text.replace(/`(.+?)`/g, '<code>$1</code>');

    // Unordered lists
    text = text.replace(/^- (.+)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Ordered lists
    text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

    // Horizontal rules
    text = text.replace(/^---$/gm, '<hr>');

    // Paragraphs (lines not already wrapped in tags)
    text = text.replace(/^(?!<[hulo]|<li|<hr)(.+)$/gm, '<p>$1</p>');

    // Clean up empty paragraphs
    text = text.replace(/<p>\s*<\/p>/g, '');

    return text;
});

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
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

.page-container {
    min-height: 100vh;
    padding: 40px 20px;
    background: linear-gradient(135deg, #f0f2f5 0%, #e8ecf1 100%);
    font-family: 'Outfit', sans-serif;
}

.card {
    background: white;
    max-width: 820px;
    margin: 0 auto;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    animation: slideUp 0.5s ease-out;
}

.card-header {
    padding: 32px 40px 20px;
    border-bottom: 2px solid #e3e8ee;
    background: #f8fafc;
}

.card-header h1 {
    margin: 0 0 6px;
    font-size: 1.8rem;
    color: #1a1f36;
    font-weight: 700;
}

.subtitle {
    color: #666;
    margin: 0;
    font-size: 0.95rem;
}

.state-text {
    color: #999;
    font-style: italic;
    padding: 40px;
}

/* CODEBOOK CONTENT */
.codebook-body {
    padding: 32px 40px;
    color: #1a1f36;
    line-height: 1.8;
    font-size: 1rem;
}

.codebook-body :deep(h1) {
    font-size: 1.6rem;
    font-weight: 700;
    color: #1a1f36;
    margin: 28px 0 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e3e8ee;
}

.codebook-body :deep(h2) {
    font-size: 1.3rem;
    font-weight: 600;
    color: #306ee8;
    margin: 24px 0 10px;
}

.codebook-body :deep(h3) {
    font-size: 1.1rem;
    font-weight: 600;
    color: #475569;
    margin: 20px 0 8px;
}

.codebook-body :deep(p) {
    margin: 8px 0;
    color: #334155;
}

.codebook-body :deep(ul) {
    padding-left: 20px;
    margin: 8px 0;
}

.codebook-body :deep(li) {
    margin: 6px 0;
    color: #334155;
}

.codebook-body :deep(strong) {
    color: #1a1f36;
    font-weight: 700;
}

.codebook-body :deep(code) {
    background: #f1f5f9;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.9em;
    color: #306ee8;
}

.codebook-body :deep(hr) {
    border: none;
    border-top: 2px solid #e3e8ee;
    margin: 24px 0;
}

/* ACTIONS */
.actions {
    padding: 24px 40px 32px;
    border-top: 2px solid #e3e8ee;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.95rem;
    color: #444;
    margin-bottom: 18px;
    cursor: pointer;
    font-weight: 500;
}

.checkbox-label input {
    width: 18px;
    height: 18px;
    cursor: pointer;
    flex-shrink: 0;
    accent-color: #306ee8;
}

button {
    width: 100%;
    padding: 14px;
    background: #306ee8;
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 1.1rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s;
    font-family: 'Outfit', sans-serif;
    box-shadow: 0 4px 14px rgba(48, 110, 232, 0.3);
}

button:hover:not(:disabled) {
    background: #1a4ab9;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(48, 110, 232, 0.4);
}

button:disabled {
    background: #ccc;
    cursor: not-allowed;
    box-shadow: none;
}

.error {
    color: #dc3545;
    padding: 20px 40px;
}

/* ANIMATIONS */
@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>

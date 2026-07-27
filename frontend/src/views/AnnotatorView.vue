<template>
    <div class="main-container" :class="{ 'wide-mode': isWide }">
        <div v-if="loading" class="loading-container">
            <div class="loader"></div>
            <p>{{ UI_STRINGS.loading_task }}</p>
        </div>

        <div v-else-if="!currentDoc && !stopped" class="finished-card">
            <div class="confetti">🎉</div>
            <h2>{{ UI_STRINGS.tasks_completed }}</h2>
            <div class="debrief-text">
                <p>{{ UI_STRINGS.debrief_warning }}</p>
                <p>{{ UI_STRINGS.debrief_thank_you }}</p>
            </div>
            <p class="redirect-notice">{{ UI_STRINGS.redirect_notice.replace('{seconds}', countdown) }}</p>
        </div>

        <div v-else-if="stopped" class="finished-card">
            <div class="icon">🛑</div>
            <h2>{{ UI_STRINGS.session_ended }}</h2>
            <p>{{ stopMessage || UI_STRINGS.default_thank_you }}</p>
        </div>

        <div v-else class="task-card">
            <div v-if="isGold" class="training-banner">
                {{ UI_STRINGS.gold_task_banner }}
            </div>

            <div class="card-header highlight-header" style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div class="instruction-box">
                    <h3>{{ UI_STRINGS.task_instruction_header }}</h3>
                    <p>{{ schema.instruction || UI_STRINGS.default_instruction }}</p>
                </div>
                <button @click="toggleWide" class="toggle-wide-btn" :title="isWide ? 'Shrink' : 'Expand'">
                    <span v-if="!isWide">↔️</span>
                    <span v-else>🔄</span>
                </button>
            </div>

            <div class="card-body">
                <!-- Text display (always shown) -->
                <div v-if="!hasComponent('span_highlight')" class="doc-text-preview">
                    {{ currentDoc.text }}
                </div>

                <!-- Component-driven blocks -->
                <template v-for="comp in activeComponents" :key="comp.type">
                    <div class="section" v-if="comp.type === 'span_highlight'">
                        <SpanHighlightBlock :ref="el => blockRefs[comp.type] = el" :text="currentDoc.text"
                            :config="comp" v-model="result[comp.type]" />
                    </div>
                    <div class="section classification-section" v-else-if="comp.type === 'classification'">
                        <ClassificationBlock :ref="el => blockRefs[comp.type] = el" :config="comp"
                            v-model="result[comp.type]" />
                    </div>
                </template>
            </div>

            <div class="card-footer actions">
                <button class="action-btn clear-btn" @click="clearForm">{{ UI_STRINGS.clear_btn }}</button>
                <button class="submit-btn primary-submit" @click="submitTask" :disabled="!canSubmit">
                    {{ UI_STRINGS.submit_btn }}
                </button>
            </div>

            <p v-if="errorMsg" class="error-toast">{{ errorMsg }}</p>
        </div>
    </div>

    <!-- ── DEBUG PANEL ── shows the exact JSON that will be sent to /submit/ -->
    <transition name="debug-slide">
        <div v-if="debugOpen" class="debug-panel">
            <div class="debug-header">
                <span class="debug-title">🛠 Payload JSON → /api/submit/</span>
                <div class="debug-controls">
                    <span class="debug-badge">LIVE</span>
                    <button class="debug-close" @click="debugOpen = false">✕</button>
                </div>
            </div>
            <pre class="debug-body">{{ JSON.stringify(debugPayload, null, 2) }}</pre>
        </div>
    </transition>

    <!-- Floating toggle button -->
    <button class="debug-toggle" @click="debugOpen = !debugOpen" :class="{ active: debugOpen }" title="Toggle debug panel">
        {{ debugOpen ? '🙈' : '🛠' }}
    </button>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../axios';
import { useProjectContext } from '../composables/useProjectContext';
import { UI_STRINGS } from '../i18n';
import SpanHighlightBlock from '../components/blocks/SpanHighlightBlock.vue';
import ClassificationBlock from '../components/blocks/ClassificationBlock.vue';

const router = useRouter();
const { pid, projectSlug, projectId, isTest } = useProjectContext();

// State
const loading = ref(true);
const currentDoc = ref(null);
const errorMsg = ref('');
const schema = ref({});       // annotation_schema from project_config
const startTime = ref(0);
const countdown = ref(5);
let redirectTimer = null;
const stopped = ref(false);
const stopMessage = ref('');
const isGold = ref(false);
const isWide = ref(localStorage.getItem('annotator_wide_mode') === 'true');

const toggleWide = () => {
    isWide.value = !isWide.value;
    localStorage.setItem('annotator_wide_mode', isWide.value);
};

// Component system
const blockRefs = ref({});
const result = ref({});       // { span_highlight: [...], classification: '...' }

onUnmounted(() => { if (redirectTimer) clearInterval(redirectTimer); });
onMounted(() => { if (!pid) router.push('/'); fetchNextTask(); });

// Derive active components from schema.components, with fallback for old schemas
const activeComponents = computed(() => {
    if (schema.value.components?.length > 0)
        return schema.value.components;
    // Backward-compat: infer from legacy root-level keys
    const fallback = [];
    if ((schema.value.span_labels || []).length > 0)
        fallback.push({ type: 'span_highlight', labels: schema.value.span_labels });
    if ((schema.value.class_labels || []).length > 0)
        fallback.push({ type: 'classification', options: schema.value.class_labels });
    return fallback;
});

const hasComponent = (type) => activeComponents.value.some(c => c.type === type);

const canSubmit = computed(() => {
    // Require classification if that component is active
    if (hasComponent('classification')) {
        const val = result.value['classification'];
        if (Array.isArray(val)) return val.length > 0;
        return val != null;
    }
    return true;
});

const clearForm = () => {
    result.value = {};
    Object.values(blockRefs.value).forEach(ref => ref?.reset?.());
};

const fetchNextTask = async () => {
    loading.value = true;
    currentDoc.value = null;
    errorMsg.value = '';
    result.value = {};
    stopped.value = false;

    if (!projectId && !projectSlug) {
        errorMsg.value = UI_STRINGS.error_no_project;
        loading.value = false;
        return;
    }
    try {
        const res = await api.get('next-task/', {
            params: { pid, project_id: projectId, project_slug: projectSlug, is_test: isTest }
        });

        if (res.data.status === 'completed') {
            loading.value = false;
            redirectTimer = setInterval(() => {
                countdown.value--;
                if (countdown.value <= 0) { clearInterval(redirectTimer); window.location.href = res.data.completion_url; }
            }, 1000);
            return;
        }
        if (res.data.status === 'stopped') {
            loading.value = false;
            stopped.value = true;
            stopMessage.value = res.data.message;
            return;
        }

        isGold.value = !!res.data.is_gold;
        currentDoc.value = res.data;
        schema.value = res.data.project_config || {};
        startTime.value = Date.now();
    } catch (err) {
        errorMsg.value = UI_STRINGS.error_fetch_task;
    } finally {
        loading.value = false;
    }
};

const submitTask = async () => {
    if (!canSubmit.value) return;
    loading.value = true;

    const payload = {
        pid,
        project_id: projectId,
        project_slug: projectSlug,
        document: currentDoc.value.id,
        result: { ...result.value },
        milliseconds_to_complete: Date.now() - startTime.value,
        is_test: isTest,
    };

    try {
        await api.post('submit/', payload);
        fetchNextTask();
    } catch (err) {
        errorMsg.value = UI_STRINGS.error_save_task;
        loading.value = false;
    }
};

// ── Debug panel ──
const debugOpen = ref(false);

const debugPayload = computed(() => ({
    pid,
    project_id: projectId,
    project_slug: projectSlug,
    document: currentDoc.value?.id ?? null,
    result: { ...result.value },
    milliseconds_to_complete: currentDoc.value ? (Date.now() - startTime.value) : 0,
    is_test: isTest,
}));
</script>

<style scoped>
@import '../assets/shared.css';

.main-container {
    max-width: 1000px;
    margin: 0px auto;
    padding: 37px;
    font-family: 'Outfit', sans-serif;
    color: #1a1f36;
    transition: max-width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.main-container.wide-mode {
    max-width: 1600px;
}

.toggle-wide-btn {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.toggle-wide-btn:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* CARDS */
.task-card,
.finished-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    animation: slideUp 0.5s ease-out;
}

.highlight-header {
    background-color: #f8fafc;
}

.instruction-box h3 {
    margin: 0 0 8px 0;
    color: #1a1f36;
    font-size: 1.25rem;
}

.instruction-box p {
    margin: 0;
    color: #4f566b;
    line-height: 1.5;
}

/* TRAINING BANNER */
.training-banner {
    background: #fef3c7;
    color: #92400e;
    padding: 12px;
    text-align: center;
    font-weight: 700;
    font-size: 0.9rem;
    border-bottom: 1px solid #fde68a;
}

/* FINISHED STATE */
.finished-card {
    text-align: center;
    padding: 60px 40px;
    background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
}

.confetti {
    font-size: 4rem;
    margin-bottom: 20px;
}

.finished-card h2 {
    color: #1a1f36;
    margin-bottom: 20px;
    font-size: 2.5rem;
}

.debrief-text {
    background: white;
    border-radius: 12px;
    padding: 24px;
    max-width: 600px;
    margin: 0 auto 30px;
    border-left: 6px solid #306ee8;
    text-align: left;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
}

/* ── DEBUG PANEL ── */
.debug-panel {
    position: fixed;
    bottom: 70px;
    right: 20px;
    width: 440px;
    max-height: 60vh;
    background: rgba(13, 17, 23, 0.97);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 110, 123, 0.5);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05);
    display: flex;
    flex-direction: column;
    z-index: 9999;
    overflow: hidden;
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
}

.debug-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: rgba(255,255,255,0.04);
    border-bottom: 1px solid rgba(99, 110, 123, 0.3);
    flex-shrink: 0;
}

.debug-title {
    font-size: 0.78rem;
    font-weight: 600;
    color: #8b949e;
    letter-spacing: 0.5px;
}

.debug-controls {
    display: flex;
    align-items: center;
    gap: 8px;
}

.debug-badge {
    background: #28a745;
    color: white;
    font-size: 0.6rem;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    letter-spacing: 1px;
    animation: pulse-badge 2s ease-in-out infinite;
}

@keyframes pulse-badge {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.debug-close {
    background: none;
    border: none;
    color: #6e7681;
    cursor: pointer;
    font-size: 0.85rem;
    padding: 0;
    line-height: 1;
    transition: color 0.15s;
}
.debug-close:hover { color: #e6edf3; }

.debug-body {
    flex: 1;
    overflow-y: auto;
    margin: 0;
    padding: 14px;
    font-size: 0.73rem;
    line-height: 1.65;
    color: #e6edf3;
    white-space: pre;
    scrollbar-width: thin;
    scrollbar-color: rgba(99,110,123,0.4) transparent;
}

.debug-toggle {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: 2px solid rgba(99, 110, 123, 0.5);
    background: rgba(13, 17, 23, 0.92);
    backdrop-filter: blur(8px);
    cursor: pointer;
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    transition: all 0.2s;
}
.debug-toggle:hover {
    border-color: #58a6ff;
    background: rgba(88, 166, 255, 0.15);
    transform: scale(1.08);
}
.debug-toggle.active {
    border-color: #28a745;
    background: rgba(40, 167, 69, 0.15);
}

/* Slide-up animation */
.debug-slide-enter-active, .debug-slide-leave-active {
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s;
}
.debug-slide-enter-from, .debug-slide-leave-to {
    transform: translateY(20px);
    opacity: 0;
}
</style>

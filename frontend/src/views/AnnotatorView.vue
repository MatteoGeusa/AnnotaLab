<template>
    <div class="main-container">
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

            <div class="card-header highlight-header">
                <div class="instruction-box">
                    <h3>{{ UI_STRINGS.task_instruction_header }}</h3>
                    <p>{{ schema.instruction || UI_STRINGS.default_instruction }}</p>
                </div>
            </div>

            <div class="card-body">
                <!-- Text display (always shown) -->
                <div v-if="!hasComponent('span_highlight')" class="doc-text-preview">
                    {{ currentDoc.text }}
                </div>

                <!-- Component-driven blocks -->
                <template v-for="comp in activeComponents" :key="comp.type">
                    <div class="section" v-if="comp.type === 'span_highlight'">
                        <SpanHighlightBlock
                            :ref="el => blockRefs[comp.type] = el"
                            :text="currentDoc.text"
                            :config="comp"
                            v-model="result[comp.type]"
                        />
                    </div>
                    <div class="section classification-section" v-else-if="comp.type === 'classification'">
                        <ClassificationBlock
                            :ref="el => blockRefs[comp.type] = el"
                            :config="comp"
                            v-model="result[comp.type]"
                        />
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
const { pid, projectSlug, projectId } = useProjectContext();

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
            params: { pid, project_id: projectId, project_slug: projectSlug }
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
    };

    try {
        await api.post('submit/', payload);
        fetchNextTask();
    } catch (err) {
        errorMsg.value = UI_STRINGS.error_save_task;
        loading.value = false;
    }
};
</script>

<style scoped>
@import '../assets/shared.css';

.main-container {
    max-width: 1000px;
    margin: 0px auto;
    padding: 37px;
    font-family: 'Outfit', sans-serif;
    color: #1a1f36;
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
</style>

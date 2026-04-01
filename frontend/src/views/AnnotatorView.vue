<template>
    <div class="main-container">
        <div v-if="loading" class="loading-container">
            <div class="loader"></div>
            <p>Loading next task...</p>
        </div>

        <div v-else-if="!currentDoc && !stopped" class="finished-card">
            <div class="confetti">🎉</div>
            <h2>All tasks completed!</h2>
            <div class="debrief-text">
                <p>The texts you annotated were obtained from social media and may include false information and
                    conspiracy theories. The authors of this task do not endorse them.</p>
                <p>You may take this task multiple times. Thank you for your work!</p>
            </div>
            <p class="redirect-notice">Redirecting to provider in <strong>{{ countdown }}</strong> seconds...</p>
        </div>

        <div v-else-if="stopped" class="finished-card">
            <div class="icon">🛑</div>
            <h2>Session Ended</h2>
            <p>{{ stopMessage || "Thank you for your contribution." }}</p>
        </div>

        <div v-else class="task-card">
            <div v-if="isGold" class="training-banner">
                QUALITY CONTROL TASK (This is a gold unit used to verify annotation quality)
            </div>

            <div class="card-header highlight-header">
                <div class="instruction-box">
                    <h3>Task Instruction</h3>
                    <p>{{ config.instruction || "Read the text below and complete the tasks." }}</p>
                </div>
            </div>

            <div class="card-body">
                <div class="section" v-if="hasHighlighter">
                    <TextHighlighter :text="currentDoc.text" :labels="spanLabels" v-model:spans="spans" />
                </div>

                <div class="doc-text-preview" v-else>
                    {{ currentDoc.text }}
                </div>

                <div class="section classification-section" v-if="classOptions.length > 0">
                    <div class="question-title">
                        {{ config.question || "Classify this text:" }}
                    </div>

                    <div class="options-grid">
                        <label v-for="opt in classOptions" :key="opt.value" class="option-label"
                            :class="{ active: isSelected(opt.value) }" :title="opt.hover_hint">
                            <input v-if="config.multi_select" type="checkbox" :value="opt.value"
                                v-model="classification">
                            <input v-else type="radio" :value="opt.value" v-model="classification">
                            <span class="check-icon"></span>
                            {{ opt.label }}
                        </label>
                    </div>
                </div>
            </div>

            <div class="card-footer actions">
                <button class="action-btn clear-btn" @click="clearForm">Clear</button>
                <button class="submit-btn primary-submit" @click="submitTask" :disabled="!canSubmit">
                    Submit &amp; Next
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
import TextHighlighter from '../components/TextHighlighter.vue';
import { useProjectContext } from '../composables/useProjectContext';

const router = useRouter();
const { pid, projectSlug, projectId } = useProjectContext();

// STATO
const loading = ref(true);
const currentDoc = ref(null);
const errorMsg = ref('');
const config = ref({});
const startTime = ref(0);
const countdown = ref(5);
let redirectTimer = null;
const stopped = ref(false);
const stopMessage = ref('');
const isTraining = ref(false);
const isGold = ref(false);

onUnmounted(() => {
    if (redirectTimer) clearInterval(redirectTimer);
});

// RISPOSTE DELL'UTENTE
const classification = ref(null);
const spans = ref([]);

// OPZIONI ESTRATTE DAL CONFIG
const spanLabels = ref([]);
const classOptions = ref([]);

const hasHighlighter = computed(() => spanLabels.value.length > 0);

onMounted(() => {
    if (!pid) router.push('/');
    fetchNextTask();
});

const clearForm = () => {
    spans.value = [];
    if (config.value.multi_select) {
        classification.value = [];
    } else {
        classification.value = null;
    }
};

const fetchNextTask = async () => {
    loading.value = true;
    currentDoc.value = null;
    errorMsg.value = '';
    spans.value = [];
    stopped.value = false;

    if (!projectId && !projectSlug) {
        errorMsg.value = "Fatal Error: No Project ID/Slug found.";
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
                if (countdown.value <= 0) {
                    clearInterval(redirectTimer);
                    window.location.href = res.data.completion_url;
                }
            }, 1000);
            return;
        } else if (res.data.status === 'stopped') {
            loading.value = false;
            stopped.value = true;
            stopMessage.value = res.data.message;
            return;
        }

        isTraining.value = !!res.data.feedback_enabled;
        isGold.value = !!res.data.is_gold;

        currentDoc.value = res.data;
        config.value = res.data.project_config || {};

        spanLabels.value = config.value.span_labels || [];
        classOptions.value = config.value.class_labels || [];

        if (config.value.multi_select) {
            classification.value = [];
        } else {
            classification.value = null;
        }

        startTime.value = Date.now();
    } catch (err) {
        errorMsg.value = "Error fetching task. Please refresh.";
    } finally {
        loading.value = false;
    }
};

const isSelected = (val) => {
    if (Array.isArray(classification.value)) {
        return classification.value.includes(val);
    }
    return classification.value === val;
};

const canSubmit = computed(() => {
    if (classOptions.value.length > 0) {
        if (Array.isArray(classification.value)) {
            return classification.value.length > 0;
        }
        return classification.value !== null;
    }
    return true;
});

const submitTask = async () => {
    if (!canSubmit.value) return;

    const duration = (Date.now() - startTime.value);
    loading.value = true;

    const payload = {
        pid: pid,
        document: currentDoc.value.id,
        result: {
            classification: classification.value,
            spans: spans.value
        },
        milliseconds_to_complete: duration
    };

    try {
        await api.post('submit/', payload);
        fetchNextTask();
    } catch (err) {
        errorMsg.value = "Error saving. Try again.";
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

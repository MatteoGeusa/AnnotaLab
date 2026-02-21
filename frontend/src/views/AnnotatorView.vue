<template>
    <div class="main-container">
        <header class="app-header">
            <div class="user-info">
                <!-- temporarily disabled logout button -->
                <!-- <span class="pid">Worker: {{ pid }}</span> -->
                <!-- <button @click="logout" class="logout-btn">Logout</button> -->
            </div>
        </header>

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

        <div v-else-if="isSurvey" class="task-card survey-container">
            <div class="card-header survey-header">
                <h3>Preliminary Survey</h3>
                <p>Sondaggio Preliminare</p>
            </div>

            <div class="card-body">
                <div v-for="(q, idx) in surveyQuestions" :key="idx" class="survey-item">
                    <label class="survey-label">{{ q.text }}</label>

                    <!-- Multiple Choice -->
                    <div v-if="q.options" class="survey-options">
                        <label v-for="opt in q.options" :key="opt" class="radio-label">
                            <input type="radio" :name="'q' + idx" :value="opt" v-model="surveyAnswers[idx]">
                            <span class="radio-custom"></span>
                            {{ opt }}
                        </label>
                    </div>

                    <!-- Free Text -->
                    <input v-else type="text" class="survey-input" v-model="surveyAnswers[idx]"
                        placeholder="Your answer...">
                </div>
            </div>

            <div class="card-footer">
                <button class="submit-btn success" @click="submitSurvey" :disabled="!canSubmitSurvey">
                    Submit Survey
                </button>
            </div>
        </div>

        <div v-else class="task-card">
            <div v-if="isTraining" class="training-banner">
                🎓 TRAINING MODE (Feedback Enabled)
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
                            :class="{ active: isSelected(opt.value) }">
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
                    Submit & Next
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

const router = useRouter();
const pid = localStorage.getItem('prolific_pid');

// STATO
const loading = ref(true);
const currentDoc = ref(null);
const errorMsg = ref('');
const config = ref({});
const startTime = ref(0);
const countdown = ref(10);
let redirectTimer = null;
const stopped = ref(false);
const stopMessage = ref('');
const isSurvey = ref(false);
const surveyQuestions = ref([]);
const surveyAnswers = ref({});
const isTraining = ref(false);

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

    const pid = localStorage.getItem('prolific_pid');
    const projectId = localStorage.getItem('project_id');

    if (!projectId) {
        errorMsg.value = "Fatal Error: No Project ID found.";
        loading.value = false;
        return;
    }

    try {
        const res = await api.get(`next-task/?pid=${pid}&project_id=${projectId}`);

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
        isSurvey.value = false;

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

const canSubmitSurvey = computed(() => {
    if (surveyQuestions.value.length === 0) return true;
    for (let i = 0; i < surveyQuestions.value.length; i++) {
        if (!surveyAnswers.value[i] || surveyAnswers.value[i].trim() === '') return false;
    }
    return true;
});

const submitSurvey = async () => {
    loading.value = true;
    const pid = localStorage.getItem('prolific_pid');
    const projectId = localStorage.getItem('project_id');

    try {
        await api.post('submit-survey/', {
            pid: pid,
            project_id: projectId,
            survey_data: surveyAnswers.value
        });
        fetchNextTask();
    } catch (err) {
        errorMsg.value = "Error submitting survey.";
        loading.value = false;
    }
};

const logout = () => {
    localStorage.removeItem('prolific_pid');
    router.push('/');
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

.main-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'Outfit', sans-serif;
    min-height: 100vh;
    background-color: #f6f8fa;
    color: #1a1f36;
}

.app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 0;
    margin-bottom: 2rem;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.logo {
    font-size: 2rem;
}

.brand .title {
    font-size: 1.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #306ee8 0%, #172b4d 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.user-info {
    display: flex;
    align-items: center;
    gap: 15px;
    background: white;
    padding: 6px 16px;
    border-radius: 50px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.pid {
    font-weight: 500;
    color: #4f566b;
    font-size: 0.9rem;
}

.logout-btn {
    background: #fff;
    border: 1px solid #dcdfe6;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s;
}

.logout-btn:hover {
    background: #fef2f2;
    border-color: #fee2e2;
    color: #dc2626;
}

/* CARDS */
.task-card,
.finished-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    margin-bottom: 30px;
    animation: slideUp 0.5s ease-out;
}

.card-header {
    padding: 24px 30px;
    border-bottom: 1px solid #e3e8ee;
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

.card-body {
    padding: 30px;
}

.card-footer {
    padding: 20px 30px;
    background: #f8fafc;
    border-top: 1px solid #e3e8ee;
    display: flex;
    justify-content: flex-end;
    gap: 15px;
}

/* SURVEY STYLES */
.survey-header {
    background: linear-gradient(135deg, #e3effb 0%, #f0f7ff 100%);
}

.survey-item {
    margin-bottom: 30px;
    padding: 20px;
    border-radius: 12px;
    background: #f9fafb;
}

.survey-label {
    display: block;
    font-weight: 600;
    margin-bottom: 15px;
    font-size: 1.1rem;
}

.survey-options {
    display: grid;
    gap: 10px;
}

.radio-label {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: white;
    border: 1px solid #e3e8ee;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.radio-label:hover {
    border-color: #306ee8;
    background: #f0f7ff;
}

/* CLASSIFICATION */
.classification-section {
    margin-top: 30px;
    padding-top: 30px;
    border-top: 2px dashed #e3e8ee;
}

.question-title {
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 20px;
    color: #1a1f36;
}

.options-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
}

.option-label {
    background: #f8fafc;
    border: 2px solid #e3e8ee;
    padding: 12px 24px;
    border-radius: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    user-select: none;
}

.option-label:hover {
    border-color: #cbd5e1;
    background: #fff;
}

.option-label.active {
    background: #306ee8;
    color: white;
    border-color: #1a4ab9;
    box-shadow: 0 4px 12px rgba(48, 110, 232, 0.3);
}

.option-label input {
    display: none;
}

/* BUTTONS */
.action-btn {
    padding: 12px 24px;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
}

.clear-btn {
    background: #f1f5f9;
    color: #475569;
}

.clear-btn:hover {
    background: #e2e8f0;
}

.submit-btn {
    padding: 14px 32px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 1.05rem;
    cursor: pointer;
    border: none;
    transition: all 0.3s;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
}

.primary-submit {
    background: #306ee8;
    color: white;
    flex-grow: 1;
    max-width: 300px;
}

.primary-submit:hover:not(:disabled) {
    background: #1a4ab9;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(48, 110, 232, 0.4);
}

.submit-btn:disabled {
    background: #e3e8ee;
    color: #a0aec0;
    box-shadow: none;
    cursor: not-allowed;
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

/* LOADING */
.loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 100px 0;
}

.loader {
    width: 48px;
    height: 48px;
    border: 5px solid #e3e8ee;
    border-bottom-color: #306ee8;
    border-radius: 50%;
    animation: rotation 1s linear infinite;
    margin-bottom: 20px;
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

/* ANIMATIONS */
@keyframes rotation {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}

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

/* ERROR TOAST */
.error-toast {
    position: fixed;
    bottom: 30px;
    right: 30px;
    background: #fee2e2;
    color: #dc2626;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-left: 4px solid #dc2626;
}

/* UTILS */
.doc-text-preview {
    font-size: 1.2rem;
    line-height: 1.8;
    color: #334155;
    background: #f8fafc;
    padding: 24px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
}
</style>

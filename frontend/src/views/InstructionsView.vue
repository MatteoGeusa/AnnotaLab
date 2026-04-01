<template>
    <div class="page-container">
        <!-- LOADING -->
        <div v-if="loading" class="card wide center-content">
            <div class="loader"></div>
            <p class="state-text">Loading instructions...</p>
        </div>

        <!-- ERROR -->
        <div v-else-if="errorMsg" class="card wide">
            <p class="error">{{ errorMsg }}</p>
        </div>

        <!-- SKIP -->
        <div v-else-if="shouldSkip" class="card wide center-content">
            <p class="state-text">No instructions for this project. Redirecting...</p>
        </div>

        <!-- PHASE 1: READ INSTRUCTIONS -->
        <div v-else-if="phase === 'instructions'" class="card wide">
            <div class="card-header">
                <h1>📝 Task Instructions</h1>
                <p class="subtitle">Please read the following instructions carefully before starting.</p>
            </div>

            <div class="markdown-body" v-html="rendered"></div>

            <div class="actions">
                <label class="checkbox-label">
                    <input type="checkbox" v-model="hasReadInstructions">
                    I have read and understood the instructions above.
                </label>
                <button @click="goToPracticeOrFinish" :disabled="!hasReadInstructions">
                    {{ hasPractice ? 'Continue to Practice Task' : 'Start Task' }}
                </button>
            </div>
        </div>

        <!-- PHASE 2: PRACTICE TASK -->
        <div v-else-if="phase === 'practice'" class="task-card">
            <div class="practice-banner" :class="practiceTaskRequired ? 'practice-banner-required' : ''">
                🎯 PRACTICE TASK — {{ practiceTaskRequired ? '⚠️ You must pass this task to proceed' : 'Try annotating this example before starting the real task' }}
            </div>

            <div class="card-header highlight-header">
                <div class="instruction-box flex-guide">
                    <div class="task-instructions-text">
                        <h3>Practice Task</h3>
                        <p>{{ taskConfig.instruction || `Read the text below and complete the tasks, then submit to see
                            feedback.` }}
                        </p>
                    </div>

                    <div class="technical-mini-guide">
                        <h5>How to annotate:</h5>
                        <ul>
                            <li><span class="step-icon">1</span> <strong>Highlight:</strong> Click &amp; drag over text</li>
                            <li><span class="step-icon">2</span> <strong>Label:</strong> Click a colored button</li>
                            <li><span class="step-icon">3</span> <strong>Remove:</strong> Click an existing highlight
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="card-body">
                <!-- Text Highlighter or plain text -->
                <div class="section" v-if="spanLabels.length > 0">
                    <TextHighlighter :text="practiceTask.text" :labels="spanLabels" v-model:spans="practiceSpans" />
                </div>
                <div class="doc-text-preview" v-else>
                    {{ practiceTask.text }}
                </div>

                <!-- Classification -->
                <div class="section classification-section" v-if="classOptions.length > 0">
                    <div class="question-title">
                        {{ taskConfig.question || "Classify this text:" }}
                    </div>
                    <div class="options-grid">
                        <label v-for="opt in classOptions" :key="opt.value" class="option-label"
                            :class="{ active: practiceClassification === opt.value }">
                            <input type="radio" :value="opt.value" v-model="practiceClassification">
                            <span class="check-icon"></span>
                            {{ opt.label }}
                        </label>
                    </div>
                </div>
            </div>

            <!-- ACTIONS -->
            <div class="card-footer actions" v-if="!showFeedback">
                <button class="action-btn clear-btn" @click="clearPractice">Clear</button>
                
                <div style="display: flex; gap: 10px;">
                    <button v-if="!practiceTaskRequired" class="submit-btn skip-btn" @click="finishInstructions" style="background-color: #94a3b8;">
                        Skip Practice
                    </button>
                    <button class="submit-btn primary-submit" @click="checkPractice" :disabled="!canSubmitPractice">
                        Submit Practice
                    </button>
                </div>
            </div>

            <!-- FEEDBACK -->
            <div v-if="showFeedback" class="feedback-container">
                <div class="feedback-header" :class="feedbackCorrect ? 'feedback-success' : 'feedback-error'">
                    <span class="feedback-icon">{{ feedbackCorrect ? '✅' : '❌' }}</span>
                    <span class="feedback-title">{{ feedbackCorrect ? `Correct! Well done.` : `Not quite right. Review
                        the feedback below.` }}</span>
                </div>

                <div class="feedback-details">
                    <!-- Classification feedback -->
                    <div v-if="classOptions.length > 0" class="feedback-item">
                        <strong>Classification:</strong>
                        <span v-if="classificationCorrect" class="correct-text">✅ Your answer "{{ practiceClassification
                        }}" is correct.</span>
                        <span v-else class="wrong-text">❌ You selected "{{ practiceClassification || `nothing` }}" — the
                            correct answer is
                            "{{ goldSolution.classification }}".</span>
                    </div>

                    <!-- Spans feedback -->
                    <div v-if="spanLabels.length > 0" class="feedback-item">
                        <strong>Highlights:</strong>
                        <div class="spans-feedback">
                            <div v-for="(gs, i) in (goldSolution.spans || [])" :key="i" class="span-feedback-row">
                                <span class="badge" :style="{ background: getLabelColor(gs.label) }">{{ gs.label
                                }}</span>
                                <span v-if="matchedSpans[i]" class="correct-text">✅ "{{ gs.text }}"</span>
                                <span v-else class="wrong-text">❌ Missing: "{{ gs.text }}"</span>
                            </div>
                        </div>
                    </div>

                    <!-- Hints -->
                    <div v-if="practiceTask.hints && practiceTask.hints.length > 0" class="hints-section">
                        <strong>💡 Hints:</strong>
                        <ul class="hints-list">
                            <li v-for="(hint, i) in practiceTask.hints" :key="i">{{ hint }}</li>
                        </ul>
                    </div>
                </div>

                <div class="feedback-actions">
                    <button v-if="!feedbackCorrect" class="action-btn retry-btn" @click="retryPractice">
                        🔄 Try Again
                    </button>
                    <!-- Skip only shown if practice is NOT required, or if they got it correct -->
                    <button
                        v-if="!practiceTaskRequired || feedbackCorrect"
                        class="submit-btn primary-submit"
                        @click="finishInstructions"
                        :disabled="practiceTaskRequired && !feedbackCorrect"
                    >
                        {{ feedbackCorrect ? '🚀 Start Real Task' : 'Skip & Start Task Anyway' }}
                    </button>
                    <p v-if="practiceTaskRequired && !feedbackCorrect" class="required-notice">
                        🔒 This practice task is mandatory. Please try again until you get it right.
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../axios';
import TextHighlighter from '../components/TextHighlighter.vue';
import { useProjectContext } from '../composables/useProjectContext';
import { useMarkdownRenderer } from '../composables/useMarkdownRenderer';

const router = useRouter();
const { pid, projectSlug, projectId } = useProjectContext();

// State
const loading = ref(true);
const errorMsg = ref('');
const shouldSkip = ref(false);
const phase = ref('instructions'); // 'instructions' | 'practice'
const practiceTaskRequired = ref(false);
const hasReadInstructions = ref(false);

// Instructions content
const rawInstructions = ref('');
const practiceTask = ref(null);
const taskConfig = ref({});

// Practice state
const practiceSpans = ref([]);
const practiceClassification = ref(null);
const showFeedback = ref(false);
const feedbackCorrect = ref(false);
const classificationCorrect = ref(false);
const matchedSpans = ref([]);

// Derived from config
const spanLabels = computed(() => taskConfig.value.span_labels || []);
const classOptions = computed(() => taskConfig.value.class_labels || []);
const hasPractice = computed(() => practiceTask.value && practiceTask.value.text);
const goldSolution = computed(() => (practiceTask.value && practiceTask.value.gold_solution) || {});

const canSubmitPractice = computed(() => {
    if (classOptions.value.length > 0) {
        return practiceClassification.value !== null;
    }
    return true;
});

const { rendered } = useMarkdownRenderer(rawInstructions);

// Fetch data
const fetchInstructions = async () => {
    try {
        const res = await api.get('get-instructions/', {
            params: { pid, project_id: projectId, project_slug: projectSlug }
        });

        if (res.data.skip) {
            shouldSkip.value = true;
            const slug = projectSlug || projectId;
            await api.post('onboarding/', { pid, project_slug: projectSlug, project_id: projectId });
            setTimeout(() => router.push(`/${slug}/annotate`), 500);
            return;
        }

        rawInstructions.value = res.data.content || '';
        practiceTask.value = res.data.practice_task || null;
        practiceTaskRequired.value = res.data.practice_task_required || false;
        taskConfig.value = res.data.task_config || {};

        if (!res.data.has_instructions && practiceTask.value) {
            phase.value = 'practice';
        }
    } catch (err) {
        errorMsg.value = "Error loading instructions. " + (err.response?.data?.error || err.message);
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    if (!pid) {
        router.push('/');
        return;
    }
    fetchInstructions();
});

// Navigation
const goToPracticeOrFinish = () => {
    if (hasPractice.value) {
        phase.value = 'practice';
    } else {
        finishInstructions();
    }
};

const getLabelColor = (labelName) => {
    const l = spanLabels.value.find(x => x.name === labelName);
    return l ? l.color : '#cbd5e1';
};

// Practice evaluation
const checkPractice = () => {
    const gold = goldSolution.value;

    classificationCorrect.value = !classOptions.value.length || practiceClassification.value === gold.classification;

    const goldSpans = gold.spans || [];
    matchedSpans.value = goldSpans.map(gs => {
        return practiceSpans.value.some(ps =>
            ps.label === gs.label &&
            Math.abs(ps.start - gs.start) <= 5 &&
            Math.abs(ps.end - gs.end) <= 5
        );
    });

    const allSpansCorrect = matchedSpans.value.every(m => m);
    feedbackCorrect.value = classificationCorrect.value && (goldSpans.length === 0 || allSpansCorrect);
    showFeedback.value = true;
};

const clearPractice = () => {
    practiceSpans.value = [];
    practiceClassification.value = null;
};

const retryPractice = () => {
    clearPractice();
    showFeedback.value = false;
    feedbackCorrect.value = false;
};

const finishInstructions = async () => {
    try {
        await api.post('onboarding/', {
            pid,
            project_slug: projectSlug,
            project_id: projectId
        });
        const slug = projectSlug || projectId;
        router.push(`/${slug}/annotate`);
    } catch (err) {
        errorMsg.value = "Error saving. Please try again.";
    }
};
</script>

<style scoped>
@import '../assets/shared.css';

/* ── TASK CARD (più larga della card standard) ── */
.task-card {
    background: white;
    max-width: 1000px;
    margin: 0 auto;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    animation: slideUp 0.5s ease-out;
}

.highlight-header {
    background-color: #f8fafc;
}

.flex-guide {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 30px;
}

.task-instructions-text {
    flex: 1;
}

.technical-mini-guide {
    background: #fff;
    border: 1px solid #e2e8f0;
    padding: 15px;
    border-radius: 12px;
    width: 280px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.technical-mini-guide h5 {
    margin: 0 0 10px 0;
    font-size: 0.9rem;
    color: #1a1f36;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.technical-mini-guide ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.technical-mini-guide li {
    font-size: 0.85rem;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
    color: #4f566b;
}

.step-icon {
    background: #306ee8;
    color: white;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 700;
    flex-shrink: 0;
}

/* ── PRACTICE BANNER ── */
.practice-banner {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    padding: 14px;
    text-align: center;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.3px;
}

.practice-banner-required {
    background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
}

.required-notice {
    margin: 12px 0 0;
    padding: 10px 16px;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    color: #991b1b;
    font-size: 0.9rem;
    font-weight: 500;
    text-align: center;
    width: 100%;
}

/* ── FEEDBACK ── */
.feedback-container {
    border-top: 2px solid #e3e8ee;
    animation: slideUp 0.4s ease-out;
}

.feedback-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 18px 30px;
    font-weight: 700;
    font-size: 1.05rem;
}

.feedback-success {
    background: #ecfdf5;
    color: #065f46;
    border-bottom: 2px solid #a7f3d0;
}

.feedback-error {
    background: #fef2f2;
    color: #991b1b;
    border-bottom: 2px solid #fecaca;
}

.feedback-icon {
    font-size: 1.4rem;
}

.feedback-details {
    padding: 24px 30px;
    display: flex;
    flex-direction: column;
    gap: 18px;
}

.feedback-item {
    font-size: 0.95rem;
    line-height: 1.6;
}

.correct-text { color: #065f46; }
.wrong-text { color: #991b1b; }

.spans-feedback {
    margin-top: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.span-feedback-row {
    display: flex;
    align-items: center;
    gap: 10px;
}

.badge {
    color: white;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    min-width: 60px;
    text-align: center;
}

.hints-section {
    margin-top: 8px;
    padding: 16px;
    background: #fffbeb;
    border-radius: 10px;
    border-left: 4px solid #f59e0b;
}

.hints-list {
    margin: 8px 0 0 0;
    padding-left: 20px;
}

.hints-list li {
    margin: 6px 0;
    color: #78350f;
    font-size: 0.9rem;
}

.feedback-actions {
    padding: 20px 30px;
    background: #f8fafc;
    display: flex;
    justify-content: flex-end;
    gap: 15px;
}

.retry-btn {
    background: #fef3c7;
    color: #92400e;
    font-weight: 700;
}

.retry-btn:hover {
    background: #fde68a;
}
</style>
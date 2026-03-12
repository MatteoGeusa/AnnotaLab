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

            <div class="instructions-body" v-html="renderedInstructions"></div>

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
            <div class="practice-banner">
                🎯 PRACTICE TASK — Try annotating this example before starting the real task
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
                            <li><span class="step-icon">1</span> <strong>Highlight:</strong> Click & drag over text</li>
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
                <button class="submit-btn primary-submit" @click="checkPractice" :disabled="!canSubmitPractice">
                    Submit Practice
                </button>
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
                    <button class="submit-btn primary-submit" @click="finishInstructions">
                        {{ feedbackCorrect ? '🚀 Start Real Task' : 'Skip & Start Task Anyway' }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '../axios';
import TextHighlighter from '../components/TextHighlighter.vue';

const router = useRouter();
const route = useRoute();
const pid = localStorage.getItem('prolific_pid');
const projectSlug = route.params.projectSlug ?? localStorage.getItem('project_slug');
const projectId = localStorage.getItem('project_id');

// State
const loading = ref(true);
const errorMsg = ref('');
const shouldSkip = ref(false);
const phase = ref('instructions'); // 'instructions' | 'practice'
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

// Simple Markdown renderer (same as CodebookView)
const renderedInstructions = computed(() => {
    let text = rawInstructions.value;
    if (!text) return '';

    text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Headers
    text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    // Bold and italic
    text = text.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/(?<!\w)_(.+?)_(?!\w)/g, '<em>$1</em>');
    text = text.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

    // Inline code
    text = text.replace(/`(.+?)`/g, '<code>$1</code>');

    // Unordered lists
    text = text.replace(/^- (.+)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Ordered lists
    text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

    // Horizontal rules
    text = text.replace(/^---$/gm, '<hr>');

    // Paragraphs
    text = text.replace(/^(?!<[hulo]|<li|<hr)(.+)$/gm, '<p>$1</p>');
    text = text.replace(/<p>\s*<\/p>/g, '');

    return text;
});

// Fetch data
const fetchInstructions = async () => {
    try {
        const res = await api.get('get-instructions/', {
            params: { pid, project_id: projectId, project_slug: projectSlug }
        });

        if (res.data.skip) {
            shouldSkip.value = true;
            const slug = projectSlug || projectId;
            // Skip instructions, go directly to annotate
            await api.post('onboarding/', { pid, project_slug: projectSlug, project_id: projectId });
            setTimeout(() => router.push(`/${slug}/annotate`), 500);
            return;
        }

        rawInstructions.value = res.data.content || '';
        practiceTask.value = res.data.practice_task || null;
        taskConfig.value = res.data.task_config || {};
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

    // Check classification
    classificationCorrect.value = !classOptions.value.length || practiceClassification.value === gold.classification;

    // Check spans (fuzzy match: same label and overlapping text)
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
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

.page-container {
    min-height: 100vh;
    padding: 40px 20px;
    background: linear-gradient(135deg, #f0f2f5 0%, #e8ecf1 100%);
    font-family: 'Outfit', sans-serif;
}

/* CARDS */
.card {
    background: white;
    max-width: 820px;
    margin: 0 auto;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    animation: slideUp 0.5s ease-out;
}

.card.wide {
    max-width: 900px;
}

.center-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 40px;
}

.task-card {
    background: white;
    max-width: 1000px;
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
}

.error {
    color: #dc3545;
    padding: 20px 40px;
}

/* INSTRUCTIONS BODY (markdown) */
.instructions-body {
    padding: 32px 40px;
    color: #1a1f36;
    line-height: 1.8;
    font-size: 1rem;
}

.instructions-body :deep(h1) {
    font-size: 1.6rem;
    font-weight: 700;
    color: #1a1f36;
    margin: 28px 0 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e3e8ee;
}

.instructions-body :deep(h2) {
    font-size: 1.3rem;
    font-weight: 600;
    color: #306ee8;
    margin: 24px 0 10px;
}

.instructions-body :deep(h3) {
    font-size: 1.1rem;
    font-weight: 600;
    color: #475569;
    margin: 20px 0 8px;
}

.instructions-body :deep(p) {
    margin: 8px 0;
    color: #334155;
}

.instructions-body :deep(ul) {
    padding-left: 20px;
    margin: 8px 0;
}

.instructions-body :deep(li) {
    margin: 6px 0;
    color: #334155;
}

.instructions-body :deep(strong) {
    color: #1a1f36;
    font-weight: 700;
}

.instructions-body :deep(code) {
    background: #f1f5f9;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.9em;
    color: #306ee8;
}

.instructions-body :deep(hr) {
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

.actions button,
.feedback-actions button {
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

.actions button:hover:not(:disabled),
.feedback-actions button:hover:not(:disabled) {
    background: #1a4ab9;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(48, 110, 232, 0.4);
}

.actions button:disabled,
.feedback-actions button:disabled {
    background: #ccc;
    cursor: not-allowed;
    box-shadow: none;
}

/* PRACTICE BANNER */
.practice-banner {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    padding: 14px;
    text-align: center;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.3px;
}

/* PRACTICE TASK LAYOUT (same as AnnotatorView) */
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

.doc-text-preview {
    font-size: 1.2rem;
    line-height: 1.8;
    color: #334155;
    background: #f8fafc;
    padding: 24px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
}

/* ACTION BUTTONS */
.action-btn {
    padding: 12px 24px;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    font-family: 'Outfit', sans-serif;
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
    font-family: 'Outfit', sans-serif;
    width: auto;
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

/* FEEDBACK */
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

.correct-text {
    color: #065f46;
}

.wrong-text {
    color: #991b1b;
}

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

/* LOADING */
.loader {
    width: 48px;
    height: 48px;
    border: 5px solid #e3e8ee;
    border-bottom-color: #306ee8;
    border-radius: 50%;
    animation: rotation 1s linear infinite;
    margin-bottom: 20px;
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

@keyframes rotation {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}
</style>
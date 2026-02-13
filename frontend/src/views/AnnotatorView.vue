<template>
    <div class="main-container">
        <header>
            <div class="user-info">User: {{ pid }}</div>
            <button @click="logout" class="logout-btn">Logout</button>
        </header>

        <div v-if="loading" class="loading">
            <p>Loading next task...</p>
        </div>

        <div v-else-if="!currentDoc && !stopped" class="finished">
            <h2>🎉 All tasks completed!</h2>
            <p>Thank you for your contribution.</p>
            <p>Redirecting to provider in {{ countdown }} seconds...</p>
        </div>

        <div v-else-if="stopped" class="finished">
            <h2>🎉 Session Ended</h2>
            <p>{{ stopMessage || "Thank you for your contribution." }}</p>
        </div>

        <div v-else-if="isSurvey" class="task-area survey-container">
            <div class="instructions">
                <h3>Preliminary Survey / Sondaggio Preliminare</h3>
                <p>Please answer the following questions to proceed.</p>
            </div>

            <div v-for="(q, idx) in surveyQuestions" :key="idx" class="survey-item">
                <label class="survey-label">{{ q.text }}</label>

                <!-- Multiple Choice -->
                <div v-if="q.options" class="survey-options">
                    <label v-for="opt in q.options" :key="opt" class="radio-label">
                        <input type="radio" :name="'q' + idx" :value="opt" v-model="surveyAnswers[idx]">
                        {{ opt }}
                    </label>
                </div>

                <!-- Free Text -->
                <input v-else type="text" class="survey-input" v-model="surveyAnswers[idx]"
                    placeholder="Your answer...">
            </div>

            <div class="actions">
                <button class="submit-btn" @click="submitSurvey" :disabled="!canSubmitSurvey">
                    Submit Survey
                </button>
            </div>
        </div>

        <div v-else class="task-area">

            <div v-if="isTraining" class="training-badge">
                TRAINING MODE (Feedback Enabled)
            </div>

            <div class="instructions">
                <h3>Task Instruction</h3>
                <p>{{ config.instruction || "Read the text below and complete the tasks." }}</p>
            </div>

            <div class="doc-text-preview" v-if="!hasHighlighter">
                {{ currentDoc.text }}
            </div>

            <div class="section classification-box" v-if="classOptions.length > 0">
                <h4>{{ config.question || "Classify this text:" }}</h4>

                <div class="input-group">
                    <label v-for="opt in classOptions" :key="opt.value" class="input-label"
                        :class="{ selected: isSelected(opt.value) }">
                        <input v-if="config.multi_select" type="checkbox" :value="opt.value" v-model="classification">
                        <input v-else type="radio" :value="opt.value" v-model="classification">
                        {{ opt.label }}
                    </label>
                </div>
            </div>



            <div class="section" v-if="hasHighlighter">
                <h4>Highlight Evidence</h4>
                <TextHighlighter :text="currentDoc.text" :labels="spanLabels" v-model:spans="spans" />
            </div>

            <div class="actions">
                <button class="submit-btn" @click="submitTask" :disabled="!canSubmit">
                    Submit & Next
                </button>
            </div>

            <p v-if="errorMsg" class="error">{{ errorMsg }}</p>
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
const config = ref({}); // Contiene l'intero JSON di configurazione
const startTime = ref(0); // Timer start timestamp
const countdown = ref(10);
let redirectTimer = null;
const stopped = ref(false);
const stopMessage = ref('');
const isSurvey = ref(false);
const surveyQuestions = ref([]); // [{text: "...", options: [...]}]
const surveyAnswers = ref({}); // {0: "Ans", 1: "..."}
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

// Computed Helper: True se c'è almeno una label di evidenziazione
const hasHighlighter = computed(() => spanLabels.value.length > 0);

onMounted(() => {
    if (!pid) router.push('/');
    fetchNextTask();
});

const fetchNextTask = async () => {
    loading.value = true;
    currentDoc.value = null;
    errorMsg.value = '';
    spans.value = [];
    stopped.value = false;

    const pid = localStorage.getItem('prolific_pid');
    const projectId = localStorage.getItem('project_id');

    if (!projectId) {
        errorMsg.value = "Fatal Error: No Project ID found. Please restart from link.";
        loading.value = false;
        return;
    }


    try {
        const res = await api.get(`next-task/?pid=${pid}&project_id=${projectId}`);

        // GESTIONE COMPLETAMENTO
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

        // CONTROL TYPE
        if (res.data.type === 'SURVEY') {
            currentDoc.value = null; // Ensure doc is null
            isSurvey.value = true;
            surveyQuestions.value = res.data.questions || [];
            surveyAnswers.value = {};
            loading.value = false;
            return;
        } else {
            isSurvey.value = false;
        }

        if (res.data.type === 'TRAINING') {
            isTraining.value = true;
        } else {
            isTraining.value = false;
        }

        currentDoc.value = res.data;
        config.value = res.data.project_config || {};

        // SETUP OPZIONI
        spanLabels.value = config.value.span_labels || [];
        classOptions.value = config.value.class_labels || [];

        // SETUP VARIABILE CLASSIFICAZIONE
        // Se è multiselect (checkbox), deve essere un Array vuoto []
        // Altrimenti (radio/scala), deve essere null
        if (config.value.multi_select) {
            classification.value = [];
        } else {
            classification.value = null;
        }

        // Start the timer
        startTime.value = Date.now();

    } catch (err) {
        if (err.response && err.response.status === 404) {
            // Task finiti ma senza redirect URL
        } else {
            errorMsg.value = "Error fetching task. Please refresh.";
        }
    } finally {
        loading.value = false;
    }
};

// Helper per lo stile CSS "selected" (gestisce sia array che valori singoli)
const isSelected = (val) => {
    if (Array.isArray(classification.value)) {
        return classification.value.includes(val);
    }
    return classification.value === val;
};

// Validazione: Il bottone Submit si attiva solo se...
const canSubmit = computed(() => {
    // 1. Se ci sono domande (Radio/Checkbox), bisogna rispondere
    if (classOptions.value.length > 0) {
        if (Array.isArray(classification.value)) {
            return classification.value.length > 0; // Checkbox: almeno una
        }
        return classification.value !== null; // Radio: selezionato
    }

    // 2. Se c'è SOLO l'evidenziatore (NER puro), l'invio è sempre possibile
    // (perché potrebbe non esserci nulla da evidenziare nel testo)
    return true;
});

const submitTask = async () => {
    if (!canSubmit.value) return; // double check

    // Calculate duration
    const endTime = Date.now();
    const duration = (endTime - startTime.value);

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
    // Check if all questions have an answer (basic check)
    if (surveyQuestions.value.length === 0) return true;
    // Check if we have keys for all indices
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
        // Reload to get next step (Training or Task)
        fetchNextTask();
    } catch (err) {
        errorMsg.value = "Error submitting survey. " + (err.response?.data?.error || err.message);
        loading.value = false;
    }
};

const logout = () => {
    localStorage.removeItem('prolific_pid');
    router.push('/');
};
</script>

<style scoped>
.main-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'Segoe UI', sans-serif;
}

header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}

.task-area {
    display: flex;
    flex-direction: column;
    gap: 25px;
}

/* STILE PREVIEW TESTO (Quando non c'è evidenziatore) */
.doc-text-preview {
    padding: 20px;
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 1.1rem;
    line-height: 1.6;
}

/* STILI CLASSIFICAZIONE */
.classification-box {
    background: #eef2f5;
    padding: 20px;
    border-radius: 8px;
}

.input-group {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
}

.input-label {
    background: white;
    padding: 10px 20px;
    border-radius: 6px;
    border: 1px solid #ccc;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 8px;
    user-select: none;
    /* Evita selezione testo involontaria */
}

.input-label:hover {
    border-color: #666;
}

.input-label.selected {
    background: #007bff;
    color: white;
    border-color: #0056b3;
}


/* REMOVED SCALE STYLES */

/* SUBMIT BUTTON */
.submit-btn {
    width: 100%;
    padding: 15px;
    background-color: #28a745;
    color: white;
    font-size: 1.2rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    margin-top: 10px;
}

.submit-btn:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.logout-btn {
    background: none;
    border: 1px solid #ccc;
    padding: 5px 10px;
    cursor: pointer;
}

.error {
    color: red;
    margin-top: 10px;
    font-weight: bold;
}

.finished {
    text-align: center;
    padding: 60px 20px;
    background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    animation: fadeIn 0.5s ease-out;
}

.finished h2 {
    color: #2e7d32;
    margin-bottom: 15px;
    font-size: 2rem;
}

.finished p {
    font-size: 1.1rem;
    color: #333;
    margin: 10px 0;
}

.loading {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 200px;
    font-size: 1.2rem;
    color: #666;
    animation: pulse 1.5s infinite;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulse {
    0% {
        opacity: 0.6;
    }

    50% {
        opacity: 1;
    }

    100% {
        opacity: 0.6;
    }
}

.training-badge {
    background: #ffc107;
    color: #333;
    padding: 10px;
    text-align: center;
    font-weight: bold;
    border-radius: 6px;
    border: 1px solid #e0a800;
}

.survey-container {
    background: #fff;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.survey-item {
    margin-bottom: 25px;
    padding-bottom: 15px;
    border-bottom: 1px solid #f0f0f0;
}

.survey-label {
    display: block;
    font-weight: 600;
    margin-bottom: 10px;
    font-size: 1.1rem;
    color: #444;
}

.survey-input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    font-size: 1rem;
}

.survey-options {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.radio-label {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    font-size: 1rem;
}
</style>
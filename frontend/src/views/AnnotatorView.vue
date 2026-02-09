<template>
    <div class="main-container">
        <header>
            <div class="user-info">User: {{ pid }}</div>
            <button @click="logout" class="logout-btn">Logout</button>
        </header>

        <div v-if="loading" class="loading">
            <p>Loading next task...</p>
        </div>

        <div v-else-if="!currentDoc" class="finished">
            <h2>🎉 All tasks completed!</h2>
            <p>Thank you for your contribution.</p>
        </div>

        <div v-else class="task-area">
            <div class="instructions">
                <h3>Task Instruction</h3>
                <p>1. Leggi il testo. 2. Classificalo. 3. Evidenzia le parti chiave se presenti.</p>
            </div>

            <div class="section classification-box">
                <h4>Does this text contain a conspiracy theory?</h4>
                <div class="radio-group">
                    <label v-for="opt in classOptions" :key="opt.value" class="radio-label"
                        :class="{ selected: classification === opt.value }">
                        <input type="radio" :value="opt.value" v-model="classification">
                        {{ opt.label }}
                    </label>
                </div>
            </div>

            <div class="section">
                <h4>Highlight Evidence (Actor, Victim, etc.)</h4>
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
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../axios';
import TextHighlighter from '../components/TextHighlighter.vue';

const router = useRouter();
const pid = localStorage.getItem('prolific_pid');
const loading = ref(true);
const currentDoc = ref(null);
const errorMsg = ref('');

// STATO DELLE ANNOTAZIONI
const classification = ref(null);
const spans = ref([]);

// CONFIGURAZIONE (Arriva dal backend)
const spanLabels = ref([]);   // es. Actor, Victim
const classOptions = ref([]); // es. Yes, No

// LOGICA
onMounted(() => {
    if (!pid) router.push('/');
    fetchNextTask();
});

const fetchNextTask = async () => {
    loading.value = true;
    currentDoc.value = null;
    errorMsg.value = '';

    // Reset risposte
    classification.value = null;
    spans.value = [];

    try {
        const res = await api.get(`next-task/?pid=${pid}`);
        if (res.data.status === 'completed') {
            currentDoc.value = null;
            // Mostriamo il link di completamento
            // window.location.href = res.data.completion_url; // Reindirizza AUTOMATICAMENTE su Prolific
            return;
        }
        currentDoc.value = res.data;

        // Configuriamo l'interfaccia basandoci sui dati del backend
        const config = res.data.project_config || {};

        // Fallback se il config è vuoto (per sicurezza)
        spanLabels.value = config.span_labels || [];
        classOptions.value = config.class_labels || [
            { value: 'Yes', label: 'Yes' }, { value: 'No', label: 'No' }
        ];

    } catch (err) {
        if (err.response && err.response.status === 404) {
            // Niente più task
            currentDoc.value = null;
        } else {
            errorMsg.value = "Error fetching task. Please refresh.";
        }
    } finally {
        loading.value = false;
    }
};

const canSubmit = computed(() => {
    // Obblighiamo almeno a rispondere alla domanda Sì/No
    return classification.value !== null;
});

const submitTask = async () => {
    if (!canSubmit.value) return;
    loading.value = true;

    const payload = {
        pid: pid,
        document: currentDoc.value.id,
        result: {
            classification: classification.value,
            spans: spans.value
        },
        seconds_to_complete: 0 // TODO: Aggiungi un timer vero qui!
    };

    try {
        await api.post('submit/', payload);
        // Se va bene, carica il prossimo
        fetchNextTask();
    } catch (err) {
        errorMsg.value = "Error saving. Try again.";
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
    margin-bottom: 30px;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}

.section {
    margin-bottom: 30px;
}

h4 {
    margin-bottom: 10px;
    color: #333;
}

/* Classificazione Box */
.classification-box {
    background: #eef2f5;
    padding: 20px;
    border-radius: 8px;
}

.radio-group {
    display: flex;
    gap: 15px;
}

.radio-label {
    background: white;
    padding: 10px 20px;
    border-radius: 6px;
    border: 1px solid #ccc;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 8px;
}

.radio-label:hover {
    border-color: #666;
}

.radio-label.selected {
    background: #007bff;
    color: white;
    border-color: #0056b3;
}

/* Submit Button */
.submit-btn {
    width: 100%;
    padding: 15px;
    background-color: #28a745;
    color: white;
    font-size: 1.2rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
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
</style>
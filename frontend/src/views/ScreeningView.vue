<template>
    <div class="page-container">
        <div class="card wide">
            <div class="card-header">
                <h1>About You</h1>
                <p class="subtitle">Please answer the following questions before starting the task.</p>
            </div>

            <div v-if="loading" class="state-text" style="padding: 30px 40px;">Loading screening...</div>
            <div v-else-if="errorMsg" class="error">{{ errorMsg }}</div>
            <div v-else-if="shouldSkip" class="state-text" style="padding: 30px 40px;">No screening required. Redirecting...</div>

            <div v-else class="questions-container">
                <div v-for="(q, index) in questions" :key="q.id" class="question-block">
                    <label class="question-label">
                        <span class="question-number">{{ index + 1 }}.</span>
                        {{ q.label }}
                        <span v-if="q.required" class="required-star">*</span>
                    </label>

                    <!-- TEXT -->
                    <input v-if="q.type === 'text'" type="text" v-model="responses[q.id]"
                        :placeholder="q.placeholder || ''" class="input-field" />

                    <!-- NUMBER -->
                    <input v-if="q.type === 'number'" type="number" v-model.number="responses[q.id]" :min="q.min"
                        :max="q.max" :placeholder="q.placeholder || ''" class="input-field" />

                    <!-- TEXTAREA -->
                    <textarea v-if="q.type === 'textarea'" v-model="responses[q.id]" :placeholder="q.placeholder || ''"
                        class="input-field textarea-field" rows="3"></textarea>

                    <!-- SELECT -->
                    <select v-if="q.type === 'select'" v-model="responses[q.id]" class="input-field">
                        <option value="" disabled>Select an option...</option>
                        <option v-for="opt in q.options" :key="opt" :value="opt">{{ opt }}</option>
                    </select>

                    <!-- RADIO -->
                    <div v-if="q.type === 'radio'" class="options-group">
                        <label v-for="opt in q.options" :key="opt" class="radio-label"
                            :class="{ active: responses[q.id] === opt }">
                            <input type="radio" :value="opt" v-model="responses[q.id]" />
                            {{ opt }}
                        </label>
                    </div>

                    <!-- MULTI_SELECT -->
                    <div v-if="q.type === 'multi_select'" class="options-group">
                        <label v-for="opt in q.options" :key="opt" class="checkbox-label-option"
                            :class="{ active: (responses[q.id] || []).includes(opt) }">
                            <input type="checkbox" :value="opt" v-model="responses[q.id]" />
                            {{ opt }}
                        </label>
                    </div>

                    <!-- LIKERT -->
                    <div v-if="q.type === 'likert'" class="likert-container">
                        <span class="likert-anchor">{{ (q.anchors && q.anchors[0]) || '1' }}</span>
                        <div class="likert-scale">
                            <label v-for="n in (q.scale || 5)" :key="n" class="likert-option"
                                :class="{ active: responses[q.id] === n }">
                                <input type="radio" :value="n" v-model="responses[q.id]" />
                                {{ n }}
                            </label>
                        </div>
                        <span class="likert-anchor">{{ (q.anchors && q.anchors[1]) || (q.scale || 5) }}</span>
                    </div>
                </div>
            </div>

            <div v-if="!loading && !shouldSkip && questions.length > 0" class="actions">
                <p v-if="validationError" class="validation-error">{{ validationError }}</p>
                <button @click="submitScreening" :disabled="submitting">
                    {{ submitting ? 'Saving...' : 'Continue' }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../axios';
import { useProjectContext } from '../composables/useProjectContext';

const router = useRouter();
const { pid, projectSlug, projectId } = useProjectContext();

const loading = ref(true);
const errorMsg = ref('');
const shouldSkip = ref(false);
const submitting = ref(false);
const validationError = ref('');

const questions = ref([]);
const responses = reactive({});

const fetchScreening = async () => {
    try {
        const res = await api.get('get-screening/', {
            params: { pid, project_id: projectId, project_slug: projectSlug }
        });

        if (res.data.skip) {
            shouldSkip.value = true;
            const slug = projectSlug || projectId;
            setTimeout(() => router.push(`/${slug}/instructions`), 500);
            return;
        }

        questions.value = res.data.questions || [];

        for (const q of questions.value) {
            if (q.type === 'multi_select') {
                responses[q.id] = [];
            } else {
                responses[q.id] = q.type === 'number' ? null : '';
            }
        }
    } catch (err) {
        if (err.response?.status === 400 && err.response?.data?.error === 'Screening already completed') {
            const slug = projectSlug || projectId;
            router.push(`/${slug}/codebook`);
            return;
        }
        errorMsg.value = "Error loading screening. " + (err.response?.data?.error || err.message);
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    if (!pid) {
        router.push('/');
        return;
    }
    fetchScreening();
});

const submitScreening = async () => {
    validationError.value = '';

    for (const q of questions.value) {
        if (q.required) {
            const val = responses[q.id];
            if (val === null || val === undefined || val === '') {
                validationError.value = `Please answer: "${q.label}"`;
                return;
            }
            if (Array.isArray(val) && val.length === 0) {
                validationError.value = `Please select at least one option for: "${q.label}"`;
                return;
            }
        }
    }

    submitting.value = true;

    try {
        await api.post('screening/', {
            pid,
            project_slug: projectSlug,
            project_id: projectId,
            responses: { ...responses }
        });

        const slug = projectSlug || projectId;
        router.push(`/${slug}/codebook`);
    } catch (err) {
        validationError.value = err.response?.data?.error || "Error saving screening. Please try again.";
    } finally {
        submitting.value = false;
    }
};
</script>

<style scoped>
@import '../assets/shared.css';

/* ── QUESTIONS ── */
.questions-container {
    display: flex;
    flex-direction: column;
    gap: 28px;
    padding: 30px 40px;
}

.question-block {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.question-label {
    font-weight: 600;
    font-size: 1rem;
    color: #1a1f36;
    display: flex;
    align-items: baseline;
    gap: 6px;
}

.question-number {
    color: #306ee8;
    font-weight: 700;
    min-width: 20px;
}

.required-star {
    color: #dc2626;
    font-weight: 700;
}

/* ── INPUT FIELDS ── */
.input-field {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e3e8ee;
    border-radius: 10px;
    font-size: 0.95rem;
    font-family: 'Outfit', sans-serif;
    transition: all 0.2s;
    box-sizing: border-box;
    background: #f8fafc;
    color: #1a1f36;
}

.input-field:focus {
    outline: none;
    border-color: #306ee8;
    background: white;
    box-shadow: 0 0 0 3px rgba(48, 110, 232, 0.1);
}

.textarea-field {
    resize: vertical;
    min-height: 80px;
}

select.input-field {
    appearance: auto;
    cursor: pointer;
}

/* ── RADIO & CHECKBOX OPTIONS ── */
.options-group {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.radio-label,
.checkbox-label-option {
    background: #f8fafc;
    border: 2px solid #e3e8ee;
    padding: 10px 20px;
    border-radius: 10px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    user-select: none;
    font-size: 0.9rem;
}

.radio-label:hover,
.checkbox-label-option:hover {
    border-color: #cbd5e1;
    background: white;
}

.radio-label.active,
.checkbox-label-option.active {
    background: #306ee8;
    color: white;
    border-color: #1a4ab9;
    box-shadow: 0 4px 12px rgba(48, 110, 232, 0.25);
}

.radio-label input,
.checkbox-label-option input {
    display: none;
}

/* ── LIKERT SCALE ── */
.likert-container {
    display: flex;
    align-items: center;
    gap: 12px;
}

.likert-anchor {
    font-size: 0.8rem;
    color: #64748b;
    font-weight: 500;
    min-width: 60px;
    text-align: center;
}

.likert-scale {
    display: flex;
    gap: 8px;
    flex: 1;
    justify-content: center;
}

.likert-option {
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #e3e8ee;
    border-radius: 50%;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s;
    background: #f8fafc;
    color: #475569;
}

.likert-option:hover {
    border-color: #306ee8;
    background: #eff6ff;
}

.likert-option.active {
    background: #306ee8;
    color: white;
    border-color: #1a4ab9;
    box-shadow: 0 4px 12px rgba(48, 110, 232, 0.3);
    transform: scale(1.1);
}

.likert-option input {
    display: none;
}

/* ── VALIDATION ── */
.validation-error {
    color: #dc2626;
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 12px;
    padding: 10px 16px;
    background: #fef2f2;
    border-radius: 8px;
    border-left: 4px solid #dc2626;
}
</style>

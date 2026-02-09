<template>
    <div class="page-container">
        <div class="card">
            <h1>Informed Consent</h1>
            <div class="scroll-box">
                <p><strong>Project:</strong> PsyCoMark Study</p>
                <p><strong>Goal:</strong> We are studying linguistic markers in online text...</p>
                <p><strong>Data:</strong> Your answers will be anonymous...</p>
                <p><strong>Rights:</strong> You can withdraw at any time...</p>
            </div>

            <div class="actions">
                <label>
                    <input type="checkbox" v-model="accepted">
                    I have read and understood the information above.
                </label>
                <button @click="submitConsent" :disabled="!accepted">I Agree</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../axios';

const router = useRouter();
const accepted = ref(false);
const pid = localStorage.getItem('prolific_pid');

const submitConsent = async () => {
    await api.post('consent/', { pid });
    router.push('/instructions');
};
</script>

<style scoped>
.page-container {
    display: flex;
    justify-content: center;
    padding: 50px;
}

.card {
    background: white;
    padding: 30px;
    max-width: 600px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.scroll-box {
    height: 300px;
    overflow-y: scroll;
    border: 1px solid #eee;
    padding: 15px;
    margin: 20px 0;
    background: #fafafa;
}

button {
    background: #007bff;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    margin-top: 20px;
}

button:disabled {
    background: #ccc;
}
</style>
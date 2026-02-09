<template>
    <div class="page-container">
        <div class="card wide">
            <h1>Instructions</h1>

            <div class="section">
                <h3>1. The Goal</h3>
                <p>You will read reddit comments. Your task is to identify if they contain a conspiracy theory.</p>
            </div>

            <div class="section">
                <h3>2. Definitions (The Tags)</h3>
                <ul>
                    <li><strong style="color:#FF5733">Actor:</strong> Who is doing the conspiracy? (e.g., "The FBI",
                        "They")</li>
                    <li><strong style="color:#33FF57">Action:</strong> What are they doing? (e.g., "hiding", "faking")
                    </li>
                    <li><strong style="color:#3357FF">Victim:</strong> Who is being hurt? (e.g., "the people", "me")
                    </li>
                </ul>
            </div>

            <div class="section example-box">
                <h3>3. Worked Example</h3>
                <p class="comment">"The government is putting chips in the water to control us."</p>
                <div class="explanation">
                    <p><strong>Conspiracy?</strong> Yes.</p>
                    <p><strong>Highlights:</strong></p>
                    <ul>
                        <li><span class="badge" style="background:#FF5733">Actor</span> = "The government"</li>
                        <li><span class="badge" style="background:#33FF57">Action</span> = "putting chips"</li>
                        <li><span class="badge" style="background:#3357FF">Victim</span> = "us"</li>
                    </ul>
                </div>
            </div>

            <div class="actions">
                <p>When you are ready, click below to start the qualification task.</p>
                <button @click="finishInstructions">Start Task</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import api from '../axios';

const router = useRouter();
const pid = localStorage.getItem('prolific_pid');

const finishInstructions = async () => {
    // Qui potresti mandarlo a una pagina "Training" separata se vuoi il quiz
    // Per ora lo mandiamo diretti all'annotazione segnando l'onboarding come finito
    await api.post('onboarding/', { pid });
    router.push('/annotate');
};
</script>

<style scoped>
.page-container {
    padding: 40px;
}

.card {
    background: white;
    padding: 40px;
    max-width: 800px;
    margin: 0 auto;
    border-radius: 8px;
}

.example-box {
    background: #f0f8ff;
    padding: 20px;
    border-left: 5px solid #007bff;
    margin: 20px 0;
}

.badge {
    color: white;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.8rem;
    margin-right: 5px;
}

.comment {
    font-style: italic;
    font-size: 1.1rem;
    margin-bottom: 10px;
}

button {
    background: #28a745;
    color: white;
    padding: 15px 30px;
    font-size: 1.2rem;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}
</style>
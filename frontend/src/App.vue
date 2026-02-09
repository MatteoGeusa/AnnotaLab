<script setup>
import { ref, onMounted } from 'vue'
import api from './services/api';

const backendMessage = ref('Waiting for response...')

const healthCheck = async () => {
  try {
    const response = await api.get('/healthcheck'); 
    backendMessage.value = response.data.message;
  } catch (error) {
    backendMessage.value = "Connection error!";
  }
}

onMounted(() => {
  healthCheck()
})
</script>

<template>
  <div style="text-align: center; margin-top: 50px;">
    <h1>Integration Test</h1>
    <p style="font-size: 20px; color: green;">
      {{ backendMessage }}
    </p>
  </div>
</template>
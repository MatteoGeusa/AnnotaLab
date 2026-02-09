<script setup>
import { ref, onMounted } from 'vue'
import api from './services/api';

const messaggioDalBackend = ref('In attesa di risposta...')

const healtcheck = async () => {
  try {
    const response = await api.get('/test'); 
    messaggioDalBackend.value = response.data.messaggio;
  } catch (error) {
    messaggioDalBackend.value = "Errore di connessione!";
  }
}

onMounted(() => {
  healtcheck()
})
</script>

<template>
  <div style="text-align: center; margin-top: 50px;">
    <h1>Test Integrazione</h1>
    <p style="font-size: 20px; color: green;">
      {{ messaggioDalBackend }}
    </p>
  </div>
</template>
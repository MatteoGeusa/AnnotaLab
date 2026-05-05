<template>
  <div class="annotation-block span-highlight-block">
    <TextHighlighter
      :text="text"
      :labels="config.labels || []"
      v-model:spans="localSpans"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import TextHighlighter from '../TextHighlighter.vue';

const props = defineProps({
  text:       { type: String, required: true },
  // config = the component entry from annotation_schema.components
  // { type: 'span_highlight', labels: [{name, color, hover_hint?}] }
  config:     { type: Object, required: true },
  modelValue: { type: Array, default: () => [] },
});

const emit = defineEmits(['update:modelValue']);

const localSpans = ref([...props.modelValue]);
watch(localSpans, (val) => emit('update:modelValue', val), { deep: true });

const reset = () => { localSpans.value = []; };
defineExpose({ reset });
</script>



<style scoped>
@import '../../assets/shared.css';
</style>


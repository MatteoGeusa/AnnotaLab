<template>
  <div class="annotation-block classification-block">
    <div class="question-title">
      {{ config.question || 'Classify this text:' }}
    </div>
    <div class="options-grid">
      <label
        v-for="opt in config.options || []"
        :key="opt.value"
        class="option-label"
        :class="{ active: isSelected(opt.value) }"
        :title="opt.hover_hint || ''"
      >
        <input
          v-if="config.multi_select"
          type="checkbox"
          :value="opt.value"
          v-model="localValue"
        />
        <input
          v-else
          type="radio"
          :value="opt.value"
          v-model="localValue"
        />
        <span class="check-icon"></span>
        {{ opt.label }}
      </label>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  // config = the component entry from annotation_schema.components
  // { type: 'classification', question?, multi_select?, options: [{label, value, hover_hint?}] }
  config:     { type: Object, required: true },
  modelValue: { default: null },
});

const emit = defineEmits(['update:modelValue']);

const localValue = ref(props.config.multi_select ? [] : null);

watch(localValue, (val) => emit('update:modelValue', val), { deep: true });

const isSelected = (val) =>
  Array.isArray(localValue.value)
    ? localValue.value.includes(val)
    : localValue.value === val;

const reset = () => { localValue.value = props.config.multi_select ? [] : null; };
defineExpose({ reset });
</script>

<style scoped>
.options-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.option-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}
.option-label input {
  margin-right: 10px;
}
</style>

<style scoped>
@import '../../assets/shared.css';
</style>

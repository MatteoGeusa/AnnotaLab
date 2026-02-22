<template>
    <div class="highlighter-container">
        <div class="toolbar" v-if="labels.length > 0">
            <div class="toolbar-brand">
                <span class="toolbar-icon">🖋️</span>
                <span class="toolbar-text">Highlighter</span>
            </div>
            <div class="label-chips">
                <button v-for="(label, idx) in labels" :key="label.name" :style="{
                    backgroundColor: selectedLabel === label.name ? label.color : 'white',
                    color: selectedLabel === label.name ? 'white' : '#4f566b',
                    borderColor: selectedLabel === label.name ? 'transparent' : '#e3e8ee'
                }" class="label-chip" @click="selectedLabel = label.name"
                    :class="{ active: selectedLabel === label.name }" :title="label.hover_hint">
                    <span class="chip-name">{{ label.name }}</span>
                    <span class="chip-key">{{ idx + 1 }}</span>
                </button>
            </div>
        </div>

        <div class="text-card-area" ref="textRef" @mouseup="handleSelection">
            <template v-for="(chunk, index) in renderChunks" :key="index">
                <span v-if="chunk.isHighlight" class="highlight-span"
                    :style="{ backgroundColor: getLabelColor(chunk.label) + '33', borderBottomColor: getLabelColor(chunk.label) }">
                    <span class="highlight-text">{{ chunk.text }}</span>
                    <span class="highlight-tag" :style="{ backgroundColor: getLabelColor(chunk.label) }">
                        {{ chunk.label }}
                        <button class="remove-chip-btn" @click.stop="removeSpan(chunk.id)">×</button>
                    </span>
                </span>
                <span v-else class="normal-text">{{ chunk.text }}</span>
            </template>
        </div>

        <div v-if="showPopup" class="popup-overlay" @click.self="closePopup">
            <div class="popup-modal">
                <div class="popup-icon">⚠️</div>
                <p class="popup-message">{{ popupMessage }}</p>
                <button class="popup-btn" @click="closePopup">Understood</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';

const props = defineProps({
    text: String,
    labels: Array,
    spans: {
        type: Array,
        default: () => []
    }
});

const emit = defineEmits(['update:spans']);

const selectedLabel = ref(null);
const textRef = ref(null);

// Popup State
const showPopup = ref(false);
const popupMessage = ref("");

const openPopup = (msg) => {
    popupMessage.value = msg;
    showPopup.value = true;
};

const closePopup = () => {
    showPopup.value = false;
};

// Keydown listener for labels 1-9
const handleKeydown = (e) => {
    const key = parseInt(e.key);
    if (!isNaN(key) && key > 0 && key <= props.labels.length) {
        selectedLabel.value = props.labels[key - 1].name;
    }
};

onMounted(() => {
    window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown);
});

watch(() => props.labels, (newLabels) => {
    if (newLabels && newLabels.length > 0 && !selectedLabel.value) {
        selectedLabel.value = newLabels[0].name;
    }
}, { immediate: true });


const getGlobalOffset = (root, targetNode, targetOffset) => {
    let offset = 0;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode: (node) => {
            if (node.parentNode && (node.parentNode.classList.contains('remove-chip-btn') || node.parentNode.classList.contains('highlight-tag'))) {
                return NodeFilter.FILTER_REJECT;
            }
            return NodeFilter.FILTER_ACCEPT;
        }
    });

    while (walker.nextNode()) {
        const node = walker.currentNode;
        if (node === targetNode) {
            return offset + targetOffset;
        }
        offset += node.nodeValue.length;
    }
    return -1;
};

const handleSelection = () => {
    const selection = window.getSelection();
    if (selection.rangeCount === 0 || selection.isCollapsed) return;

    const range = selection.getRangeAt(0);
    const container = textRef.value;

    if (!container.contains(range.commonAncestorContainer)) {
        selection.removeAllRanges();
        return;
    }

    const start = getGlobalOffset(container, range.startContainer, range.startOffset);
    const end = getGlobalOffset(container, range.endContainer, range.endOffset);

    if (start === -1 || end === -1) {
        selection.removeAllRanges();
        return;
    }

    let realStart = Math.min(start, end);
    let realEnd = Math.max(start, end);

    let tempSegment = props.text.slice(realStart, realEnd);
    const leadingSpaces = tempSegment.length - tempSegment.trimStart().length;
    const trailingSpaces = tempSegment.length - tempSegment.trimEnd().length;

    realStart += leadingSpaces;
    realEnd -= trailingSpaces;

    while (realStart > 0 && !/\s/.test(props.text[realStart - 1])) {
        realStart--;
    }
    while (realEnd < props.text.length && !/\s/.test(props.text[realEnd])) {
        realEnd++;
    }

    let textSegment = props.text.slice(realStart, realEnd);

    if (!textSegment.trim()) {
        selection.removeAllRanges();
        return;
    }

    textSegment = textSegment.trim();

    if (!selectedLabel.value) {
        openPopup("Please select a label first!");
        selection.removeAllRanges();
        return;
    }

    const hasOverlap = props.spans.some(span => {
        return (realStart < span.end && realEnd > span.start);
    });

    if (hasOverlap) {
        openPopup("Warning: Overlapping highlights are not allowed. Please remove the existing one first.");
        selection.removeAllRanges();
        return;
    }

    const newSpan = {
        start: realStart,
        end: realEnd,
        label: selectedLabel.value,
        text: textSegment,
        id: Date.now()
    };

    emit('update:spans', [...props.spans, newSpan]);
    selection.removeAllRanges();
};

const removeSpan = (spanId) => {
    const filtered = props.spans.filter(s => s.id !== spanId);
    emit('update:spans', filtered);
};

const getLabelColor = (labelName) => {
    const l = props.labels.find(x => x.name === labelName);
    return l ? l.color : '#cbd5e1';
};

const renderChunks = computed(() => {
    if (!props.text) return [];

    const sortedSpans = [...props.spans].sort((a, b) => a.start - b.start);
    const chunks = [];
    let currentIndex = 0;

    sortedSpans.forEach(span => {
        if (span.start > currentIndex) {
            chunks.push({
                text: props.text.slice(currentIndex, span.start),
                isHighlight: false
            });
        }

        chunks.push({
            text: props.text.slice(span.start, span.end),
            isHighlight: true,
            label: span.label,
            id: span.id
        });

        currentIndex = span.end;
    });

    if (currentIndex < props.text.length) {
        chunks.push({
            text: props.text.slice(currentIndex),
            isHighlight: false
        });
    }

    return chunks;
});
</script>

<style scoped>
.highlighter-container {
    display: flex;
    flex-direction: column;
    gap: 0;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e3e8ee;
    background: white;
}

.toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background-color: #e3effb;
    border-bottom: 1px solid #d1d9e6;
}

.toolbar-brand {
    display: flex;
    align-items: center;
    gap: 8px;
}

.toolbar-icon {
    font-size: 1.2rem;
}

.toolbar-text {
    font-weight: 700;
    font-size: 0.9rem;
    color: #1a1f36;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.label-chips {
    display: flex;
    gap: 8px;
}

.label-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 50px;
    border: 1px solid;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.85rem;
    transition: all 0.2s;
    background: white;
}

.chip-key {
    background: rgba(0, 0, 0, 0.1);
    width: 18px;
    height: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    font-size: 0.7rem;
}

.label-chip.active {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
}

.label-chip.active .chip-key {
    background: rgba(255, 255, 255, 0.3);
}

.text-card-area {
    font-size: 1.15rem;
    line-height: 2.6;
    /* Balanced line height for labels and readability */
    padding: 35px;
    min-height: 250px;
    white-space: pre-wrap;
    cursor: text;
    background-color: #fdfdfd;
    color: #1e293b;
    /* Darker, higher contrast text */
}

.normal-text {
    color: inherit;
}

/* PREMIUM HIGHLIGHT STYLES */
.highlight-span {
    padding: 2px 0;
    margin: 0 1px;
    border-bottom: 2px solid;
    position: relative;
    display: inline;
    border-radius: 2px;
}

.highlight-text {
    /* Keep text clear */
    position: relative;
    z-index: 2;
}

.highlight-tag {
    position: absolute;
    top: 1.6rem;
    /* Perfectly centered between lines */
    left: 4px;
    font-size: 0.55rem;
    font-weight: 800;
    color: white;
    padding: 0 6px;
    border-radius: 3px;
    text-transform: uppercase;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    user-select: none;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
    z-index: 10;
    white-space: nowrap;
    height: 14px;
    letter-spacing: 0.3px;
}

.remove-chip-btn {
    background: rgba(0, 0, 0, 0.2);
    border: none;
    color: white;
    border-radius: 50%;
    width: 14px;
    height: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 10px;
    padding: 0;
    transition: background 0.2s;
}

.remove-chip-btn:hover {
    background: rgba(0, 0, 0, 0.5);
}

/* POPUP MODAL (Premium Look) */
.popup-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(26, 31, 54, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 2000;
}

.popup-modal {
    background: white;
    padding: 32px;
    border-radius: 20px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
    text-align: center;
    max-width: 400px;
    width: 90%;
    animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.popup-icon {
    font-size: 3rem;
    margin-bottom: 16px;
}

.popup-message {
    font-size: 1.1rem;
    color: #4f566b;
    margin-bottom: 24px;
    line-height: 1.5;
}

.popup-btn {
    padding: 10px 30px;
    background: #306ee8;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s;
}

.popup-btn:hover {
    background: #1a4ab9;
    transform: scale(1.05);
}

@keyframes popIn {
    from {
        opacity: 0;
        transform: scale(0.8);
    }

    to {
        opacity: 1;
        transform: scale(1);
    }
}
</style>

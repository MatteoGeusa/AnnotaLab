<template>
    <div class="highlighter-container">
        <div class="toolbar" v-if="labels.length > 0">
            <span class="toolbar-label">Seleziona etichetta:</span>
            <button v-for="label in labels" :key="label.name" :style="{
                backgroundColor: selectedLabel === label.name ? label.color : '#f0f0f0',
                color: selectedLabel === label.name ? 'white' : 'black',
                borderColor: label.color
            }" class="label-btn" @click="selectedLabel = label.name">
                {{ label.name }}
            </button>
        </div>

        <div class="text-area" ref="textRef" @mouseup="handleSelection">
            <template v-for="(chunk, index) in renderChunks" :key="index">
                <span v-if="chunk.isHighlight" class="highlight"
                    :style="{ backgroundColor: getLabelColor(chunk.label) }">{{ chunk.text }}<button class="remove-btn"
                        @click.stop="removeSpan(chunk.id)">×</button></span>
                <span v-else>{{ chunk.text }}</span>
            </template>
        </div>

        <!-- Popup Modal -->
        <div v-if="showPopup" class="popup-overlay" @click.self="closePopup">
            <div class="popup-content">
                <p class="popup-message">{{ popupMessage }}</p>
                <button class="popup-close-btn" @click="closePopup">OK</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

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

// Stato per il popup
const showPopup = ref(false);
const popupMessage = ref("");

const openPopup = (msg) => {
    popupMessage.value = msg;
    showPopup.value = true;
};

const closePopup = () => {
    showPopup.value = false;
};

watch(() => props.labels, (newLabels) => {
    if (newLabels && newLabels.length > 0 && !selectedLabel.value) {
        selectedLabel.value = newLabels[0].name;
    }
}, { immediate: true });

// --- FUNZIONE CRITICA: Calcola l'offset assoluto ---
// Cammina nel DOM per contare i caratteri reali prima del nodo selezionato
const getGlobalOffset = (root, targetNode, targetOffset) => {
    let offset = 0;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode: (node) => {
            // Ignoriamo i nodi di testo dentro i bottoni (la "x")
            // ed eventuali spazi vuoti generati dal layout se non fanno parte del testo
            if (node.parentNode && node.parentNode.classList.contains('remove-btn')) {
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
    return -1; // Non trovato
};

const handleSelection = () => {
    const selection = window.getSelection();
    if (selection.rangeCount === 0 || selection.isCollapsed) return;

    const range = selection.getRangeAt(0);
    const container = textRef.value;

    // 1. Verifica che la selezione sia dentro il nostro container
    if (!container.contains(range.commonAncestorContainer)) {
        selection.removeAllRanges();
        return;
    }

    // 2. Calcola Start e End globali usando la funzione robusta
    const start = getGlobalOffset(container, range.startContainer, range.startOffset);
    const end = getGlobalOffset(container, range.endContainer, range.endOffset);

    // Se qualcosa è andato storto nel calcolo, esci
    if (start === -1 || end === -1) {
        selection.removeAllRanges();
        return;
    }

    // 3. Normalizza (se l'utente ha selezionato da destra a sinistra)
    let realStart = Math.min(start, end);
    let realEnd = Math.max(start, end);
    let textSegment = props.text.slice(realStart, realEnd);

    // 4. Controllo Spazi Vuoti e Trimming
    if (!textSegment.trim()) {
        selection.removeAllRanges();
        return;
    }

    // 4b. Rimuovi spazi vuoti agli estremi della selezione
    const leadingSpaces = textSegment.length - textSegment.trimStart().length;
    const trailingSpaces = textSegment.length - textSegment.trimEnd().length;

    realStart += leadingSpaces;
    realEnd -= trailingSpaces;
    textSegment = textSegment.trim();

    // 4. Controllo Etichetta
    if (!selectedLabel.value) {
        openPopup("Seleziona prima un'etichetta!");
        selection.removeAllRanges();
        return;
    }

    // 5. Controllo Sovrapposizioni (Importante!)
    // Impediamo di creare annotazioni che si accavallano, causerebbero bug visivi
    const hasOverlap = props.spans.some(span => {
        return (realStart < span.end && realEnd > span.start);
    });

    if (hasOverlap) {
        // --- MODIFICA UX: Avvisiamo l'utente con un popup invece di tacere ---
        openPopup("Attenzione: Non puoi sovrapporre le evidenziazioni. Cancella quella vecchia prima.");
        selection.removeAllRanges();
        return;
    }

    // 6. Crea e Invia
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
    return l ? l.color : '#ccc';
};

// Rendering a fette (Rimane uguale, funziona bene)
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
/* STILI IDENTICI A PRIMA */
.highlighter-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.toolbar {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    align-items: center;
}

.label-btn {
    padding: 6px 12px;
    border: 2px solid transparent;
    border-radius: 20px;
    cursor: pointer;
    font-weight: bold;
    font-size: 0.9rem;
    transition: all 0.2s;
}

.label-btn:hover {
    opacity: 0.8;
}

.text-area {
    font-size: 1.2rem;
    line-height: 1.8;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 8px;
    background: white;
    min-height: 150px;
    white-space: pre-wrap;
    cursor: text;
}

.highlight {
    padding: 2px 0;
    border-radius: 4px;
    position: relative;
    margin: 0 2px;
    cursor: pointer;
}

.remove-btn {
    position: absolute;
    top: -10px;
    right: -10px;
    width: 18px;
    height: 18px;
    background: #ff4444;
    color: white;
    border: 2px solid white;
    border-radius: 50%;
    font-size: 12px;
    display: none;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 10;
    padding: 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.highlight:hover .remove-btn {
    display: flex;
}

/* STILI POPUP */
.popup-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.popup-content {
    background: white;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    text-align: center;
    max-width: 400px;
    width: 90%;
    animation: fadeIn 0.2s ease-out;
}

.popup-message {
    margin-bottom: 20px;
    font-size: 1.1rem;
    color: #333;
}

.popup-close-btn {
    padding: 8px 24px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: bold;
    transition: background 0.2s;
}

.popup-close-btn:hover {
    background: #0056b3;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>
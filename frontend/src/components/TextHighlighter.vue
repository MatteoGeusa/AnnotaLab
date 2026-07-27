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
                <span class="chunk-span"
                      :class="{ 'has-highlights': chunk.spans.length > 0 }"
                      :ref="el => registerChunkRef(el, chunk)"
                      @mouseover.stop="chunk.spans.length > 0 && setHoveredPos(chunk.start)"
                      @mouseleave="chunk.spans.length > 0 && clearHoveredPos()">
                    <span class="chunk-text" :style="getChunkTextStyle(chunk)">{{ chunk.text }}</span>
                </span>
            </template>

            <!-- Chip overlay: positioned by JS using getClientRects()[0] of the first line -->
            <div class="chip-overlay" aria-hidden="true">
                <span v-for="chip in chipPositions" :key="chip.spanId"
                    v-show="hoveredCharPos !== null && chip.start <= hoveredCharPos && chip.end > hoveredCharPos"
                    class="span-label-hint"
                    :style="{ top: chip.y + 'px', left: chip.x + 'px', background: chip.color }"
                    @mouseover="setHoveredPos(chip.start)"
                    @mouseleave="clearHoveredPos()">
                    {{ chip.label }}
                    <button class="remove-chip-btn-mini" @click.stop="removeSpan(chip.spanId)">×</button>
                </span>
            </div>
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
import { ref, computed, watch, watchEffect, onMounted, onUnmounted, nextTick } from 'vue';

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

// Chip overlay positioning (JS-measured via getClientRects)
const chunkRefMap = {};       // chunk.start (char offset) -> DOM element
const chipPositions = ref([]); // [{ spanId, label, color, y }]

const registerChunkRef = (el, chunk) => {
    if (el) {
        chunkRefMap[chunk.start] = el;
    } else {
        delete chunkRefMap[chunk.start];
    }
};

const updateChipPositions = () => {
    if (!textRef.value) return;
    const containerRect = textRef.value.getBoundingClientRect();
    const positions = [];

    for (const chunk of renderChunks.value) {
        const chipsHere = chunk.spans.filter(s => chunk.isStartOfSpan[s.id]);
        if (!chipsHere.length) continue;

        const el = chunkRefMap[chunk.start];
        if (!el) continue;

        // getClientRects() returns one DOMRect per visual line box.
        // rects[0] is the FIRST line of the span — we anchor the chip there.
        const rects = Array.from(el.getClientRects());
        if (!rects.length) continue;

        const lineBottom = rects[0].bottom - containerRect.top;
        const lineLeft   = rects[0].left   - containerRect.left;

        chipsHere.forEach(span => {
            positions.push({
                spanId: span.id,
                label: span.label,
                color: getLabelColor(span.label),
                x: lineLeft,
                y: lineBottom + span.level * 22 + 2,
                start: span.start,  // needed for hover visibility check
                end: span.end,
            });
        });
    }

    chipPositions.value = positions;
};

// Popup State
const showPopup = ref(false);
const popupMessage = ref("");

// hoveredCharPos: character offset in text currently under the mouse.
// Used to show/hide chips and apply hover background tint.
// A 100ms clear-delay prevents flicker when moving from text to chip.
const hoveredCharPos = ref(null);
let clearHoverTimer = null;

const setHoveredPos = (charPos) => {
    if (clearHoverTimer) { clearTimeout(clearHoverTimer); clearHoverTimer = null; }
    hoveredCharPos.value = charPos;
};
const clearHoveredPos = () => {
    clearHoverTimer = setTimeout(() => { hoveredCharPos.value = null; }, 100);
};

const openPopup = (msg) => {
    popupMessage.value = msg;
    showPopup.value = true;
};

const closePopup = () => {
    showPopup.value = false;
};

// Keydown listener for labels 1-9
const handleKeydown = (e) => {
    // Ignore if user is typing in an input, textarea or contenteditable
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
        return;
    }

    const key = parseInt(e.key);
    if (!isNaN(key) && key > 0 && key <= props.labels.length) {
        selectedLabel.value = props.labels[key - 1].name;
    }
};

onMounted(() => {
    window.addEventListener('keydown', handleKeydown);
    window.addEventListener('resize', updateChipPositions);
    nextTick(updateChipPositions);
});

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown);
    window.removeEventListener('resize', updateChipPositions);
    if (clearHoverTimer) clearTimeout(clearHoverTimer);
    // Remove selection color override on unmount
    document.documentElement.style.removeProperty('--text-selection-color');
});

watch(() => props.labels, (newLabels) => {
    if (newLabels && newLabels.length > 0 && !selectedLabel.value) {
        selectedLabel.value = newLabels[0].name;
    }
}, { immediate: true });

// Re-measure chip positions after spans or text change (DOM must update first)
watch(() => props.spans, () => nextTick(updateChipPositions), { deep: true });
watch(() => props.text, () => nextTick(updateChipPositions));

// Sync the browser's text-selection highlight color with the active label.
// NOTE: getLabelColor is defined later, so we inline the lookup to avoid TDZ.
watchEffect(() => {
    const label = props.labels?.find(x => x.name === selectedLabel.value);
    const color = (label?.color || '#3b82f6').replace('#', '');
    const r = parseInt(color.slice(0, 2), 16);
    const g = parseInt(color.slice(2, 4), 16);
    const b = parseInt(color.slice(4, 6), 16);
    document.documentElement.style.setProperty(
        '--text-selection-color',
        `rgba(${r}, ${g}, ${b}, 0.45)`
    );
});


const getGlobalOffset = (root, targetNode, targetOffset) => {
    let offset = 0;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode: (node) => {
            if (node.parentNode && node.parentNode.classList.contains('chunk-text')) {
                return NodeFilter.FILTER_ACCEPT;
            }
            return NodeFilter.FILTER_REJECT;
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

    // Strict redundancy check (same label): prevent ANY overlap (fully contained, containing, or partial)
    const hasAnySameLabelOverlap = props.spans.some(span =>
        span.label === selectedLabel.value && (
            realStart < span.end && realEnd > span.start
        )
    );

    if (hasAnySameLabelOverlap) {
        selection.removeAllRanges();
        return;
    }

    // Overlap check removed to allow nested/overlapping spans
    /*
    const hasOverlap = props.spans.some(span => {
        return (realStart < span.end && realEnd > span.start);
    });

    if (hasOverlap) {
        openPopup("Warning: Overlapping highlights are not allowed. Please remove the existing one first.");
        selection.removeAllRanges();
        return;
    }
    */

    const newSpan = {
        start: realStart,
        end: realEnd,
        label: selectedLabel.value,
        text: textSegment,
        id: `span-${Date.now()}-${Math.floor(Math.random() * 1000)}`
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

const getChunkTextStyle = (chunk) => {
    // box-decoration-break: clone makes background gradients repeat on EVERY visual line
    // when the inline element wraps — this is the fix for the multi-line underline bug.
    const styles = {
        WebkitBoxDecorationBreak: 'clone',
        boxDecorationBreak: 'clone',
    };

    if (chunk.spans.length > 0) {
        const sortedByLevel = [...chunk.spans].sort((a, b) => a.level - b.level);

        // One 4px colored stripe per span level, stacked bottom-up.
        // Each stripe: 4px bar + 2px gap between levels.
        const stripes = sortedByLevel.map((s, i) => {
            const color = getLabelColor(s.label);
            const offset = i * 6; // px from bottom edge
            return `linear-gradient(${color}, ${color}) left calc(100% - ${offset}px) / 100% 4px no-repeat`;
        });

        // Hover tint = color of the most recently added span covering THIS chunk.
        // We find the span in chunk.spans that appears last in props.spans (insertion order).
        if (hoveredCharPos.value !== null
            && chunk.start <= hoveredCharPos.value
            && hoveredCharPos.value < chunk.end) {
            const lastLocalSpan = chunk.spans.reduce((latest, sp) => {
                const idx = props.spans.findIndex(s => s.id === sp.id);
                const latestIdx = latest ? props.spans.findIndex(s => s.id === latest.id) : -1;
                return idx > latestIdx ? sp : latest;
            }, null);
            const hoverColor = (lastLocalSpan ? getLabelColor(lastLocalSpan.label) : '#94a3b8') + '44';
            stripes.unshift(`linear-gradient(${hoverColor}, ${hoverColor}) 0 0 / 100% 100% no-repeat`);
            styles.borderRadius = '2px';
        }

        styles.background = stripes.join(', ');
        // Enough bottom padding to show all stacked stripes without clipping
        styles.paddingBottom = `${(sortedByLevel.length * 6) + 2}px`;
    }

    return styles;
};

const spansWithLevels = computed(() => {
    // Sort spans by start position, then by end position (longer spans first)
    const sortedSpans = [...props.spans].sort((a, b) => a.start - b.start || (b.end - a.end));
    const levels = []; // stores the right-most end position of each level

    return sortedSpans.map(span => {
        let assignedLevel = -1;
        for (let i = 0; i < levels.length; i++) {
            // Check if this span fits in level i (current start >= last end in that level)
            if (span.start >= levels[i]) {
                assignedLevel = i;
                levels[i] = span.end;
                break;
            }
        }
        if (assignedLevel === -1) {
            assignedLevel = levels.length;
            levels.push(span.end);
        }
        return { ...span, level: assignedLevel };
    });
});

const maxLevels = computed(() => {
    if (props.spans.length === 0) return 0;
    const levels = [];
    spansWithLevels.value.forEach(s => {
        if (!levels.includes(s.level)) levels.push(s.level);
    });
    return Math.max(0, ...levels) + 1;
});

const renderChunks = computed(() => {
    if (!props.text) return [];

    // 1. Collect all boundaries
    const boundaries = new Set([0, props.text.length]);
    spansWithLevels.value.forEach(s => {
        boundaries.add(s.start);
        boundaries.add(s.end);
    });

    // 2. Sort boundaries to create atomic segments
    const sortedBoundaries = Array.from(boundaries).sort((a, b) => a - b);
    const chunks = [];

    for (let i = 0; i < sortedBoundaries.length - 1; i++) {
        const start = sortedBoundaries[i];
        const end = sortedBoundaries[i + 1];
        const text = props.text.slice(start, end);

        if (text === "") continue;

        // 3. Find which spans cover this atomic chunk
        const coveringSpans = spansWithLevels.value.filter(s => s.start <= start && s.end >= end);

        // Track if this chunk is the start of any span (to render the label/button)
        const isStartOfSpan = {};
        const spansByLevel = {};

        coveringSpans.forEach(s => {
            isStartOfSpan[s.id] = (s.start === start);
            if (!spansByLevel[s.level]) spansByLevel[s.level] = [];
            spansByLevel[s.level].push(s);
        });

        chunks.push({
            text,
            start,
            end,
            spans: coveringSpans,
            spansByLevel,
            isStartOfSpan
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
    position: relative; /* needed for the chip-overlay absolute positioning */
    font-size: 1.3rem;
    line-height: 3.0;
    /* Balanced line height for labels and readability */
    padding: 35px;
    min-height: 250px;
    white-space: pre-wrap;
    cursor: text;
    background-color: #fdfdfd;
    color: #1e293b;
    /* Darker, higher contrast text */
}

/* Selection highlight color = active label color (set via --text-selection-color CSS var) */
.text-card-area ::selection {
    background-color: var(--text-selection-color, rgba(59, 130, 246, 0.4));
    color: inherit;
}

.normal-text {
    color: inherit;
}

/* ATOMIC CHUNK STYLES */
.chunk-span {
    position: relative;
    display: inline;
}

.chunk-text {
    position: relative;
    z-index: 5;
}

/* Chip overlay: renders chips absolutely positioned inside text-card-area */
.chip-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 20;
}

.span-label-hint {
    /* top and left are both set inline by JS (getClientRects) */
    position: absolute;
    font-size: 0.65rem;
    font-weight: 700;
    color: white;
    padding: 0 6px;
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
    height: 18px;
    line-height: 18px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
    letter-spacing: 0.4px;
    pointer-events: auto;
    cursor: default;
    font-family: '__robotoCondensed_9f41a4', '__robotoCondensed_Fallback_9f41a4', 'Arial Narrow', 'Arial', sans-serif;
}

.remove-chip-btn-mini {
    background: rgba(0, 0, 0, 0.25);
    border: none;
    color: white;
    border-radius: 50%;
    width: 12px;
    height: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 9px;
    padding: 0;
    transition: background 0.2s;
}

.remove-chip-btn-mini:hover {
    background: rgba(0, 0, 0, 0.5);
}

.chunk-span.has-highlights {
    border-radius: 2px;
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

<style scoped>
@import '../assets/shared.css';
</style>
import { computed } from 'vue';

/**
 * Composable che converte un testo Markdown in HTML.
 * @param {import('vue').Ref<string>} rawText - ref contenente il testo Markdown grezzo
 * @returns {{ rendered: import('vue').ComputedRef<string> }}
 */
export function useMarkdownRenderer(rawText) {
    const rendered = computed(() => {
        let text = rawText.value;
        if (!text) return '';

        // Escape HTML entities
        text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

        // Headers
        text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>');

        // Bold and italic
        text = text.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
        text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/(?<!\w)_(.+?)_(?!\w)/g, '<em>$1</em>');
        text = text.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

        // Inline code
        text = text.replace(/`(.+?)`/g, '<code>$1</code>');

        // Unordered lists
        text = text.replace(/^- (.+)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

        // Ordered lists
        text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

        // Horizontal rules
        text = text.replace(/^---$/gm, '<hr>');

        // Paragraphs (lines not already wrapped in tags)
        text = text.replace(/^(?!<[hulo]|<li|<hr)(.+)$/gm, '<p>$1</p>');

        // Clean up empty paragraphs
        text = text.replace(/<p>\s*<\/p>/g, '');

        return text;
    });

    return { rendered };
}

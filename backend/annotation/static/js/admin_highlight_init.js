/**
 * admin_highlight_init.js
 * Initializes Highlight.js for JSON syntax highlighting in the Django admin.
 * Loaded via the AnnotatorAdmin.Media class.
 */
document.addEventListener('DOMContentLoaded', function () {
    if (typeof hljs !== 'undefined') {
        // Highlight all <code> blocks that have a language class (e.g. class="json")
        document.querySelectorAll('pre code[class]').forEach(function (block) {
            hljs.highlightElement(block);
        });
    }
});

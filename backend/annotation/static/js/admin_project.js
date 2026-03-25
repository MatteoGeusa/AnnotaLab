/**
 * admin_project.js
 * Optimized field visibility and drag-and-drop for Project Admin
 */
document.addEventListener("DOMContentLoaded", function () {

    function forceVisibility(fieldName, shouldShow) {
        const field = document.getElementById(`id_${fieldName}`) || 
                      document.querySelector(`input[name="${fieldName}"]`) || 
                      document.querySelector(`select[name="${fieldName}"]`);
        
        const container = document.querySelector(`.field-${fieldName}`) || 
                          (field ? field.closest('.fieldBox') : null) ||
                          (field ? field.closest('.flex-col, .form-row') : null);

        if (!container) return;
        container.style.display = shouldShow ? '' : 'none';
        
        const row = container.parentElement;
        if (row && (row.classList.contains('form-row') || row.classList.contains('flex') || row.classList.contains('grid'))) {
            const hasVisibleContent = Array.from(row.children).some(child => {
                 return child.style.display !== 'none' && 
                        (child.classList.contains('fieldBox') || child.className.includes('field-'));
            });
            row.style.display = hasVisibleContent ? '' : 'none';
        }
    }

    function sync() {
        // A. Distribution Strategy
        const distVal = (document.getElementById('id_distribution_strategy') || {}).value;
        if (distVal) {
            forceVisibility('min_annotations_per_doc', distVal !== 'FULL_OVERLAP');
            forceVisibility('max_annotations_per_doc', distVal !== 'FULL_OVERLAP');
            forceVisibility('prioritize_unannotated', distVal !== 'FULL_OVERLAP');
            forceVisibility('block_size', distVal === 'SAME_ANNOTATORS');
            forceVisibility('annotators_per_block', distVal === 'SAME_ANNOTATORS');
        }
    }

    ['id_distribution_strategy'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', sync);
    });

    // Capture potential late renders (Unfold characteristics)
    sync();
    [50, 200, 500, 1000].forEach(delay => setTimeout(sync, delay));

    // Drag and Drop (Compact)
    document.querySelectorAll('input[type="file"]').forEach(input => {
        if (input.name.includes('upload_')) {
            const p = input.closest('.flex-col, div');
            if (p && !p.querySelector('.dd-zone')) {
                const zone = document.createElement('div');
                zone.className = "dd-zone";
                zone.style.padding = "10px"; zone.style.border = "2px dashed #444"; zone.style.cursor = "pointer";
                zone.style.textAlign = "center"; zone.style.borderRadius = "6px"; zone.style.marginBottom = "5px";
                zone.innerHTML = "📂 Upload File";
                input.style.display = 'none';
                p.prepend(zone);
                zone.onclick = () => input.click();
                input.onchange = () => zone.innerHTML = `✅ ${input.files[0].name}`;
            }
        }
    });
});

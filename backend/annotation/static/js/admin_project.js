/**
 * admin_project.js
 * Enhances the file upload fields with drag-and-drop zones
 * and displays the selected filename after choosing a file.
 * Also handles FULL_OVERLAP strategy field disabling.
 */
document.addEventListener("DOMContentLoaded", function () {
  // ============================================
  // 1. FILE UPLOAD DRAG & DROP
  // ============================================
  const fileInputs = document.querySelectorAll(
    'input[type="file"][name="upload_task_config"], input[type="file"][name="upload_gold_config"], input[type="file"][name="upload_screening_config"], input[type="file"][name="upload_codebook_content"]',
  );

  fileInputs.forEach(function (input) {
    const fieldWrapper = input.closest(
      ".flex-col, .field-upload_task_config, .field-upload_gold_config, .field-upload_screening_config, div",
    );
    if (!fieldWrapper) return;

    // Check if already wrapped (avoid double-wrapping)
    if (fieldWrapper.querySelector(".file-upload-wrapper")) return;

    const label =
      input.name === "upload_task_config"
        ? "Task Configuration"
        : input.name === "upload_gold_config"
          ? "Gold Units Configuration"
          : input.name === "upload_screening_config"
            ? "Screening Configuration"
            : "Codebook Materials";

    const icon =
      input.name === "upload_task_config"
        ? "⚙️"
        : input.name === "upload_gold_config"
          ? "🛡️"
          : input.name === "upload_screening_config"
            ? "📋"
            : "📖";

    // Create the styled wrapper
    const wrapper = document.createElement("div");
    wrapper.className = "file-upload-wrapper";

    const zone = document.createElement("div");
    zone.className = "upload-zone";
    zone.innerHTML = `
            <div class="upload-icon">${icon}</div>
            <span class="upload-label">Drop a JSON file here or click to browse</span>
            <span class="upload-hint">Overwrites the current <code>${label}</code></span>
        `;

    const selectedInfo = document.createElement("div");
    selectedInfo.className = "file-selected";
    selectedInfo.innerHTML = '<span>📎</span><span class="filename"></span>';

    wrapper.appendChild(zone);
    wrapper.appendChild(selectedInfo);

    // Move the original input inside the wrapper
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    // Drag & Drop visual feedback
    zone.addEventListener("dragover", function (e) {
      e.preventDefault();
      zone.classList.add("dragover");
    });

    zone.addEventListener("dragleave", function () {
      zone.classList.remove("dragover");
    });

    zone.addEventListener("drop", function () {
      zone.classList.remove("dragover");
    });

    // Show selected filename
    input.addEventListener("change", function () {
      if (input.files && input.files.length > 0) {
        selectedInfo.querySelector(".filename").textContent =
          input.files[0].name;
        selectedInfo.classList.add("visible");
        zone.querySelector(".upload-label").textContent =
          "File selected — click Save to apply";
      } else {
        selectedInfo.classList.remove("visible");
        zone.querySelector(".upload-label").textContent =
          "Drop a JSON file here or click to browse";
      }
    });
  });

  // ============================================
  // 2. FULL_OVERLAP STRATEGY: DISABLE MIN/MAX
  // ============================================
  const strategySelect = document.querySelector('#id_distribution_strategy');
  const minField = document.querySelector('#id_min_annotations_per_doc');
  const maxField = document.querySelector('#id_max_annotations_per_doc');
  const blockSizeInput = document.querySelector('#id_block_size');

  if (strategySelect) {
    // Create warning banner for FULL_OVERLAP
    const banner = document.createElement('div');
    banner.className = 'full-overlap-warning';
    banner.innerHTML = '⚠️ <strong>FULL_OVERLAP mode:</strong> Min and Max annotation limits are ignored. Every annotator will see every document.';
    banner.style.display = 'none'; // hidden by default

    // Insert banner before the Distribution Strategy fieldset
    const strategyFieldWrapper = strategySelect.closest('.form-row, .flex-col, fieldset');
    if (strategyFieldWrapper) {
      strategyFieldWrapper.parentNode.insertBefore(banner, strategyFieldWrapper);
    }

    function toggleFields() {
      const isFullOverlap = strategySelect.value === 'FULL_OVERLAP';
      const isSameAnnotators = strategySelect.value === 'SAME_ANNOTATORS';

      // Helper to hide/show a pair of fields and their container row
      function toggleFieldPair(f1, f2, shouldShow) {
          if (!f1) return;
          
          const cont1 = f1.closest('.fieldBox') || f1.closest(`[class*="field-${f1.name}"]`) || f1.parentElement;
          const cont2 = f2 ? (f2.closest('.fieldBox') || f2.closest(`[class*="field-${f2.name}"]`) || f2.parentElement) : null;
          
          if (cont1) cont1.style.display = shouldShow ? '' : 'none';
          if (cont2) cont2.style.display = shouldShow ? '' : 'none';
          
          // If they share a wrapper, hide the wrapper too (e.g. Django Unfold grouped fields)
          if (cont1 && cont2 && cont1.parentElement === cont2.parentElement) {
              cont1.parentElement.style.display = shouldShow ? '' : 'none';
          } else if (cont1) {
               const formRow = cont1.closest('.form-row');
               if (formRow) formRow.style.display = shouldShow ? '' : 'none';
          }
      }

      // 1. FULL_OVERLAP logic (Hide min/max AND prioritize)
      // They should be visible ONLY if we are NOT in FULL_OVERLAP
      const prioritizeField = document.querySelector('#id_prioritize_unannotated');
      
      toggleFieldPair(minField, maxField, !isFullOverlap);
      toggleFieldPair(prioritizeField, null, !isFullOverlap);
      if (banner) {
          banner.style.display = isFullOverlap ? 'block' : 'none';
      }

      // 2. SAME_ANNOTATORS logic (Hide block settings)
      // They should be visible ONLY if we ARE in SAME_ANNOTATORS
      const annotatorsField = document.querySelector('#id_annotators_per_block');
      toggleFieldPair(blockSizeInput, annotatorsField, isSameAnnotators);
    }

    // Run on load + on change
    toggleFields();
    strategySelect.addEventListener('change', toggleFields);
  }
});


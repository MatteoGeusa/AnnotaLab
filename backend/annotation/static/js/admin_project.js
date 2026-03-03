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
    'input[type="file"][name="upload_task_config"], input[type="file"][name="upload_gold_config"], input[type="file"][name="upload_screening_config"]',
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
          : "Screening Configuration";

    const icon =
      input.name === "upload_task_config"
        ? "⚙️"
        : input.name === "upload_gold_config"
          ? "🛡️"
          : "📋";

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

  if (strategySelect && minField && maxField) {
    // Create warning banner
    const banner = document.createElement('div');
    banner.className = 'full-overlap-warning';
    banner.innerHTML = '⚠️ <strong>FULL_OVERLAP mode:</strong> Min and Max annotation limits are ignored. Every annotator will see every document.';
    
    // Insert banner before the Distribution Strategy fieldset
    const strategyFieldWrapper = strategySelect.closest('.form-row, .flex-col, fieldset');
    if (strategyFieldWrapper) {
      strategyFieldWrapper.parentNode.insertBefore(banner, strategyFieldWrapper);
    }

    function toggleFields() {
      const isFullOverlap = strategySelect.value === 'FULL_OVERLAP';
      
      // We use readOnly and pointer-events instead of disabled
      // because disabled fields are NOT sent in the POST request,
      // which causes validation errors in Django for mandatory fields.
      minField.readOnly = isFullOverlap;
      maxField.readOnly = isFullOverlap;
      
      if (isFullOverlap) {
        minField.style.opacity = '0.5';
        maxField.style.opacity = '0.5';
        minField.style.pointerEvents = 'none';
        maxField.style.pointerEvents = 'none';
        banner.style.display = 'block';
      } else {
        minField.style.opacity = '1';
        maxField.style.opacity = '1';
        minField.style.pointerEvents = 'auto';
        maxField.style.pointerEvents = 'auto';
        banner.style.display = 'none';
      }
    }

    // Run on load + on change
    toggleFields();
    strategySelect.addEventListener('change', toggleFields);
  }
});


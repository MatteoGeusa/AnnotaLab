/**
 * admin_project.js
 * Enhances the file upload fields with drag-and-drop zones
 * and displays the selected filename after choosing a file.
 */
document.addEventListener("DOMContentLoaded", function () {
  // Target all raw file inputs that correspond to our upload fields
  const fileInputs = document.querySelectorAll(
    'input[type="file"][name="upload_task_config"], input[type="file"][name="upload_screening_config"]',
  );

  fileInputs.forEach(function (input) {
    const fieldWrapper = input.closest(
      ".flex-col, .field-upload_task_config, .field-upload_screening_config, div",
    );
    if (!fieldWrapper) return;

    // Check if already wrapped (avoid double-wrapping)
    if (fieldWrapper.querySelector(".file-upload-wrapper")) return;

    const label =
      input.name === "upload_task_config"
        ? "Task Configuration"
        : "Screening Configuration";

    const icon = input.name === "upload_task_config" ? "⚙️" : "🛡️";

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
});

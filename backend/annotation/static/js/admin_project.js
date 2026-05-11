/**
 * admin_project.js
 * Optimized field visibility and drag-and-drop for Project Admin
 */

(function() {
    const style = document.createElement('style');
    style.innerHTML = `
        #admin-popup-container {
            position: fixed;
            top: 2rem;
            right: 2rem;
            z-index: 999999;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            pointer-events: none;
        }

        .admin-popup {
            pointer-events: auto;
            background: #1e293b;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            min-width: 320px;
            max-width: 450px;
            animation: popupSlideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes popupSlideIn {
            from { transform: translateX(100%) scale(0.9); opacity: 0; }
            to { transform: translateX(0) scale(1); opacity: 1; }
        }

        .admin-popup.closing {
            animation: popupSlideOut 0.3s forwards;
        }

        @keyframes popupSlideOut {
            to { transform: translateX(100%); opacity: 0; }
        }

        .admin-popup-title {
            font-weight: 800;
            font-size: 0.875rem;
            margin-bottom: 0.25rem;
        }

        .admin-popup-message {
            font-size: 0.8125rem;
            opacity: 0.8;
            line-height: 1.5;
        }

        .admin-popup-close {
            cursor: pointer;
            opacity: 0.5;
            margin-left: auto;
        }

        .admin-popup-close:hover { opacity: 1; }

        .admin-popup.success { border-left: 4px solid #10b981; }
        .admin-popup.error { border-left: 4px solid #ef4444; }
        .admin-popup.warning { border-left: 4px solid #f59e0b; }
        .admin-popup.info { border-left: 4px solid #3b82f6; }
    `;
    document.head.appendChild(style);
})();

/**
 * Open project preview with dynamic participant ID from input
 */
window.openProjectPreview = function (baseUrl, slug, inputId, isPublished = false, status = '', updateStatusUrl = '') {
    if (status !== 'LIVE') {
        let title = "Playground Mode Required";
        let msg = "You cannot perform test annotations while the project is in **Draft**.<br><br>Would you like to switch to **Playground** mode now to enable testing?";
        let btn = "Switch to Playground";
        let emoji = "📁";

        if (status === 'PAUSED') {
            title = "⏸️ Collection Paused";
            msg = "This project is currently **Paused**. To perform test annotations and verify the configuration, you must return to **Live** mode.<br><br>Would you like to resume now?";
            btn = "Resume to Live";
            emoji = "⏸️";
        } else if (status === 'COMPLETED') {
            title = "🏁 Project Completed";
            msg = "This project is marked as **Completed**. To perform additional test annotations, you must return it to **Live** mode.<br><br>Would you like to resume now?";
            btn = "Resume to Live";
            emoji = "🏁";
        }

        window.adminConfirm(
            `🚀 ${title}`,
            msg,
            emoji,
            btn,
            "#10b981",
            () => {
                if (window.executeUpdateStatus) {
                    window.executeUpdateStatus(null, updateStatusUrl, 'LIVE');
                } else {
                    console.error("executeUpdateStatus not found");
                }
            }
        );
        return;
    }

    const input = document.getElementById(inputId);
    const pid = (input && input.value.trim()) ? input.value.trim() : 'ADMIN_TEST';
    const url = `${baseUrl}/${slug}?PROLIFIC_PID=${encodeURIComponent(pid)}&is_test=true`;

    window.open(url, '_blank');
};

/**
 * Copy JSON configuration from hidden element to clipboard
 */
window.copyConfigToClipboard = function (button) {
    const container = button.closest('.json-config-display');
    const rawContent = container.querySelector('.json-raw-content').innerHTML;

    // Create a textarea to handle HTML entities naturally if needed, 
    // but here we just need the text
    const tempElement = document.createElement('textarea');
    tempElement.innerHTML = rawContent;
    const textToCopy = tempElement.value;

    navigator.clipboard.writeText(textToCopy).then(() => {
        const originalText = button.innerHTML;
        button.innerHTML = '✅ Copied!';
        button.style.background = 'rgba(16, 185, 129, 0.2)';
        button.style.color = '#10b981';

        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = 'rgba(48, 110, 232, 0.1)';
            button.style.color = '#306ee8';
        }, 2000);

        if (window.adminNotify) {
            window.adminNotify('success', 'Copied', 'JSON configuration copied to clipboard.');
        }
    });
};

/**
 * Copy Markdown content from hidden element to clipboard
 */
window.copyMarkdownToClipboard = function (button) {
    const container = button.closest('.json-config-display');
    const rawContent = container.querySelector('.markdown-raw-content').innerHTML;

    const tempElement = document.createElement('textarea');
    tempElement.innerHTML = rawContent;
    const textToCopy = tempElement.value;

    navigator.clipboard.writeText(textToCopy).then(() => {
        const originalText = button.innerHTML;
        button.innerHTML = '✅ Copied!';
        button.style.background = 'rgba(16, 185, 129, 0.2)';
        button.style.color = '#10b981';

        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = 'rgba(48, 110, 232, 0.1)';
            button.style.color = '#306ee8';
        }, 2000);

        if (window.adminNotify) {
            window.adminNotify('success', 'Copied', 'Markdown content copied to clipboard.');
        }
    });
};
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

    // --- MACE Button Injection for Changelist ---
    const injectMaceButton = () => {
        let maceUrl = window.MACE_RUN_URL;

        // Fallback: Try to parse project ID from current URL if not provided by template
        if (!maceUrl) {
            const params = new URLSearchParams(window.location.search);
            const pid = params.get('project__id') || 
                        params.get('project__id__exact') || 
                        params.get('document__project__id') || 
                        params.get('document__project__id__exact');
            
            if (pid && !isNaN(pid)) {
                maceUrl = `/admin/annotation/project/${pid}/run-mace/`;
                console.log("MACE: Fallback URL generated:", maceUrl);
            }
        }

        if (!maceUrl || document.getElementById('mace-injected-btn')) return;

        // Try to find the filters button using various strategies
        let filtersBtn = document.querySelector('a[x-on\\:click*="filterOpen"]') ||
                         document.querySelector('.unfold-filters-button') || 
                         document.querySelector('[data-unfold-filters]') ||
                         document.querySelector('.unfold-filter-container button');
        
        // Final fallback: Find by text content
        if (!filtersBtn) {
            filtersBtn = Array.from(document.querySelectorAll('a, button'))
                .find(el => el.textContent.trim().includes('Filters') && el.offsetParent !== null);
        }
        
        if (filtersBtn) {
            const btn = document.createElement('button');
            btn.id = 'mace-injected-btn';
            btn.type = 'button';
            btn.innerHTML = '<span style="margin-right: 6px;">🤖</span> Run MACE Analysis';
            
            // Match Unfold's primary button style (Emerald/Blue)
            btn.className = 'bg-primary-600 border-none flex font-bold items-center justify-center leading-none px-4 py-2 rounded-md text-white text-xs whitespace-nowrap cursor-pointer hover:bg-primary-700 transition-colors shadow-sm';
            btn.style.height = '38px'; 
            btn.style.marginLeft = '12px'; 
            
            // Insert BEFORE the filters button
            filtersBtn.parentNode.insertBefore(btn, filtersBtn);
            btn.onclick = () => window.quickRunMace(btn, maceUrl);
        } else {
            // If still not found, try to append to toolbar as last resort
            const toolbar = document.querySelector('#toolbar') || document.querySelector('.changelist-form-container');
            if (toolbar && !document.getElementById('mace-injected-btn')) {
                const btn = document.createElement('button');
                btn.id = 'mace-injected-btn';
                btn.type = 'button';
                btn.innerHTML = '🤖 Run MACE';
                btn.className = 'bg-primary-600 border-none px-4 py-2 rounded-md text-white text-xs font-bold ml-auto cursor-pointer';
                toolbar.appendChild(btn);
                btn.onclick = () => window.quickRunMace(btn, maceUrl);
            }
        }
    };

    injectMaceButton();
    setTimeout(injectMaceButton, 500);
    setTimeout(injectMaceButton, 1500);

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

// CSRF Token Helper
window.getAdminCookie = function (name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

/**
 * Internal helper to parse basic markdown (**bold**) and newlines
 */
window._parseAdminMarkdown = function(text) {
    if (!text) return "";
    return text
        .replace(/\*\*(.*?)\*\*/g, '<b style="color: white; font-weight: 800;">$1</b>')
        .replace(/\n/g, '<br>');
};

/**
 * Modern Notification System for Admin
 */
window.adminNotify = function (type, title, message, duration = 5000) {
    let container = document.getElementById('admin-popup-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'admin-popup-container';
        document.body.appendChild(container);
    }

    const popup = document.createElement('div');
    popup.className = `admin-popup ${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    popup.innerHTML = `
        <div class="admin-popup-icon">${icons[type] || '🔔'}</div>
        <div class="admin-popup-content">
            <div class="admin-popup-title">${title}</div>
            <div class="admin-popup-message">${window._parseAdminMarkdown(message)}</div>
        </div>
        <div class="admin-popup-close" onclick="this.parentElement.closePopup()">✕</div>
    `;

    popup.closePopup = () => {
        popup.classList.add('closing');
        setTimeout(() => popup.remove(), 400);
    };

    container.prepend(popup);

    if (duration > 0) {
        setTimeout(popup.closePopup, duration);
    }
    return popup;
};

/**
 * Handles quick status update from the project list view via AJAX
 */
window.quickUpdateStatus = function (buttonElement, url, newStatus, statusLabel) {
    window.adminConfirm(
        "UPDATE PROJECT STATUS",
        `Do you want to change the status to **${statusLabel}**?`,
        "⚙️",
        `Yes, set to ${statusLabel}`,
        "#3b82f6",
        () => window.executeUpdateStatus(buttonElement, url, newStatus)
    );
};

window.executeUpdateStatus = function (buttonElement, url, newStatus) {
    const container = buttonElement ? buttonElement.closest('.status-badge-container') : null;

    if (buttonElement) buttonElement.disabled = true;
    if (container) container.style.opacity = '0.5';

    const csrftoken = window.getAdminCookie('csrftoken');

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ status: newStatus }),
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(
                    err => { throw err; },
                    () => { throw new Error(`Server returned ${response.status}`); }
                );
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                window.adminNotify('success', 'Status Updated', 'The project status has been changed successfully.', 2000);
                setTimeout(() => window.location.reload(), 800);
            } else {
                window.adminNotify('error', 'Status Change Failed', data.message || 'Unknown error');
                if (buttonElement) buttonElement.disabled = false;
                if (container) container.style.opacity = '1';
            }
        })
        .catch(error => {
            console.error('Update failed:', error);
            const msg = error.message || (typeof error === 'string' ? error : 'The request to update status failed.');
            window.adminNotify('error', 'Error', msg);
            if (buttonElement) buttonElement.disabled = false;
            if (container) container.style.opacity = '1';
        });
}

/**
 * Bridge standard Django messages to the modern popup system
 */
document.addEventListener("DOMContentLoaded", function () {
    // Check for standard Django message list elements
    const djangoMessages = document.querySelectorAll('.messagelist > li');
    djangoMessages.forEach(msg => {
        let type = 'info';
        if (msg.classList.contains('success')) type = 'success';
        if (msg.classList.contains('error')) type = 'error';
        if (msg.classList.contains('warning')) type = 'warning';

        window.adminNotify(type, 'System Message', msg.innerText, 5000 + (djangoMessages.length * 500));

        // Hide the original banner to avoid double messaging
        msg.parentElement.style.display = 'none';
    });
});

/**
 * Custom Modal Dialog popup for critical actions
 */
window.adminConfirm = function (title, message, emojis, confirmText, confirmColor, onConfirm) {
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.backgroundColor = 'rgba(15, 23, 42, 0.7)';
    overlay.style.zIndex = '999999';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.backdropFilter = 'blur(4px)';

    const modal = document.createElement('div');
    modal.style.background = '#1e293b';
    modal.style.color = '#f8fafc';
    modal.style.padding = '32px 24px';
    modal.style.borderRadius = '16px';
    modal.style.width = '90%';
    modal.style.maxWidth = '420px';
    modal.style.boxShadow = '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255,255,255,0.1)';
    modal.style.fontFamily = 'system-ui, -apple-system, sans-serif';
    modal.style.textAlign = 'center';

    modal.innerHTML = `
        <div style="font-size: 48px; margin-bottom: 16px; line-height: 1;">${emojis}</div>
        <h2 style="margin: 0 0 12px 0; font-size: 20px; font-weight: 800; letter-spacing: -0.02em;">${title}</h2>
        <p style="margin: 0 0 28px 0; font-size: 14px; color: #94a3b8; line-height: 1.6;">${window._parseAdminMarkdown(message)}</p>
        <div style="display: flex; gap: 12px; justify-content: center;">
            <button id="modal-cancel-btn" style="flex: 1; padding: 12px 16px; border-radius: 8px; border: 1px solid #334155; background: transparent; color: #cbd5e1; cursor: pointer; font-weight: 600; font-size: 14px; transition: all 0.2s;">Cancel</button>
            <button id="modal-confirm-btn" style="flex: 2; padding: 12px 16px; border-radius: 8px; border: none; background: ${confirmColor}; color: white; cursor: pointer; font-weight: 700; font-size: 14px; transition: all 0.2s; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);">${confirmText}</button>
        </div>
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    modal.animate([
        { transform: 'scale(0.9)', opacity: 0 },
        { transform: 'scale(1)', opacity: 1 }
    ], { duration: 200, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' });

    const close = () => {
        const anim = overlay.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 150, easing: 'ease-in' });
        anim.onfinish = () => overlay.remove();
    };

    document.getElementById('modal-cancel-btn').onclick = close;
    document.getElementById('modal-cancel-btn').onmouseover = function () { this.style.backgroundColor = '#334155'; };
    document.getElementById('modal-cancel-btn').onmouseout = function () { this.style.backgroundColor = 'transparent'; };

    document.getElementById('modal-confirm-btn').onclick = () => {
        close();
        onConfirm();
    };
};

/**
 * Custom Modal Alert (Informational only, based on adminConfirm style)
 */
window.adminAlert = function (title, message, emojis, btnText = "Understood", btnColor = "#3b82f6") {
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed'; overlay.style.top = '0'; overlay.style.left = '0';
    overlay.style.width = '100vw'; overlay.style.height = '100vh';
    overlay.style.backgroundColor = 'rgba(15, 23, 42, 0.7)'; overlay.style.zIndex = '999999';
    overlay.style.display = 'flex'; overlay.style.alignItems = 'center'; overlay.style.justifyContent = 'center';
    overlay.style.backdropFilter = 'blur(4px)';

    const modal = document.createElement('div');
    modal.style.background = '#1e293b'; modal.style.color = '#f8fafc';
    modal.style.padding = '32px 24px'; modal.style.borderRadius = '16px';
    modal.style.width = '90%'; modal.style.maxWidth = '420px';
    modal.style.boxShadow = '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255,255,255,0.1)';
    modal.style.fontFamily = 'system-ui, -apple-system, sans-serif'; modal.style.textAlign = 'center';

    modal.innerHTML = `
        <div style="font-size: 48px; margin-bottom: 16px; line-height: 1;">${emojis}</div>
        <h2 style="margin: 0 0 12px 0; font-size: 20px; font-weight: 800; letter-spacing: -0.02em;">${title}</h2>
        <p style="margin: 0 0 28px 0; font-size: 14px; color: #94a3b8; line-height: 1.6;">${window._parseAdminMarkdown(message)}</p>
        <div style="display: flex; justify-content: center;">
            <button id="modal-close-btn" style="width: 100%; padding: 12px 16px; border-radius: 8px; border: none; background: ${btnColor}; color: white; cursor: pointer; font-weight: 700; font-size: 14px; transition: all 0.2s; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);">${btnText}</button>
        </div>
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    modal.animate([
        { transform: 'scale(0.9)', opacity: 0 },
        { transform: 'scale(1)', opacity: 1 }
    ], { duration: 200, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' });

    const close = () => {
        overlay.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 150 }).onfinish = () => overlay.remove();
    };

    document.getElementById('modal-close-btn').onclick = close;
};

/**
 * Specific modal for Project Cloning choice
 */
window.adminCloneChoice = function (projectName, url, onClone, isPublished = false) {
    const message = `How would you like to clone **${projectName}**?`;
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed'; overlay.style.top = '0'; overlay.style.left = '0';
    overlay.style.width = '100vw'; overlay.style.height = '100vh';
    overlay.style.backgroundColor = 'rgba(15, 23, 42, 0.7)'; overlay.style.zIndex = '999999';
    overlay.style.display = 'flex'; overlay.style.alignItems = 'center'; overlay.style.justifyContent = 'center';
    overlay.style.backdropFilter = 'blur(4px)';

    const modal = document.createElement('div');
    modal.style.background = '#1e293b'; modal.style.color = '#f8fafc';
    modal.style.padding = '32px 24px'; modal.style.borderRadius = '16px';
    modal.style.width = '90%'; modal.style.maxWidth = '460px';
    modal.style.boxShadow = '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255,255,255,0.1)';
    modal.style.fontFamily = 'system-ui, -apple-system, sans-serif'; modal.style.textAlign = 'center';

    let publishedWarning = '';
    if (isPublished) {
        publishedWarning = `
            <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); color: #f59e0b; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; text-align: left; line-height: 1.5; display: flex; gap: 10px; align-items: start;">
                 <span style="font-size: 18px;">⚠️</span>
                 <span>This project is <b>Launched/Live</b>. To make structural changes or upload new data, you must <b>clone</b> it into a new project (Draft).</span>
            </div>
        `;
    }

    modal.innerHTML = `
        <div style="font-size: 48px; margin-bottom: 16px; line-height: 1;">📋</div>
        <h2 style="margin: 0 0 12px 0; font-size: 20px; font-weight: 800;">Clone Project</h2>
        <p style="margin: 0 0 20px 0; font-size: 14px; color: #94a3b8; line-height: 1.6;">${window._parseAdminMarkdown(message)}</p>
        
        ${publishedWarning}

        <div style="margin-bottom: 24px; text-align: left;">
            <label style="display: block; font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 6px; margin-left: 2px;">New Project Name</label>
            <input type="text" id="modal-clone-name" value="${projectName} (Clone)" 
                   style="width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; font-size: 14px; outline: none; box-sizing: border-box;">
        </div>

        <div style="display: flex; flex-direction: column; gap: 10px;">
            <button id="modal-clone-incomplete" style="padding: 14px; border-radius: 8px; border: 1px solid #6366f1; background: #4f46e5; color: white; cursor: pointer; font-weight: 700; font-size: 14px; transition: opacity 0.2s;">Clone Config + Docs + Workers</button>
            <button id="modal-clone-config" style="padding: 12px; border-radius: 8px; border: 1px solid #475569; background: #334155; color: white; cursor: pointer; font-weight: 600; font-size: 14px; transition: opacity 0.2s;">Clone Only Config</button>
            <button id="modal-clone-cancel" style="padding: 10px; background: transparent; border: none; color: #94a3b8; cursor: pointer; font-size: 13px; margin-top: 5px;">Cancel</button>
        </div>
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    // Auto-focus the input
    setTimeout(() => {
        const input = document.getElementById('modal-clone-name');
        if (input) {
            input.focus();
            input.select();
        }
    }, 100);

    const close = () => {
        overlay.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 150 }).onfinish = () => overlay.remove();
    };

    const getName = () => document.getElementById('modal-clone-name').value || `${projectName} (Clone)`;

    document.getElementById('modal-clone-incomplete').onclick = () => { const n = getName(); close(); onClone('incomplete', n); };
    document.getElementById('modal-clone-config').onclick = () => { const n = getName(); close(); onClone('config', n); };
    document.getElementById('modal-clone-cancel').onclick = close;
};

/**
 * Handles "Clone Project" quick action
 */
window.quickCloneProject = function (buttonElement, url, projectName, isPublished = false) {
    window.adminCloneChoice(projectName, url, (mode, newName) => {
        executeCloneAction(buttonElement, url, mode, newName);
    }, isPublished);
};

/**
 * Execution logic for Cloning
 */
function executeCloneAction(buttonElement, url, cloneMode, newName) {
    const container = buttonElement.closest('div');
    if (container) {
        buttonElement.disabled = true;
        container.style.opacity = '0.5';
    }

    const csrftoken = window.getAdminCookie('csrftoken');

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({
            clone_mode: cloneMode,
            new_name: newName
        }),
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(
                    err => { throw err; },
                    () => { throw new Error(`Server returned ${response.status}`); }
                );
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                window.adminNotify('success', 'Project Cloned!', data.message, 4000);
                console.log("Cloning success, redirecting to project list...");
                setTimeout(() => window.location.replace('/admin/annotation/project/'), 1000);
            } else {
                window.adminNotify('error', 'Cloning Failed', data.message || 'Unknown error');
                if (container) { buttonElement.disabled = false; container.style.opacity = '1'; }
            }
        })
        .catch(error => {
            console.error('Clone failed:', error);
            window.adminNotify('error', 'Action Failed', error.message || 'Network error');
            if (container) { buttonElement.disabled = false; container.style.opacity = '1'; }
        });
}

/**
 * Handles quick "Run MACE Analysis" action from the operations panel
 */
window.quickRunMace = function (buttonElement, url) {
    const isLive = document.body.classList.contains('project-is-live'); // Optional: check if we can detect status
    
    window.adminConfirm(
        "MACE ANALYSIS",
        "This will calculate the most likely correct labels and annotator reliability scores.\n\n" +
        "ℹ️ **Note:** Since this project is in development, all annotations (including test ones) will be used. Once the project is **LIVE**, only production data will be considered.",
        "🤖",
        "Run Analysis",
        "#8b5cf6", // Purple
        () => executeRunMaceAction(buttonElement, url)
    );
};

function executeRunMaceAction(buttonElement, url) {
    const container = buttonElement.closest('div');
    if (container) {
        buttonElement.disabled = true;
        container.style.opacity = '0.5';
    }

    const csrftoken = window.getAdminCookie('csrftoken');

    window.adminNotify('info', 'MACE Analysis', 'Starting reliability analysis... please wait.', 5000);

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({}),
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(
                    err => { throw err; },
                    () => { throw new Error(`Server returned ${response.status}`); }
                );
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                window.adminNotify('success', 'Analysis Completed!', data.message, 8000);
            } else {
                window.adminNotify('error', 'MACE Analysis Failed', data.message || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('MACE failed:', error);
            window.adminNotify('error', 'Action Failed', error.message || 'Network error');
        })
        .finally(() => {
            if (container) {
                buttonElement.disabled = false;
                container.style.opacity = '1';
            }
        });
};

/**
 * Handles confirmation and download for Export JSONL
 */
window.quickExportProject = function (buttonElement, url, projectName) {
    window.adminConfirm(
        "EXPORT DATA",
        `Do you want to download the annotation dataset for **${projectName}**?\n\nThis will generate a .jsonl file with all current annotations.`,
        "📥",
        "Download Now",
        "#10b981", // Emerald/Green
        () => {
            // Standard trigger to download file by opening the URL in same/new tab
            window.location.href = url;
            window.adminNotify('success', 'Export Started', 'Generating file for download...', 2000);
        }
    );
};

/**
 * Handles quick "Nuke Data" action from the project list view
 */
window.quickNukeProject = function (buttonElement, url) {
    window.adminConfirm(
        "NUKE TEST DATA",
        "Are you sure you want to delete ALL test annotations and worker enrollments?\n\nThis action CANNOT be undone.",
        "☢️",
        "Yes, Nuke Data",
        "#dc2626", // Red
        () => executeProjectPostAction(buttonElement, url, 'nuke', 'warning', 'Data Nuked ☢️')
    );
};

/**
 * Handles "Launch Official" action from the project list view
 */
window.quickLaunchProject = function (buttonElement, url) {
    window.adminConfirm(
        "OFFICIAL DEPLOYMENT",
        "This will permanently NUKE all playground test data, switch the project to LIVE, and LOCK the configuration forever.\n\nAre you sure you and your team are ready to collect real data?",
        "🚀",
        "Launch Official!",
        "linear-gradient(135deg, #10b981, #059669)", // Emerald
        () => executeProjectPostAction(buttonElement, url, 'launch', 'success', 'Project Launched 🚀')
    );
};

/**
 * Reusable execution core for Launch and Nuke
 */
window.executeProjectPostAction = function (buttonElement, url, actionName, successNotifyType, successNotifyTitle) {
    const container = buttonElement.closest('div');
    if (container) {
        buttonElement.disabled = true;
        container.style.opacity = '0.5';
    }

    const csrftoken = window.getAdminCookie('csrftoken');

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ action: actionName }),
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(
                    err => { throw err; },
                    () => { throw new Error(`Server returned ${response.status}`); }
                );
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                window.adminNotify(successNotifyType, successNotifyTitle, data.message, 3000);
                setTimeout(() => window.location.reload(), 1000);
            } else {
                window.adminNotify('error', 'Action Failed', data.message || 'Unknown error');
                if (container) {
                    buttonElement.disabled = false;
                    container.style.opacity = '1';
                }
            }
        })
        .catch(error => {
            console.error('Action failed:', error);
            const msg = error.message || (typeof error === 'string' ? error : 'The action request failed due to a server error.');
            window.adminNotify('error', 'Action Failed', msg);
            if (container) {
                buttonElement.disabled = false;
                container.style.opacity = '1';
            }
        });
}

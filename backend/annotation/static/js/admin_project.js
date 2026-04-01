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
    // CSRF Token Helper
    window.getAdminCookie = function(name) {
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
            <div class="admin-popup-message">${message}</div>
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
window.quickUpdateStatus = function (buttonElement, url, newStatus) {
    const container = buttonElement.closest('.status-badge-container');
    
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
window.adminConfirm = function(title, message, emojis, confirmText, confirmColor, onConfirm) {
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
        <p style="margin: 0 0 28px 0; font-size: 14px; color: #94a3b8; line-height: 1.6;">${message.replace(/\n/g, '<br>')}</p>
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
        const anim = overlay.animate([ { opacity: 1 }, { opacity: 0 } ], { duration: 150, easing: 'ease-in' });
        anim.onfinish = () => overlay.remove();
    };
    
    document.getElementById('modal-cancel-btn').onclick = close;
    document.getElementById('modal-cancel-btn').onmouseover = function() { this.style.backgroundColor = '#334155'; };
    document.getElementById('modal-cancel-btn').onmouseout = function() { this.style.backgroundColor = 'transparent'; };
    
    document.getElementById('modal-confirm-btn').onclick = () => {
        close();
        onConfirm();
    };
};

/**
 * Specific modal for Project Cloning choice
 */
window.adminCloneChoice = function(projectName, url, onClone) {
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
    
    modal.innerHTML = `
        <div style="font-size: 48px; margin-bottom: 16px; line-height: 1;">📋</div>
        <h2 style="margin: 0 0 12px 0; font-size: 20px; font-weight: 800;">Clone Project</h2>
        <p style="margin: 0 0 28px 0; font-size: 14px; color: #94a3b8; line-height: 1.6;">How would you like to clone <b>${projectName}</b>?</p>
        
        <div style="display: flex; flex-direction: column; gap: 10px;">
            <button id="modal-clone-full" style="padding: 14px; border-radius: 8px; border: none; background: #6366f1; color: white; cursor: pointer; font-weight: 700; font-size: 14px;">🚀 Full Clone (Docs + Config)</button>
            <button id="modal-clone-config" style="padding: 12px; border-radius: 8px; border: 1px solid #475569; background: #334155; color: white; cursor: pointer; font-weight: 600; font-size: 14px;">⚙️ Clone Config Only</button>
            <button id="modal-clone-cancel" style="padding: 10px; background: transparent; border: none; color: #94a3b8; cursor: pointer; font-size: 13px; margin-top: 5px;">Cancel</button>
        </div>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    const close = () => {
        overlay.animate([ { opacity: 1 }, { opacity: 0 } ], { duration: 150 }).onfinish = () => overlay.remove();
    };
    
    document.getElementById('modal-clone-full').onclick = () => { close(); onClone(true); };
    document.getElementById('modal-clone-config').onclick = () => { close(); onClone(false); };
    document.getElementById('modal-clone-cancel').onclick = close;
};

/**
 * Handles "Clone Project" quick action
 */
window.quickCloneProject = function (buttonElement, url, projectName) {
    window.adminCloneChoice(projectName, url, (withDataset) => {
        executeCloneAction(buttonElement, url, withDataset);
    });
};

/**
 * Execution logic for Cloning
 */
function executeCloneAction(buttonElement, url, withDataset) {
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
        body: JSON.stringify({ clone_dataset: withDataset }),
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
                setTimeout(() => window.location.reload(), 1000);
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
window.executeProjectPostAction = function(buttonElement, url, actionName, successNotifyType, successNotifyTitle) {
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

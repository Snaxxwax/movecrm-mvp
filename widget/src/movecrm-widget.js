/**
 * MoveCRM Embeddable Quote Widget
 * 
 * Usage:
 * <script src="https://cdn.movecrm.com/widget/movecrm-widget.js"></script>
 * <script>
 *   MoveCRMWidget.init({
 *     tenantSlug: 'your-company',
 *     apiUrl: 'https://api.movecrm.com',
 *     containerId: 'movecrm-widget',
 *     theme: 'light'
 *   });
 * </script>
 */

(function(window, document) {
  'use strict';

  // Widget configuration
  let config = {
    tenantSlug: '',
    apiUrl: 'https://api.movecrm.com',
    containerId: 'movecrm-widget',
    theme: 'light',
    primaryColor: '#2563eb',
    borderRadius: '8px',
    maxFileSize: 50 * 1024 * 1024, // 50MB
    allowedFileTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    maxFiles: 5
  };

  // Widget state
  let state = {
    isOpen: false,
    isSubmitting: false,
    files: [],
    formData: {}
  };

  // Utility functions
  function createElement(tag, className, innerHTML) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (innerHTML) element.innerHTML = innerHTML;
    return element;
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  function validateFile(file) {
    if (!config.allowedFileTypes.includes(file.type)) {
      return `File type ${file.type} is not allowed. Please upload images only.`;
    }
    if (file.size > config.maxFileSize) {
      return `File size ${formatFileSize(file.size)} exceeds the maximum allowed size of ${formatFileSize(config.maxFileSize)}.`;
    }
    return null;
  }

  function showNotification(message, type = 'info') {
    const notification = createElement('div', `movecrm-notification movecrm-notification-${type}`, message);
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.classList.add('movecrm-notification-show');
    }, 100);

    setTimeout(() => {
      notification.classList.remove('movecrm-notification-show');
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 5000);
  }

  // Widget HTML template
  function getWidgetHTML() {
    return `
      <div class="movecrm-widget-overlay" id="movecrm-overlay">
        <div class="movecrm-widget-modal">
          <div class="movecrm-widget-header">
            <h2>Get Your Moving Quote</h2>
            <button class="movecrm-widget-close" id="movecrm-close">&times;</button>
          </div>
          
          <form class="movecrm-widget-form" id="movecrm-form">
            <div class="movecrm-form-group">
              <label for="movecrm-name">Full Name *</label>
              <input type="text" id="movecrm-name" name="name" required>
            </div>
            
            <div class="movecrm-form-group">
              <label for="movecrm-email">Email Address *</label>
              <input type="email" id="movecrm-email" name="email" required>
            </div>
            
            <div class="movecrm-form-group">
              <label for="movecrm-phone">Phone Number</label>
              <input type="tel" id="movecrm-phone" name="phone">
            </div>
            
            <div class="movecrm-form-row">
              <div class="movecrm-form-group">
                <label for="movecrm-pickup">Pickup Address *</label>
                <input type="text" id="movecrm-pickup" name="pickup_address" required>
              </div>
              
              <div class="movecrm-form-group">
                <label for="movecrm-delivery">Delivery Address *</label>
                <input type="text" id="movecrm-delivery" name="delivery_address" required>
              </div>
            </div>
            
            <div class="movecrm-form-group">
              <label for="movecrm-date">Preferred Move Date</label>
              <input type="date" id="movecrm-date" name="move_date">
            </div>
            
            <div class="movecrm-form-group">
              <label for="movecrm-notes">Additional Notes</label>
              <textarea id="movecrm-notes" name="notes" rows="3" placeholder="Tell us about your move, special items, or any specific requirements..."></textarea>
            </div>
            
            <div class="movecrm-form-group">
              <label>Upload Photos of Items (Optional)</label>
              <div class="movecrm-file-upload" id="movecrm-file-upload">
                <input type="file" id="movecrm-files" name="files" multiple accept="image/*" style="display: none;">
                <div class="movecrm-file-drop-zone" id="movecrm-drop-zone">
                  <div class="movecrm-file-drop-content">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="7,10 12,15 17,10"></polyline>
                      <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    <p>Drop images here or <button type="button" class="movecrm-file-browse">browse files</button></p>
                    <small>Max ${config.maxFiles} files, ${formatFileSize(config.maxFileSize)} each</small>
                  </div>
                </div>
                <div class="movecrm-file-list" id="movecrm-file-list"></div>
              </div>
            </div>
            
            <div class="movecrm-form-actions">
              <button type="button" class="movecrm-btn movecrm-btn-secondary" id="movecrm-cancel">Cancel</button>
              <button type="submit" class="movecrm-btn movecrm-btn-primary" id="movecrm-submit">
                <span class="movecrm-submit-text">Get Quote</span>
                <span class="movecrm-submit-loading" style="display: none;">
                  <svg class="movecrm-spinner" width="16" height="16" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" opacity="0.25"></circle>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="4" fill="none"></path>
                  </svg>
                  Submitting...
                </span>
              </button>
            </div>
          </form>
        </div>
      </div>
    `;
  }

  // Widget CSS
  function getWidgetCSS() {
    return `
      .movecrm-widget-trigger {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: ${config.primaryColor};
        color: white;
        border: none;
        border-radius: 50px;
        padding: 16px 24px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      
      .movecrm-widget-trigger:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
      }
      
      .movecrm-widget-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 1000000;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      
      .movecrm-widget-overlay.movecrm-widget-open {
        display: flex;
      }
      
      .movecrm-widget-modal {
        background: white;
        border-radius: ${config.borderRadius};
        width: 90%;
        max-width: 600px;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        animation: movecrm-modal-enter 0.3s ease;
      }
      
      @keyframes movecrm-modal-enter {
        from {
          opacity: 0;
          transform: scale(0.9) translateY(20px);
        }
        to {
          opacity: 1;
          transform: scale(1) translateY(0);
        }
      }
      
      .movecrm-widget-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 24px;
        border-bottom: 1px solid #e5e7eb;
      }
      
      .movecrm-widget-header h2 {
        margin: 0;
        font-size: 24px;
        font-weight: 700;
        color: #111827;
      }
      
      .movecrm-widget-close {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #6b7280;
        padding: 4px;
        border-radius: 4px;
        transition: all 0.2s ease;
      }
      
      .movecrm-widget-close:hover {
        background: #f3f4f6;
        color: #374151;
      }
      
      .movecrm-widget-form {
        padding: 24px;
      }
      
      .movecrm-form-group {
        margin-bottom: 20px;
      }
      
      .movecrm-form-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
      }
      
      @media (max-width: 640px) {
        .movecrm-form-row {
          grid-template-columns: 1fr;
        }
      }
      
      .movecrm-form-group label {
        display: block;
        margin-bottom: 6px;
        font-weight: 500;
        color: #374151;
        font-size: 14px;
      }
      
      .movecrm-form-group input,
      .movecrm-form-group textarea {
        width: 100%;
        padding: 12px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 16px;
        transition: border-color 0.2s ease;
        box-sizing: border-box;
      }
      
      .movecrm-form-group input:focus,
      .movecrm-form-group textarea:focus {
        outline: none;
        border-color: ${config.primaryColor};
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
      }
      
      .movecrm-file-upload {
        margin-top: 8px;
      }
      
      .movecrm-file-drop-zone {
        border: 2px dashed #d1d5db;
        border-radius: 8px;
        padding: 32px;
        text-align: center;
        transition: all 0.2s ease;
        cursor: pointer;
      }
      
      .movecrm-file-drop-zone:hover,
      .movecrm-file-drop-zone.movecrm-drag-over {
        border-color: ${config.primaryColor};
        background: rgba(37, 99, 235, 0.05);
      }
      
      .movecrm-file-drop-content svg {
        color: #9ca3af;
        margin-bottom: 12px;
      }
      
      .movecrm-file-drop-content p {
        margin: 0 0 8px 0;
        color: #6b7280;
        font-size: 16px;
      }
      
      .movecrm-file-browse {
        background: none;
        border: none;
        color: ${config.primaryColor};
        cursor: pointer;
        text-decoration: underline;
        font-size: 16px;
      }
      
      .movecrm-file-drop-content small {
        color: #9ca3af;
        font-size: 14px;
      }
      
      .movecrm-file-list {
        margin-top: 16px;
      }
      
      .movecrm-file-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px;
        background: #f9fafb;
        border-radius: 6px;
        margin-bottom: 8px;
      }
      
      .movecrm-file-info {
        display: flex;
        align-items: center;
        flex: 1;
      }
      
      .movecrm-file-info img {
        width: 40px;
        height: 40px;
        object-fit: cover;
        border-radius: 4px;
        margin-right: 12px;
      }
      
      .movecrm-file-details h4 {
        margin: 0 0 4px 0;
        font-size: 14px;
        font-weight: 500;
        color: #374151;
      }
      
      .movecrm-file-details p {
        margin: 0;
        font-size: 12px;
        color: #6b7280;
      }
      
      .movecrm-file-remove {
        background: none;
        border: none;
        color: #ef4444;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: background 0.2s ease;
      }
      
      .movecrm-file-remove:hover {
        background: #fee2e2;
      }
      
      .movecrm-form-actions {
        display: flex;
        gap: 12px;
        justify-content: flex-end;
        margin-top: 32px;
        padding-top: 24px;
        border-top: 1px solid #e5e7eb;
      }
      
      .movecrm-btn {
        padding: 12px 24px;
        border-radius: 6px;
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        border: none;
        display: inline-flex;
        align-items: center;
        gap: 8px;
      }
      
      .movecrm-btn-primary {
        background: ${config.primaryColor};
        color: white;
      }
      
      .movecrm-btn-primary:hover:not(:disabled) {
        background: #1d4ed8;
      }
      
      .movecrm-btn-primary:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      
      .movecrm-btn-secondary {
        background: #f3f4f6;
        color: #374151;
      }
      
      .movecrm-btn-secondary:hover {
        background: #e5e7eb;
      }
      
      .movecrm-spinner {
        animation: movecrm-spin 1s linear infinite;
      }
      
      @keyframes movecrm-spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      
      .movecrm-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000001;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        max-width: 400px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      
      .movecrm-notification-show {
        transform: translateX(0);
      }
      
      .movecrm-notification-success {
        background: #10b981;
      }
      
      .movecrm-notification-error {
        background: #ef4444;
      }
      
      .movecrm-notification-info {
        background: #3b82f6;
      }
      
      @media (max-width: 640px) {
        .movecrm-widget-modal {
          width: 95%;
          margin: 20px;
        }
        
        .movecrm-widget-header,
        .movecrm-widget-form {
          padding: 16px;
        }
        
        .movecrm-form-actions {
          flex-direction: column;
        }
        
        .movecrm-notification {
          right: 10px;
          left: 10px;
          max-width: none;
        }
      }
    `;
  }

  // File handling
  function handleFileSelect(files) {
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      if (state.files.length >= config.maxFiles) {
        showNotification(`Maximum ${config.maxFiles} files allowed`, 'error');
        break;
      }
      
      const error = validateFile(file);
      if (error) {
        showNotification(error, 'error');
        continue;
      }
      
      const fileObj = {
        file: file,
        id: Date.now() + i,
        preview: null
      };
      
      // Create preview for images
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
          fileObj.preview = e.target.result;
          renderFileList();
        };
        reader.readAsDataURL(file);
      }
      
      state.files.push(fileObj);
    }
    
    renderFileList();
  }

  function removeFile(fileId) {
    state.files = state.files.filter(f => f.id !== fileId);
    renderFileList();
  }

  function renderFileList() {
    const fileList = document.getElementById('movecrm-file-list');
    if (!fileList) return;
    
    if (state.files.length === 0) {
      fileList.innerHTML = '';
      return;
    }
    
    fileList.innerHTML = state.files.map(fileObj => `
      <div class="movecrm-file-item">
        <div class="movecrm-file-info">
          ${fileObj.preview ? `<img src="${fileObj.preview}" alt="Preview">` : '<div style="width: 40px; height: 40px; background: #e5e7eb; border-radius: 4px; margin-right: 12px;"></div>'}
          <div class="movecrm-file-details">
            <h4>${fileObj.file.name}</h4>
            <p>${formatFileSize(fileObj.file.size)}</p>
          </div>
        </div>
        <button type="button" class="movecrm-file-remove" onclick="MoveCRMWidget.removeFile(${fileObj.id})">&times;</button>
      </div>
    `).join('');
  }

  // Form submission
  async function submitForm(formData) {
    const submitButton = document.getElementById('movecrm-submit');
    const submitText = submitButton.querySelector('.movecrm-submit-text');
    const submitLoading = submitButton.querySelector('.movecrm-submit-loading');
    
    // Show loading state
    state.isSubmitting = true;
    submitButton.disabled = true;
    submitText.style.display = 'none';
    submitLoading.style.display = 'flex';
    
    try {
      const response = await fetch(`${config.apiUrl}/public/quote`, {
        method: 'POST',
        headers: {
          'X-Tenant-Slug': config.tenantSlug
        },
        body: formData
      });
      
      if (response.ok) {
        const result = await response.json();
        showNotification('Quote request submitted successfully! We\'ll get back to you soon.', 'success');
        closeWidget();
        resetForm();
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Failed to submit quote request');
      }
    } catch (error) {
      console.error('Quote submission error:', error);
      showNotification(error.message || 'Failed to submit quote request. Please try again.', 'error');
    } finally {
      // Reset loading state
      state.isSubmitting = false;
      submitButton.disabled = false;
      submitText.style.display = 'inline';
      submitLoading.style.display = 'none';
    }
  }

  function resetForm() {
    const form = document.getElementById('movecrm-form');
    if (form) {
      form.reset();
      state.files = [];
      renderFileList();
    }
  }

  // Widget controls
  function openWidget() {
    state.isOpen = true;
    const overlay = document.getElementById('movecrm-overlay');
    if (overlay) {
      overlay.classList.add('movecrm-widget-open');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeWidget() {
    state.isOpen = false;
    const overlay = document.getElementById('movecrm-overlay');
    if (overlay) {
      overlay.classList.remove('movecrm-widget-open');
      document.body.style.overflow = '';
    }
  }

  // Event handlers
  function setupEventHandlers() {
    // Close button
    const closeButton = document.getElementById('movecrm-close');
    if (closeButton) {
      closeButton.addEventListener('click', closeWidget);
    }
    
    // Cancel button
    const cancelButton = document.getElementById('movecrm-cancel');
    if (cancelButton) {
      cancelButton.addEventListener('click', closeWidget);
    }
    
    // Overlay click to close
    const overlay = document.getElementById('movecrm-overlay');
    if (overlay) {
      overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
          closeWidget();
        }
      });
    }
    
    // Form submission
    const form = document.getElementById('movecrm-form');
    if (form) {
      form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (state.isSubmitting) return;
        
        const formData = new FormData(form);
        
        // Add files
        state.files.forEach(fileObj => {
          formData.append('files', fileObj.file);
        });
        
        submitForm(formData);
      });
    }
    
    // File upload
    const fileInput = document.getElementById('movecrm-files');
    const dropZone = document.getElementById('movecrm-drop-zone');
    const browseButton = dropZone?.querySelector('.movecrm-file-browse');
    
    if (fileInput && dropZone) {
      // File input change
      fileInput.addEventListener('change', function(e) {
        handleFileSelect(e.target.files);
        e.target.value = ''; // Reset input
      });
      
      // Browse button
      if (browseButton) {
        browseButton.addEventListener('click', function(e) {
          e.preventDefault();
          fileInput.click();
        });
      }
      
      // Drag and drop
      dropZone.addEventListener('click', function() {
        fileInput.click();
      });
      
      dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('movecrm-drag-over');
      });
      
      dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dropZone.classList.remove('movecrm-drag-over');
      });
      
      dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('movecrm-drag-over');
        handleFileSelect(e.dataTransfer.files);
      });
    }
  }

  // Initialize widget
  function init(options = {}) {
    // Merge configuration
    config = { ...config, ...options };
    
    // Validate required options
    if (!config.tenantSlug) {
      console.error('MoveCRM Widget: tenantSlug is required');
      return;
    }
    
    // Add CSS
    const style = document.createElement('style');
    style.textContent = getWidgetCSS();
    document.head.appendChild(style);
    
    // Create trigger button
    const trigger = createElement('button', 'movecrm-widget-trigger', '💬 Get Moving Quote');
    trigger.addEventListener('click', openWidget);
    document.body.appendChild(trigger);
    
    // Create widget modal
    const widgetContainer = createElement('div');
    widgetContainer.innerHTML = getWidgetHTML();
    document.body.appendChild(widgetContainer);
    
    // Setup event handlers
    setupEventHandlers();
    
    console.log('MoveCRM Widget initialized for tenant:', config.tenantSlug);
  }

  // Public API
  window.MoveCRMWidget = {
    init: init,
    open: openWidget,
    close: closeWidget,
    removeFile: removeFile,
    config: config,
    state: state
  };

})(window, document);


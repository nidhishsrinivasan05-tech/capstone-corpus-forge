/**
 * DOCUMENT UPLOAD & PREVIEW COMPONENT
 * Clean, modular UI component for ingesting documents
 * Supports Local Files and GitHub sources
 */

class DocumentIngestionComponent {
  constructor() {
    this.currentSource = 'local'; // 'local' or 'github'
    this.isProcessing = false;
    this.init();
  }

  init() {
    this.cacheElements();
    this.attachEventListeners();
    this.setupUI();
  }

  cacheElements() {
    // Source selector
    this.sourceToggle = document.getElementById('source-toggle');
    this.sourceSelect = document.getElementById('source-select');
    this.sourceLabel = document.getElementById('source-label');

    // Forms
    this.localForm = document.getElementById('upload-form');
    this.githubForm = document.getElementById('repo-form');

    // Input fields
    this.fileInput = document.querySelector('input[type="file"]');
    this.repoUrlInput = document.getElementById('repo_url');
    this.githubTokenInput = document.getElementById('github_token');

    // Buttons
    this.uploadBtn = this.localForm?.querySelector('button[type="submit"]');
    this.fetchRepoBtn = document.getElementById('fetch-repo-btn');

    // Status display
    this.repoStatus = document.getElementById('repo-status');
  }

  attachEventListeners() {
    // Source toggle
    if (this.sourceToggle) {
      this.sourceToggle.addEventListener('click', () => this.showSourceMenu());
    }

    if (this.sourceSelect) {
      this.sourceSelect.addEventListener('change', (e) => this.switchSource(e.target.value));
    }

    // GitHub fetch button
    if (this.fetchRepoBtn) {
      this.fetchRepoBtn.addEventListener('click', () => this.handleGitHubFetch());
    }

    // Form submissions
    if (this.localForm) {
      this.localForm.addEventListener('submit', (e) => this.handleFileUpload(e));
    }
  }

  setupUI() {
    // Set initial state
    this.switchSource(this.currentSource);
  }

  // ===== SOURCE MANAGEMENT =====

  showSourceMenu() {
    if (this.sourceSelect) {
      this.sourceSelect.click();
    }
  }

  switchSource(source) {
    this.currentSource = source;

    if (source === 'github') {
      this.localForm?.classList.remove('active-form');
      this.githubForm?.classList.add('active-form');
      this.sourceLabel.textContent = 'GitHub';
    } else {
      this.localForm?.classList.add('active-form');
      this.githubForm?.classList.remove('active-form');
      this.sourceLabel.textContent = 'Local';
    }
  }

  // ===== FILE UPLOAD =====

  handleFileUpload(event) {
    event.preventDefault();

    if (!this.fileInput?.files.length) {
      this.showToast('Please select a file', 'error');
      return;
    }

    const formData = new FormData(this.localForm);
    this.uploadFile(formData);
  }

  uploadFile(formData) {
    this.setProcessing(true, 'Uploading...');

    fetch('/upload_file', {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === 'ok') {
          this.showToast(`✓ Uploaded successfully (${data.count} file)`, 'success');
          this.fileInput.value = '';
          this.localForm.reset();
          setTimeout(() => window.location.reload(), 800);
        } else {
          this.showToast(data.error || 'Upload failed', 'error');
        }
      })
      .catch((error) => {
        console.error('Upload error:', error);
        this.showToast('Upload failed: ' + error.message, 'error');
      })
      .finally(() => {
        this.setProcessing(false);
      });
  }

  // ===== GITHUB IMPORT =====

  handleGitHubFetch() {
    const url = this.repoUrlInput?.value.trim();
    const token = this.githubTokenInput?.value.trim() || null;

    if (!url) {
      this.showToast('Enter a GitHub repository URL', 'error');
      return;
    }

    if (!this.isValidGitHubUrl(url)) {
      this.showToast('Invalid GitHub URL format (e.g., https://github.com/owner/repo)', 'error');
      return;
    }

    this.fetchRepository(url, token);
  }

  isValidGitHubUrl(url) {
    const pattern = /^https:\/\/github\.com\/[\w\-]+\/[\w\-\.]+\/?(?:\/tree\/[\w\-]+)?$/;
    return pattern.test(url);
  }

  fetchRepository(url, token) {
    this.setProcessing(true, 'Fetching repository...');
    this.setRepoStatus('Fetching repository contents...', 'info');

    const formData = new FormData();
    formData.append('repo_url', url);
    if (token) {
      formData.append('github_token', token);
    }

    fetch('/import_repo', {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === 'ok') {
          this.setRepoStatus(`✓ Imported ${data.count} files`, 'success');
          this.showToast(`Successfully imported ${data.count} files`, 'success');

          if (data.warnings && data.warnings.length > 0) {
            data.warnings.forEach((w) => console.warn('Warning:', w));
          }

          this.repoUrlInput.value = '';
          this.githubTokenInput.value = '';

          setTimeout(() => window.location.reload(), 1200);
        } else {
          this.setRepoStatus(data.error || 'Import failed', 'error');
          this.showToast(data.error || 'Import failed', 'error');
        }
      })
      .catch((error) => {
        console.error('Import error:', error);
        const errorMsg = error.message || 'Network error';
        this.setRepoStatus(errorMsg, 'error');
        this.showToast(errorMsg, 'error');
      })
      .finally(() => {
        this.setProcessing(false);
      });
  }

  // ===== UI HELPERS =====

  setRepoStatus(message, type = 'info') {
    if (this.repoStatus) {
      this.repoStatus.textContent = message;
      this.repoStatus.style.display = 'block';
      this.repoStatus.className = `repo-status repo-status-${type}`;
    }
  }

  setProcessing(isProcessing, buttonText = null) {
    this.isProcessing = isProcessing;

    if (this.fetchRepoBtn) {
      this.fetchRepoBtn.disabled = isProcessing;
      this.fetchRepoBtn.classList.toggle('loading', isProcessing);
      if (buttonText && isProcessing) {
        this.fetchRepoBtn.dataset.originalText = this.fetchRepoBtn.textContent;
        this.fetchRepoBtn.textContent = buttonText;
      } else if (this.fetchRepoBtn.dataset.originalText) {
        this.fetchRepoBtn.textContent = this.fetchRepoBtn.dataset.originalText;
      }
    }

    if (this.uploadBtn) {
      this.uploadBtn.disabled = isProcessing;
      this.uploadBtn.classList.toggle('loading', isProcessing);
    }
  }

  showToast(message, type = 'info') {
    // Reuse existing toast system or create simple notification
    const event = new CustomEvent('show-toast', {
      detail: { message, type }
    });
    document.dispatchEvent(event);

    // Fallback: console log
    console.log(`[${type.toUpperCase()}] ${message}`);
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.docIngestion = new DocumentIngestionComponent();
});

// ===== DOCUMENT PREVIEW COMPONENT =====

class DocumentPreviewComponent {
  constructor() {
    this.init();
  }

  init() {
    this.attachPreviewListeners();
  }

  attachPreviewListeners() {
    document.querySelectorAll('.btn-view-more').forEach((btn) => {
      btn.addEventListener('click', (e) => this.togglePreview(e.target));
    });
  }

  togglePreview(button) {
    const docRow = button.closest('.doc-row');
    if (!docRow) return;

    const fullPreview = docRow.querySelector('.doc-full-preview');
    const isExpanded = fullPreview?.style.display !== 'none';

    if (fullPreview) {
      fullPreview.style.display = isExpanded ? 'none' : 'block';
      button.textContent = isExpanded ? 'View more' : 'Show less';
      button.setAttribute('aria-expanded', !isExpanded);
    }
  }
}

// Initialize preview component
document.addEventListener('DOMContentLoaded', () => {
  window.docPreview = new DocumentPreviewComponent();
});

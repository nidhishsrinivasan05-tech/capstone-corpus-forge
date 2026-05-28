document.addEventListener("DOMContentLoaded", () => {
    const prefersReduced = window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    /* ========================================
       TOAST NOTIFICATIONS
    ======================================== */
    function getToastStack() {
        let stack = document.querySelector(".toast-stack");
        if (!stack) {
            stack = document.createElement("div");
            stack.className = "toast-stack";
            stack.setAttribute("aria-live", "polite");
            stack.setAttribute("aria-atomic", "true");
            document.body.appendChild(stack);
        }
        return stack;
    }

    function showToast(message, type = "success", timeout = 4600) {
        const stack = getToastStack();
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        toast.setAttribute("role", "alert");

        const dot = document.createElement("span");
        dot.className = "toast-dot";

        const text = document.createElement("span");
        text.textContent = message;

        toast.appendChild(dot);
        toast.appendChild(text);
        stack.appendChild(toast);

        if (!prefersReduced) {
            window.setTimeout(() => hideToast(toast), timeout);
        }

        return toast;
    }

    function hideToast(toast) {
        toast.classList.add("is-hiding");
        toast.addEventListener("animationend", () => toast.remove(), { once: true });
    }

    /* ========================================
       LOADING STATES
    ======================================== */
    function setLoadingState(button, isLoading, loadingText) {
        if (!button) return;

        if (isLoading) {
            button.dataset.originalText = button.textContent;
            button.textContent = loadingText || "Processing...";
            button.classList.add("loading");
            button.disabled = true;
        } else {
            button.textContent = button.dataset.originalText || button.textContent;
            button.classList.remove("loading");
            button.disabled = false;
        }
    }

    function setFormLoading(form, isLoading, loadingText) {
        const button = form.querySelector('button[type="submit"], button[type="button"]');
        if (button) {
            setLoadingState(button, isLoading, loadingText);
        }

        // Also disable all inputs in the form
        form.querySelectorAll("input, select, textarea").forEach(el => {
            el.disabled = isLoading;
        });
    }

    async function fetchWithFeedback(url, options = {}) {
        const loader = showToast("Refreshing dashboard...", "warning", 60000);
        try {
            const response = await fetch(url, options);
            const payload = await response.json();
            loader.remove();
            if (!response.ok) {
                throw new Error(payload.error || `Request failed (${response.status})`);
            }
            return payload;
        } catch (error) {
            loader.remove();
            showToast(error.message || "Network error", "error");
            throw error;
        }
    }

    /* ========================================
       AUTO-HIDE SERVER FLASHES
    ======================================== */
    document.querySelectorAll(".toast").forEach((toast) => {
        if (!prefersReduced) {
            window.setTimeout(() => hideToast(toast), 5000);
        }
    });

    /* ========================================
       FILE DROP LABEL UPDATE
    ======================================== */
    document.querySelectorAll(".file-drop input[type='file']").forEach((input) => {
        input.addEventListener("change", () => {
            const fileName = input.files && input.files.length ? input.files[0].name : "Choose a file";
            const label = input.closest(".file-drop");
            const strong = label ? label.querySelector("strong") : null;
            if (strong) {
                strong.textContent = fileName;
            }
        });
    });

    /* ========================================
       COPY ARTIFACT BUTTONS
    ======================================== */
    document.querySelectorAll(".copy-artifact").forEach((button) => {
        button.addEventListener("click", async() => {
            const article = button.closest(".artifact");
            const content = article ? article.querySelector("pre") : null;
            if (!content || !navigator.clipboard) {
                showToast("Clipboard is not available in this browser.", "warning");
                return;
            }
            try {
                await navigator.clipboard.writeText(content.textContent);
                const original = button.textContent;
                button.textContent = "Copied";
                showToast("Artifact copied.", "success", 1600);
                window.setTimeout(() => {
                    button.textContent = original;
                }, 1600);
            } catch (error) {
                showToast("Copy failed.", "error");
            }
        });
    });

    /* ========================================
       ANSWER PANEL SCROLL
    ======================================== */
    const answerPanel = document.getElementById("answer-panel");
    if (answerPanel) {
        answerPanel.scrollIntoView({
            behavior: prefersReduced ? "auto" : "smooth",
            block: "start",
        });
    }

    /* ========================================
       METRICS REFRESH
    ======================================== */
    function setMetric(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    async function refreshStats() {
        const refreshButton = document.getElementById("refresh-stats");
        if (refreshButton) {
            refreshButton.disabled = true;
            refreshButton.classList.add("loading");
        }
        try {
            const payload = await fetchWithFeedback("/api/stats");
            const stats = payload.stats || {};
            const usage = payload.usage || {};
            setMetric("stat-documents", stats.document_count ?? 0);
            setMetric("stat-words", stats.indexed_words ?? 0);
            setMetric("stat-artifacts", stats.artifact_count ?? 0);
            setMetric("stat-requests", usage.request_count ?? 0);
            setMetric("stat-tokens", `${usage.token_count ?? 0} est. tokens`);
            showToast("Dashboard stats refreshed.", "success", 1600);
        } finally {
            if (refreshButton) {
                refreshButton.disabled = false;
                refreshButton.classList.remove("loading");
            }
        }
    }

    const refreshButton = document.getElementById("refresh-stats");
    if (refreshButton) {
        refreshButton.addEventListener("click", refreshStats);
    }

    /* ========================================
       SOURCE TOGGLE (Local vs GitHub)
    ======================================== */
    const sourceSelect = document.getElementById('source-select');
    const sourceLabel = document.getElementById('source-label');
    const uploadForm = document.getElementById('upload-form');
    const repoForm = document.getElementById('repo-form');
    const sourcePill = document.getElementById('source-toggle');

    function setSource(source) {
        sourceLabel.textContent = source === 'github' ? 'GitHub' : 'Local';

        if (source === 'github') {
            uploadForm.classList.remove('active-form');
            repoForm.classList.add('active-form');
            repoForm.style.display = 'block';
        } else {
            uploadForm.classList.add('active-form');
            repoForm.classList.remove('active-form');
            repoForm.style.display = 'none';
        }
    }

    if (sourceSelect) {
        setSource(sourceSelect.value);

        sourceSelect.addEventListener('change', (e) => {
            setSource(e.target.value);
        });

        // Make the pill clickable to reveal the hidden select
        if (sourcePill) {
            sourcePill.addEventListener('click', () => {
                sourceSelect.click();
            });

            sourcePill.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    sourceSelect.click();
                }
            });
        }
    }

    /* ========================================
       LOCAL FILE UPLOAD FORM
    ======================================== */
    if (uploadForm) {
        uploadForm.addEventListener('submit', (e) => {
            const fileInput = uploadForm.querySelector('input[type="file"]');
            if (!fileInput || !fileInput.files || !fileInput.files.length) {
                e.preventDefault();
                showToast("Choose a file before uploading.", "warning");
                return;
            }

            const submitBtn = uploadForm.querySelector('button[type="submit"]');
            setLoadingState(submitBtn, true, "Uploading file...");
        });

        // For AJAX-style upload (optional progressive enhancement)
        uploadForm.dataset.asyncUpload = "true";
    }

    /* ========================================
       GITHUB REPOSITORY FETCH
    ======================================== */
    const fetchRepoBtn = document.getElementById('fetch-repo-btn');
    const repoUrlInput = document.getElementById('repo_url');
    const githubTokenInput = document.getElementById('github_token');
    const repoStatus = document.getElementById('repo-status');

    function isValidGithubUrl(url) {
        try {
            const u = new URL(url);
            const pathParts = u.pathname.split('/').filter(Boolean);
            // Must be github.com/owner/repo format
            return u.hostname === 'github.com' && pathParts.length >= 2;
        } catch (e) {
            return false;
        }
    }

    function setRepoStatus(message, type = 'info') {
        repoStatus.textContent = message;
        repoStatus.style.display = 'block';
        repoStatus.className = `repo-status ${type}`;
    }

    function clearRepoStatus() {
        repoStatus.style.display = 'none';
        repoStatus.textContent = '';
        repoStatus.className = 'repo-status';
    }

    if (fetchRepoBtn && repoForm) {
        fetchRepoBtn.addEventListener('click', async() => {
            const url = repoUrlInput?.value.trim();
            const token = githubTokenInput?.value.trim();

            // Validation
            if (!url) {
                showToast('Enter a GitHub repository URL.', 'error');
                repoUrlInput?.focus();
                return;
            }

            if (!isValidGithubUrl(url)) {
                showToast('Invalid GitHub URL. Use: https://github.com/owner/repo', 'error');
                repoUrlInput?.focus();
                return;
            }

            // Set loading state
            setFormLoading(repoForm, true, "Fetching repository...");
            setRepoStatus('Connecting to GitHub...', 'info');

            try {
                const formData = new FormData();
                formData.append('repo_url', url);
                if (token) {
                    formData.append('github_token', token);
                }

                const response = await fetch(repoForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const payload = await response.json();

                if (!response.ok) {
                    const errorMsg = payload.error || `Request failed (${response.status})`;
                    setRepoStatus(errorMsg, 'error');
                    showToast(errorMsg, 'error');
                    return;
                }

                if (payload.status === 'ok') {
                    const count = payload.count || 0;
                    setRepoStatus(`Successfully imported ${count} files!`, 'success');
                    showToast(`Imported ${count} files from repository.`, 'success');

                    // Clear inputs
                    if (repoUrlInput) repoUrlInput.value = '';
                    if (githubTokenInput) githubTokenInput.value = '';

                    // Reload page after brief delay to show results
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    const errorMsg = payload.error || 'Import failed';
                    setRepoStatus(errorMsg, 'error');
                    showToast(errorMsg, 'error');
                }

            } catch (err) {
                const errorMsg = err.message || 'Network error. Check your connection.';
                setRepoStatus(errorMsg, 'error');
                showToast(errorMsg, 'error');
                console.error('GitHub fetch error:', err);
            } finally {
                setFormLoading(repoForm, false);
            }
        });

        // Enter key in URL field triggers fetch
        if (repoUrlInput) {
            repoUrlInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    fetchRepoBtn?.click();
                }
            });
        }
    }

    /* ========================================
       DOCUMENT LIST VIEW MORE / SHOW LESS
    ======================================== */
    document.querySelectorAll('.btn-view-more').forEach((btn) => {
        btn.addEventListener('click', function() {
            const docRow = this.closest('.doc-row');
            if (!docRow) return;

            const fullPreview = docRow.querySelector('.doc-full-preview');
            const shortPreview = docRow.querySelector('.doc-short');
            const isExpanded = fullPreview ? fullPreview.style.display !== 'none' : false;

            if (fullPreview) {
                if (isExpanded) {
                    // Collapse
                    fullPreview.style.display = 'none';
                    if (shortPreview) shortPreview.style.display = '';
                    this.textContent = 'View more';
                    this.setAttribute('aria-expanded', 'false');
                    this.classList.remove('expanded');
                } else {
                    // Expand
                    fullPreview.style.display = 'block';
                    if (shortPreview) shortPreview.style.display = 'none';
                    this.textContent = 'Show less';
                    this.setAttribute('aria-expanded', 'true');
                    this.classList.add('expanded');
                }
            }
        });
    });

    /* ========================================
       DELETE DOCUMENT WITH CONFIRM
    ======================================== */
    document.querySelectorAll('.doc-delete-form').forEach((form) => {
        form.addEventListener('submit', function(e) {
            const message = this.dataset.confirm;
            if (message && !window.confirm(message)) {
                e.preventDefault();
                return;
            }

            const btn = this.querySelector('button');
            if (btn) {
                setLoadingState(btn, true, "Removing...");
            }
        });
    });

    /* ========================================
       EXPOSE PUBLIC API
    ======================================== */
    window.CorpusForge = {
        showToast,
        hideToast,
        fetchWithFeedback,
        setLoadingState,
        refreshStats,
        isValidGithubUrl
    };
});
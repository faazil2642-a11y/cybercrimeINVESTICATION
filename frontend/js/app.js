// CyberTrace AI — Platform Application Logic

let currentView = 'overview';
let activeCase = null;
let casesCache = [];
let evidenceCache = [];

// ── Toast Notification Helper ──
let toastTimer = null;
window.showToast = function(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastText = document.getElementById('toast-text');
    const toastDot = document.getElementById('toast-dot');
    if (!toast || !toastText) return;

    toastText.innerText = message;
    if (type === 'error') {
        toastDot.className = 'w-2 h-2 rounded-full bg-error';
    } else if (type === 'success') {
        toastDot.className = 'w-2 h-2 rounded-full bg-secondary';
    } else {
        toastDot.className = 'w-2 h-2 rounded-full bg-primary animate-ping';
    }

    toast.classList.remove('opacity-0', '-translate-y-2');
    toast.classList.add('opacity-100', 'translate-y-0');

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.remove('opacity-100', 'translate-y-0');
        toast.classList.add('opacity-0', '-translate-y-2');
    }, 2800);
};

// ── Utility: Debounce ──
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// ── View Navigation ──
window.switchView = function(viewName) {
    currentView = viewName;

    // Hide all view panels
    document.querySelectorAll('.view-panel').forEach(el => el.classList.add('hidden'));

    // Show target view panel
    const target = document.getElementById(`view-${viewName}`);
    if (target) {
        target.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Update bottom nav active state
    document.querySelectorAll('.nav-tab').forEach(tab => {
        if (tab.getAttribute('data-target') === viewName) {
            tab.className = 'nav-tab flex flex-col items-center justify-center gap-1 w-16 h-14 text-primary font-semibold';
        } else {
            tab.className = 'nav-tab flex flex-col items-center justify-center gap-1 w-16 h-14 text-on-surface-variant hover:text-on-surface';
        }
    });

    // Update top header labels
    const pageTitles = {
        'overview': 'INVESTIGATION OVERVIEW',
        'cases': 'CASE DOSSIERS',
        'evidence': 'CRYPTOGRAPHIC EVIDENCE VAULT',
        'ai-assistant': 'AI INVESTIGATION (RAG)',
        'logs': 'FORENSIC LOG ANALYZER',
        'ip': 'IP INTELLIGENCE & TELEMETRY',
        'timeline': 'INCIDENT TIMELINE',
        'threats': 'THREAT DETECTIONS & TRIAGE',
        'knowledge': 'CYBERSECURITY KNOWLEDGE BASE',
        'reports': 'FORENSIC PDF REPORTS',
        'settings': 'SYSTEM HEALTH & TELEMETRY'
    };

    const breadcrumbs = {
        'overview': 'Overview',
        'cases': 'Cases',
        'evidence': 'Evidence',
        'ai-assistant': 'AI Assistant',
        'logs': 'Log Analyzer',
        'ip': 'IP Intelligence',
        'timeline': 'Timeline',
        'threats': 'Threats',
        'knowledge': 'Knowledge Base',
        'reports': 'Reports',
        'settings': 'Settings'
    };

    document.getElementById('header-active-page').innerText = pageTitles[viewName] || 'CYBERTRACE AI';
    document.getElementById('header-breadcrumb').innerText = breadcrumbs[viewName] || viewName;

    // Load data for active view
    loadViewData(viewName);
};

function closeDrawer() {
    document.getElementById('forensic-drawer').classList.add('hidden');
}

// ── Data Loaders by View ──
function loadViewData(viewName) {
    switch (viewName) {
        case 'overview':
            loadOverview();
            break;
        case 'cases':
            loadCases();
            break;
        case 'evidence':
            loadEvidence();
            break;
        case 'ai-assistant':
            loadChatHistory();
            break;
        case 'timeline':
            loadTimeline();
            break;
        case 'threats':
            loadThreats();
            break;
        case 'knowledge':
            loadKnowledgeDocs();
            break;
        case 'reports':
            loadReports();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// ── 1. Overview / Dashboard ──
async function loadOverview() {
    try {
        const [overview, analytics, recent] = await Promise.all([
            CyberTraceAPI.getDashboardOverview(),
            CyberTraceAPI.getDashboardAnalytics(),
            CyberTraceAPI.getRecentActivity()
        ]);

        // Metrics
        document.getElementById('metric-total-cases').innerText = overview.total_cases;
        document.getElementById('metric-cases-today').innerText = `+${overview.cases_today} TODAY`;
        document.getElementById('metric-active-cases').innerText = `${overview.active_cases} active records`;

        document.getElementById('metric-total-evidence').innerText = overview.total_evidence;
        document.getElementById('metric-indexed-evidence').innerText = `${overview.indexed_evidence} indexed for RAG`;

        document.getElementById('metric-threat-count').innerText = overview.threat_indicators;
        document.getElementById('metric-active-threats').innerText = `${overview.active_threats} high priority`;

        document.getElementById('metric-integrity-pct').innerText = `${overview.integrity_percent}%`;

        // Threat Distribution Bars
        const distContainer = document.getElementById('threat-distribution-bars');
        if (distContainer) {
            if (analytics.threat_distribution && analytics.threat_distribution.length > 0) {
                distContainer.innerHTML = analytics.threat_distribution.map(item => `
                    <div class="flex flex-col gap-1">
                      <div class="flex justify-between items-center font-code-sm text-xs">
                        <span class="text-on-surface font-medium flex items-center gap-1.5">
                          <span class="w-1.5 h-1.5" style="background-color: ${item.color}"></span>
                          ${item.category}
                        </span>
                        <span class="font-semibold" style="color: ${item.color}">${item.percentage}%</span>
                      </div>
                      <div class="w-full h-1.5 bg-surface-container-high overflow-hidden">
                        <div class="h-full" style="width: ${item.percentage}%; background-color: ${item.color}"></div>
                      </div>
                    </div>
                `).join('');
                document.getElementById('threat-dist-count').innerText = `N=${analytics.total_threats_logged} LOGGED`;
            } else {
                distContainer.innerHTML = '<div class="text-xs text-outline py-2">No active threat distributions.</div>';
            }
        }

        // Recent Cases List
        const recentCasesEl = document.getElementById('dashboard-recent-cases');
        if (recentCasesEl && recent.recent_cases) {
            recentCasesEl.innerHTML = recent.recent_cases.map(c => `
                <div class="p-2.5 bg-surface-container hover:bg-surface-container-high transition-colors cursor-pointer border border-white/5 flex items-center justify-between" onclick="selectCase('${c.id}', '${c.case_number}')">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="font-code-sm text-xs px-1.5 py-0.5 bg-surface-container-highest text-primary font-bold shrink-0">${c.case_number}</span>
                    <span class="font-medium text-xs text-on-surface truncate">${c.title}</span>
                  </div>
                  <span class="font-label-caps text-[9px] px-1.5 py-0.5 ${c.priority === 'CRITICAL' ? 'bg-error-container text-on-error-container' : 'bg-surface-container-highest text-primary'} uppercase shrink-0 font-bold">
                    ${c.priority}
                  </span>
                </div>
            `).join('');
        }

        // Recent Event Feed
        const recentEventsEl = document.getElementById('dashboard-recent-events');
        if (recentEventsEl && recent.recent_events) {
            recentEventsEl.innerHTML = recent.recent_events.map(ev => `
                <div class="flex flex-col gap-0.5 border-b border-white/5 pb-1 last:border-b-0">
                  <div class="flex items-center justify-between text-[10px]">
                    <span class="text-outline font-mono">[${ev.timestamp}]</span>
                    <span class="font-label-caps text-[9px] px-1 py-0.2 ${ev.severity === 'CRITICAL' || ev.severity === 'HIGH' ? 'bg-error/20 text-error' : 'bg-surface-container text-outline'} uppercase font-bold">
                      ${ev.severity}
                    </span>
                  </div>
                  <div class="text-on-surface-variant text-[11px] truncate">
                    ${ev.source_ip ? `<span class="text-primary font-mono">${ev.source_ip}</span> > ` : ''}${ev.description}
                  </div>
                </div>
            `).join('');
        }

    } catch (err) {
        console.error("Dashboard overview failed:", err);
    }
}

// ── 2. Case Management ──
let currentCaseFilter = 'ALL';

window.setCaseFilter = function(filter, btn) {
    currentCaseFilter = filter;
    document.querySelectorAll('.case-pill').forEach(b => {
        b.className = 'case-pill px-3 py-1 bg-surface-container-high text-on-surface-variant font-label-caps text-[10px] rounded-full';
    });
    btn.className = 'case-pill px-3 py-1 bg-primary text-on-primary font-label-caps text-[10px] rounded-full font-bold';
    loadCases();
};

async function loadCases() {
    const container = document.getElementById('cases-list-container');
    const searchVal = document.getElementById('cases-search-input')?.value || '';

    const params = {};
    if (searchVal) params.search = searchVal;
    if (currentCaseFilter !== 'ALL') {
        if (['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].includes(currentCaseFilter)) {
            params.priority = currentCaseFilter;
        } else {
            params.status = currentCaseFilter;
        }
    }

    try {
        const res = await CyberTraceAPI.getCases(params);
        casesCache = res.items || [];

        if (casesCache.length === 0) {
            container.innerHTML = '<div class="text-xs text-outline py-8 text-center bg-surface-container-lowest p-4">No investigation cases match the selected criteria.</div>';
            return;
        }

        // Set default active case if none chosen
        if (!activeCase && casesCache.length > 0) {
            activeCase = casesCache[0];
            updateActiveCaseUI();
        }

        container.innerHTML = casesCache.map(c => `
            <div class="bg-surface-container border border-white/5 p-3 flex flex-col gap-2 hover:bg-surface-container-high transition-colors">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="font-code-sm text-xs px-2 py-0.5 bg-surface-container-highest text-primary font-bold">${c.case_number}</span>
                  <span class="font-label-caps text-[10px] px-1.5 py-0.5 bg-surface-container-lowest text-outline">${c.category}</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <span class="font-label-caps text-[9px] px-2 py-0.5 ${c.priority === 'CRITICAL' ? 'bg-error-container text-on-error-container' : 'bg-surface-container-highest text-primary'} font-bold">
                    ${c.priority}
                  </span>
                  <span class="font-label-caps text-[9px] px-2 py-0.5 bg-surface-container text-secondary font-bold">
                    ${c.status}
                  </span>
                </div>
              </div>
              <div class="flex flex-col">
                <span class="font-medium text-sm text-on-surface">${c.title}</span>
                <span class="text-xs text-on-surface-variant line-clamp-2 mt-0.5">${c.description || 'No description provided.'}</span>
              </div>
              <div class="flex items-center justify-between pt-2 border-t border-white/5 font-code-sm text-[11px] text-outline">
                <span>Created: ${new Date(c.created_at).toLocaleDateString()}</span>
                <div class="flex items-center gap-2">
                  <button class="px-2.5 py-1 bg-surface-container-lowest text-primary hover:text-white transition-colors" onclick="selectCase('${c.id}', '${c.case_number}')">
                    SELECT AS ACTIVE
                  </button>
                  <button class="px-2.5 py-1 bg-surface-container-highest text-on-surface hover:text-white" onclick="switchView('ai-assistant'); selectCase('${c.id}', '${c.case_number}')">
                    INVESTIGATE AI
                  </button>
                </div>
              </div>
            </div>
        `).join('');

    } catch (err) {
        container.innerHTML = `<div class="text-xs text-error py-4 text-center">Failed to load cases: ${err.message}</div>`;
    }
}

window.openNewCaseModal = function() {
    document.getElementById('new-case-modal').classList.remove('hidden');
};

window.handleCreateCase = async function(e) {
    e.preventDefault();
    const title = document.getElementById('new-case-title').value.trim();
    const category = document.getElementById('new-case-category').value;
    const priority = document.getElementById('new-case-priority').value;
    const description = document.getElementById('new-case-desc').value.trim();

    try {
        const newCase = await CyberTraceAPI.createCase({ title, category, priority, description });
        showToast(`Case ${newCase.case_number} created successfully`, 'success');
        document.getElementById('new-case-modal').classList.add('hidden');
        document.getElementById('new-case-title').value = '';
        document.getElementById('new-case-desc').value = '';
        activeCase = newCase;
        updateActiveCaseUI();
        loadCases();
    } catch (err) {
        showToast(`Failed to create case: ${err.message}`, 'error');
    }
};

window.selectCase = function(caseId, caseNumber) {
    const found = casesCache.find(c => c.id === caseId);
    if (found) {
        activeCase = found;
    } else {
        activeCase = { id: caseId, case_number: caseNumber, title: caseNumber };
    }
    updateActiveCaseUI();
    showToast(`Active investigation dossier switched to ${caseNumber}`, 'info');
};

function updateActiveCaseUI() {
    if (!activeCase) return;
    document.getElementById('active-case-badge').innerText = activeCase.case_number;
    const input = document.getElementById('rag-query-input');
    if (input) {
        input.placeholder = `Ask CyberTrace about evidence in ${activeCase.case_number}...`;
    }
    const reportScope = document.getElementById('reports-scope-label');
    if (reportScope) {
        reportScope.innerText = activeCase.case_number;
    }
}

// ── 3. Evidence Vault ──
async function loadEvidence() {
    const container = document.getElementById('evidence-list-container');
    try {
        const res = await CyberTraceAPI.getEvidence();
        evidenceCache = res.items || [];

        if (evidenceCache.length === 0) {
            container.innerHTML = '<div class="text-xs text-outline py-8 text-center bg-surface-container-lowest p-4">No evidence files uploaded yet. Ingest forensic artifacts using the dropzone above.</div>';
            return;
        }

        renderEvidenceList(evidenceCache);
    } catch (err) {
        container.innerHTML = `<div class="text-xs text-error py-4 text-center">Failed to load evidence: ${err.message}</div>`;
    }
}

function renderEvidenceList(items) {
    const container = document.getElementById('evidence-list-container');
    container.innerHTML = items.map(ev => `
        <div class="bg-surface-container-low border border-white/5 p-3.5 space-y-2.5">
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-8 h-8 bg-primary/10 flex items-center justify-center text-primary shrink-0">
                <span class="material-symbols-outlined text-[18px]">terminal</span>
              </div>
              <div class="flex flex-col min-w-0">
                <div class="flex items-center gap-2">
                  <span class="font-code-md text-xs font-bold text-on-surface truncate">${ev.original_filename}</span>
                  <span class="px-1.5 py-0.2 bg-surface-container-highest text-primary font-label-caps text-[9px]">${ev.evidence_number}</span>
                </div>
                <span class="font-label-caps text-[10px] text-on-surface-variant">${(ev.file_size / 1024).toFixed(1)} KB • ${ev.file_type ? ev.file_type.toUpperCase() : 'RAW'}</span>
              </div>
            </div>
            <span class="font-label-caps text-[9px] px-2 py-0.5 bg-surface-container text-secondary font-bold flex items-center gap-1 shrink-0">
              <span class="w-1.5 h-1.5 rounded-full bg-secondary"></span>
              ${ev.integrity_status}
            </span>
          </div>

          <!-- Hash Row with Copy -->
          <div class="flex items-center justify-between bg-surface-container p-2 gap-2 text-xs font-mono">
            <div class="flex items-center gap-1.5 min-w-0 truncate">
              <span class="font-label-caps text-[9px] text-outline shrink-0">SHA256:</span>
              <span class="text-on-surface truncate">${ev.sha256_hash || 'PENDING'}</span>
            </div>
            <button class="p-1 hover:text-primary transition-colors text-outline shrink-0" onclick="navigator.clipboard.writeText('${ev.sha256_hash}'); showToast('SHA-256 hash copied to clipboard', 'success');" title="Copy SHA-256">
              <span class="material-symbols-outlined text-[16px]">content_copy</span>
            </button>
          </div>

          <div class="flex items-center justify-between text-[11px] font-code-sm text-outline">
            <span>Uploaded: ${new Date(ev.upload_timestamp).toLocaleString()}</span>
            <span class="text-secondary font-medium">${ev.chunk_count} RAG chunks</span>
          </div>

          <div class="grid grid-cols-3 gap-1.5 pt-1">
            <button class="py-1.5 px-2 bg-surface-container hover:bg-surface-container-high text-on-surface font-label-caps text-[10px] flex items-center justify-center gap-1 transition-colors" onclick="inspectEvidence('${ev.id}')">
              <span class="material-symbols-outlined text-[14px]">preview</span>
              <span>INSPECT</span>
            </button>
            <button class="py-1.5 px-2 bg-surface-container hover:bg-surface-container-high text-on-surface font-label-caps text-[10px] flex items-center justify-center gap-1 transition-colors" onclick="verifyHashAction('${ev.id}')">
              <span class="material-symbols-outlined text-[14px] text-secondary">verified</span>
              <span>VERIFY HASH</span>
            </button>
            <button class="py-1.5 px-2 bg-surface-container hover:bg-surface-container-high text-on-surface font-label-caps text-[10px] flex items-center justify-center gap-1 transition-colors" onclick="inspectEvidence('${ev.id}')">
              <span class="material-symbols-outlined text-[14px] text-primary">history_edu</span>
              <span>CUSTODY</span>
            </button>
          </div>
        </div>
    `).join('');
}

window.filterEvidenceList = function(q) {
    const val = q.toLowerCase().trim();
    if (!val) {
        renderEvidenceList(evidenceCache);
        return;
    }
    const filtered = evidenceCache.filter(e =>
        e.original_filename.toLowerCase().includes(val) ||
        e.evidence_number.toLowerCase().includes(val) ||
        (e.sha256_hash && e.sha256_hash.toLowerCase().includes(val))
    );
    renderEvidenceList(filtered);
};

window.handleEvidenceUpload = async function(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!activeCase) {
        showToast("Please select or create an investigation case first.", "error");
        return;
    }

    showToast(`Uploading ${file.name} to vault & sealing SHA-256...`, "info");
    try {
        const ev = await CyberTraceAPI.uploadEvidence(activeCase.id, file);
        showToast(`Evidence ${ev.evidence_number} acquired & indexed!`, "success");
        event.target.value = '';
        loadEvidence();
    } catch (err) {
        showToast(`Upload failed: ${err.message}`, "error");
    }
};

window.verifyHashAction = async function(evidenceId) {
    try {
        const res = await CyberTraceAPI.verifyHash(evidenceId);
        if (res.match) {
            showToast("SHA-256 integrity verified: ZERO DRIFT (Bit-for-bit intact)", "success");
        } else {
            showToast("WARNING: Integrity mismatch detected!", "error");
        }
    } catch (err) {
        showToast(`Verification failed: ${err.message}`, "error");
    }
};

window.inspectEvidence = async function(evidenceId) {
    try {
        const [detail, custody] = await Promise.all([
            CyberTraceAPI.getEvidenceDetail(evidenceId),
            CyberTraceAPI.getCustody(evidenceId)
        ]);

        document.getElementById('drawer-file-name').innerText = detail.original_filename;
        document.getElementById('drawer-artifact-id').innerText = detail.evidence_number;
        document.getElementById('drawer-bytes').innerText = `${detail.file_size} bytes`;
        document.getElementById('drawer-mime').innerText = detail.file_type || 'raw';
        document.getElementById('drawer-sha256').innerText = detail.sha256_hash || 'N/A';
        document.getElementById('drawer-integrity-badge').innerText = detail.integrity_status;

        const custodyEl = document.getElementById('drawer-custody-records');
        if (custody && custody.length > 0) {
            custodyEl.innerHTML = custody.map(c => `
                <div class="flex items-start gap-2 border-l-2 border-secondary pl-2 py-1 text-xs">
                  <div class="flex flex-col">
                    <span class="font-bold text-on-surface">${c.action}</span>
                    <span class="text-outline text-[10px]">${new Date(c.timestamp).toLocaleString()} • ${c.performed_by_name || 'System'}</span>
                    <span class="text-on-surface-variant text-[11px] mt-0.5">${c.details || ''}</span>
                  </div>
                </div>
            `).join('');
        } else {
            custodyEl.innerHTML = '<div class="text-xs text-outline">No chain of custody logs found.</div>';
        }

        document.getElementById('evidence-drawer').classList.remove('hidden');
    } catch (err) {
        showToast(`Inspect error: ${err.message}`, "error");
    }
};

window.copyDrawerHash = function() {
    const h = document.getElementById('drawer-sha256').innerText;
    navigator.clipboard.writeText(h);
    showToast("SHA-256 copied to clipboard", "success");
};

// ── 4. AI Investigation (RAG Chat) ──
window.setChatPrompt = function(promptText) {
    const input = document.getElementById('rag-query-input');
    if (input) {
        input.value = promptText;
        input.focus();
    }
};

async function loadChatHistory() {
    if (!activeCase) return;
    try {
        const history = await CyberTraceAPI.getChatHistory(activeCase.id);
        const container = document.getElementById('chat-messages-container');
        if (!history || history.length === 0) return;

        container.innerHTML = history.map(item => `
            <!-- User Inquiry -->
            <div class="flex flex-col items-end gap-1 pl-6">
              <div class="bg-surface-container-high p-3 text-on-surface w-full max-w-xl">
                <div class="flex items-center justify-between pb-1 border-b border-white/5 text-[10px] font-label-caps text-primary">
                  <span>LEAD FORENSIC INVESTIGATOR</span>
                  <span class="text-outline">${new Date(item.created_at).toLocaleTimeString()}</span>
                </div>
                <p class="text-[13px] pt-1.5">${item.question}</p>
              </div>
            </div>

            <!-- Grounded AI Response -->
            <div class="flex flex-col gap-2">
              <div class="bg-surface-container-low border border-white/10 p-4 shadow-xl flex flex-col gap-3 relative overflow-hidden">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-primary-container to-secondary"></div>
                <div class="flex items-center justify-between pb-2 border-b border-white/10">
                  <div class="flex items-center gap-2">
                    <span class="w-6 h-6 bg-primary-container flex items-center justify-center text-on-primary font-bold">
                      <span class="material-symbols-outlined text-[16px]">smart_toy</span>
                    </span>
                    <span class="font-label-caps text-[11px] text-primary uppercase font-bold">CYBERTRACE INTELLIGENCE</span>
                  </div>
                  <span class="font-label-caps text-[9px] px-2 py-0.5 bg-secondary/20 text-secondary font-bold">VERIFIED RAG</span>
                </div>
                <div class="text-[13.5px] leading-relaxed text-on-surface whitespace-pre-wrap">${item.answer}</div>
                ${item.sources && item.sources.length > 0 ? `
                  <div class="border-t border-white/5 pt-2 flex flex-col gap-1.5">
                    <span class="font-label-caps text-[10px] text-outline uppercase font-bold">RETRIEVED FORENSIC CITATIONS:</span>
                    <div class="flex flex-wrap gap-1.5">
                      ${item.sources.map(s => `
                        <span class="px-2 py-1 bg-surface-container text-primary font-code-sm text-[11px] border border-white/5">
                          [${s.document_name}${s.line_start ? `:${s.line_start}` : ''}]
                        </span>
                      `).join('')}
                    </div>
                  </div>
                ` : ''}
              </div>
            </div>
        `).join('');

    } catch (err) {
        console.error("Load chat history error:", err);
    }
}

window.dispatchRAGQuery = async function() {
    const input = document.getElementById('rag-query-input');
    if (!input || !input.value.trim()) return;

    if (!activeCase) {
        showToast("Please select a case to scope the investigation.", "error");
        return;
    }

    const question = input.value.trim();
    input.value = '';
    const container = document.getElementById('chat-messages-container');

    // Append User message immediately
    const userBubble = document.createElement('div');
    userBubble.className = 'flex flex-col items-end gap-1 pl-6';
    userBubble.innerHTML = `
        <div class="bg-surface-container-high p-3 text-on-surface w-full max-w-xl">
          <div class="flex items-center justify-between pb-1 border-b border-white/5 text-[10px] font-label-caps text-primary">
            <span>LEAD FORENSIC INVESTIGATOR</span>
            <span class="text-outline">NOW</span>
          </div>
          <p class="text-[13px] pt-1.5">${question}</p>
        </div>
    `;
    container.appendChild(userBubble);

    // Append Loading Assistant Card
    const loadingCard = document.createElement('div');
    loadingCard.className = 'flex flex-col gap-2';
    loadingCard.innerHTML = `
        <div class="bg-surface-container-low border border-white/10 p-4 shadow-xl flex flex-col gap-2 relative">
          <div class="flex items-center gap-2 text-primary text-xs font-code-sm">
            <span class="material-symbols-outlined text-[18px] animate-spin">sync</span>
            <span>Searching vector embeddings across ${activeCase.case_number} evidence...</span>
          </div>
        </div>
    `;
    container.appendChild(loadingCard);
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });

    try {
        const res = await CyberTraceAPI.chatRAG(activeCase.id, question);
        loadingCard.innerHTML = `
            <div class="bg-surface-container-low border border-white/10 p-4 shadow-xl flex flex-col gap-3 relative overflow-hidden">
              <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-primary-container to-secondary"></div>
              <div class="flex items-center justify-between pb-2 border-b border-white/10">
                <div class="flex items-center gap-2">
                  <span class="w-6 h-6 bg-primary-container flex items-center justify-center text-on-primary font-bold">
                    <span class="material-symbols-outlined text-[16px]">smart_toy</span>
                  </span>
                  <span class="font-label-caps text-[11px] text-primary uppercase font-bold">CYBERTRACE INTELLIGENCE</span>
                </div>
                <span class="font-label-caps text-[9px] px-2 py-0.5 bg-secondary/20 text-secondary font-bold">VERIFIED RAG</span>
              </div>
              <div class="text-[13.5px] leading-relaxed text-on-surface whitespace-pre-wrap">${res.answer}</div>
              ${res.findings && res.findings.length > 0 ? `
                <div class="flex flex-col gap-2 pt-2 border-t border-white/5">
                  <span class="font-label-caps text-[10px] text-outline uppercase font-bold">STRUCTURED FINDINGS:</span>
                  ${res.findings.map(f => `
                    <div class="p-2.5 bg-surface-container border border-white/5 flex flex-col gap-1">
                      <div class="flex justify-between items-center">
                        <span class="font-code-sm text-xs font-bold text-on-surface">${f.title}</span>
                        <span class="font-label-caps text-[9px] px-1.5 py-0.2 ${f.severity === 'CRITICAL' || f.severity === 'HIGH' ? 'bg-error-container text-on-error-container' : 'bg-surface-container-highest text-primary'} font-bold">
                          ${f.severity}
                        </span>
                      </div>
                      <p class="text-xs text-on-surface-variant">${f.description}</p>
                    </div>
                  `).join('')}
                </div>
              ` : ''}
              ${res.sources && res.sources.length > 0 ? `
                <div class="border-t border-white/5 pt-2 flex flex-col gap-1.5">
                  <span class="font-label-caps text-[10px] text-outline uppercase font-bold">RETRIEVED FORENSIC CITATIONS:</span>
                  <div class="flex flex-wrap gap-1.5">
                    ${res.sources.map(s => `
                      <span class="px-2 py-1 bg-surface-container text-primary font-code-sm text-[11px] border border-white/5">
                        [${s.document_name}${s.line_start ? `:${s.line_start}` : ''} | Score: ${s.relevance_score.toFixed(2)}]
                      </span>
                    `).join('')}
                  </div>
                </div>
              ` : ''}
            </div>
        `;
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    } catch (err) {
        loadingCard.innerHTML = `
            <div class="bg-surface-container-low border border-error/40 p-4 flex flex-col gap-1.5 text-xs">
              <span class="font-bold text-error">AI Co-Processor Notice</span>
              <span class="text-on-surface-variant">${err.message}</span>
            </div>
        `;
    }
};

// ── 5. Log Analyzer ──
window.handleLogUpload = async function(e) {
    const file = e.target.files[0];
    if (!file) return;

    showToast(`Analyzing ${file.name}...`, "info");
    try {
        const caseId = activeCase ? activeCase.id : '';
        const res = await CyberTraceAPI.analyzeLog(file, caseId);
        renderLogAnalysis(res);
        showToast(`Log analysis complete: ${res.parsed_events} events parsed`, "success");
    } catch (err) {
        showToast(`Analysis failed: ${err.message}`, "error");
    }
};

window.loadSampleLogAnalysis = async function() {
    showToast("Analyzing demonstration auth_server.log...", "info");
    const sampleLog = `2026-11-18T22:14:01Z auth.warn sshd Failed password for root from 192.0.2.45
2026-11-18T22:14:05Z auth.warn sshd Failed password for root from 192.0.2.45
2026-11-18T22:14:09Z auth.warn sshd Failed password for admin from 192.0.2.45
2026-11-18T22:14:14Z auth.warn sshd Failed password for admin from 192.0.2.45
2026-11-18T22:14:18Z auth.warn sshd Failed password for deploy from 192.0.2.45
2026-11-18T22:14:23Z auth.warn sshd Failed password for srv_backup from 192.0.2.45
2026-11-18T22:18:09Z auth.info sshd Accepted password for srv_backup from 192.0.2.45
2026-11-18T22:18:10Z audit sudo srv_backup TTY=pts/2 COMMAND=/bin/bash
2026-11-18T22:19:45Z audit sudo admin TTY=pts/2 COMMAND=/bin/cat /etc/shadow`;

    const blob = new Blob([sampleLog], { type: 'text/plain' });
    const file = new File([blob], 'auth_server_sample.log');
    const caseId = activeCase ? activeCase.id : '';
    const res = await CyberTraceAPI.analyzeLog(file, caseId);
    renderLogAnalysis(res);
    showToast("Demonstration log analyzed with real rule engines!", "success");
};

function renderLogAnalysis(res) {
    const container = document.getElementById('log-results-container');
    container.innerHTML = `
        <div class="bg-surface-container-low border border-white/10 p-4 space-y-3">
          <div class="flex items-center justify-between border-b border-white/10 pb-2">
            <div>
              <span class="font-code-md text-xs font-bold text-on-surface">${res.file_name}</span>
              <span class="text-outline text-[11px] block">${res.summary}</span>
            </div>
            <span class="font-code-sm text-xs text-secondary font-bold">${res.parsed_events} EVENTS PARSED</span>
          </div>

          <div class="flex flex-col gap-2">
            <span class="font-label-caps text-[10px] text-outline uppercase font-bold">ANOMALIES & THREAT INDICATORS:</span>
            ${res.findings && res.findings.length > 0 ? res.findings.map(f => `
              <div class="p-3 bg-surface-container border border-white/5 flex flex-col gap-1.5">
                <div class="flex justify-between items-center">
                  <span class="font-code-sm text-xs font-bold text-on-surface">${f.category}</span>
                  <span class="font-label-caps text-[9px] px-2 py-0.5 ${f.severity === 'HIGH' || f.severity === 'CRITICAL' ? 'bg-error-container text-on-error-container' : 'bg-surface-container-highest text-primary'} font-bold">
                    ${f.severity}
                  </span>
                </div>
                <p class="text-xs text-on-surface-variant">${f.description}</p>
                ${f.source_ip ? `<div class="font-code-sm text-[11px] text-primary">Source IP: ${f.source_ip}</div>` : ''}
                ${f.evidence_lines && f.evidence_lines.length > 0 ? `
                  <div class="bg-surface-container-lowest p-2 font-mono text-[10px] text-outline space-y-1">
                    ${f.evidence_lines.slice(0, 3).map(l => `<div class="truncate">> ${l}</div>`).join('')}
                  </div>
                ` : ''}
              </div>
            `).join('') : '<div class="text-xs text-secondary py-2">No malicious patterns or anomalies flagged.</div>'}
          </div>
        </div>
    `;
}

// ── 6. IP Intelligence ──
window.executeIPLookup = async function() {
    const input = document.getElementById('ip-lookup-input');
    const ip = input?.value.trim();
    if (!ip) return;

    const container = document.getElementById('ip-results-container');
    container.innerHTML = '<div class="text-xs text-outline py-4 text-center">Querying forensic records...</div>';

    try {
        const caseId = activeCase ? activeCase.id : '';
        const res = await CyberTraceAPI.analyzeIP(ip, caseId);

        container.innerHTML = `
            <div class="bg-surface-container-low border border-white/10 p-4 space-y-3">
              <div class="flex items-center justify-between border-b border-white/10 pb-2">
                <div class="flex items-center gap-2">
                  <span class="font-code-md text-sm font-bold text-primary">${res.ip_address}</span>
                  <span class="font-label-caps text-[10px] px-1.5 py-0.2 bg-surface-container-highest text-outline">IPv${res.ip_version || 4}</span>
                </div>
                <span class="font-code-sm text-xs text-secondary font-bold">${res.total_events} RECORDED EVENTS</span>
              </div>

              <div class="grid grid-cols-2 gap-2 text-xs font-code-sm">
                <div class="p-2 bg-surface-container border border-white/5">
                  <span class="text-outline text-[10px] block">FIRST OBSERVED</span>
                  <span class="text-on-surface">${res.first_seen ? new Date(res.first_seen).toLocaleString() : 'N/A'}</span>
                </div>
                <div class="p-2 bg-surface-container border border-white/5">
                  <span class="text-outline text-[10px] block">LAST OBSERVED</span>
                  <span class="text-on-surface">${res.last_seen ? new Date(res.last_seen).toLocaleString() : 'N/A'}</span>
                </div>
              </div>

              <div class="space-y-1">
                <span class="font-label-caps text-[10px] text-outline uppercase font-bold">AUTHENTICATED USERNAMES:</span>
                <div class="flex flex-wrap gap-1">
                  ${res.associated_users.length > 0 ? res.associated_users.map(u => `
                    <span class="px-2 py-0.5 bg-surface-container text-on-surface font-code-sm text-xs">${u}</span>
                  `).join('') : '<span class="text-xs text-outline">None recorded</span>'}
                </div>
              </div>

              <div class="space-y-1">
                <span class="font-label-caps text-[10px] text-outline uppercase font-bold">CROSS-CASE CITATIONS:</span>
                <div class="flex flex-wrap gap-1">
                  ${res.related_cases.length > 0 ? res.related_cases.map(c => `
                    <span class="px-2 py-0.5 bg-surface-container-highest text-primary font-code-sm text-xs">${c}</span>
                  `).join('') : '<span class="text-xs text-outline">No cross-case linkages</span>'}
                </div>
              </div>

              <p class="text-[11px] text-outline font-label-caps pt-1">${res.note}</p>
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<div class="text-xs text-error py-4">IP profiling failed: ${err.message}</div>`;
    }
};

// ── 7. Timeline ──
async function loadTimeline() {
    const container = document.getElementById('timeline-events-container');
    if (!activeCase) {
        container.innerHTML = '<div class="text-xs text-outline py-6 text-center">Select an investigation case to reconstruct chronological event timelines.</div>';
        return;
    }

    try {
        const res = await CyberTraceAPI.getTimeline(activeCase.id);
        if (!res.events || res.events.length === 0) {
            container.innerHTML = `<div class="text-xs text-outline py-6 text-center">No timeline events recorded for ${activeCase.case_number}.</div>`;
            return;
        }

        container.innerHTML = res.events.map(ev => `
            <div class="p-3 bg-surface-container-low border-l-2 ${ev.severity === 'CRITICAL' ? 'border-error' : (ev.severity === 'HIGH' ? 'border-primary' : 'border-outline')} flex items-start justify-between gap-3">
              <div class="flex flex-col gap-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="font-mono text-xs text-primary font-bold">[${new Date(ev.timestamp).toLocaleTimeString()}]</span>
                  <span class="font-code-sm text-xs font-semibold text-on-surface">${ev.event_type}</span>
                </div>
                <span class="text-xs text-on-surface-variant">${ev.description}</span>
                <div class="flex items-center gap-2 text-[10px] font-code-sm text-outline pt-0.5">
                  ${ev.source_ip ? `<span>IP: ${ev.source_ip}</span> • ` : ''}
                  ${ev.username ? `<span>User: ${ev.username}</span> • ` : ''}
                  <span>Ref: ${ev.source_reference || 'Forensic Log'}</span>
                </div>
              </div>
              <span class="font-label-caps text-[9px] px-1.5 py-0.5 ${ev.severity === 'CRITICAL' ? 'bg-error-container text-on-error-container' : 'bg-surface-container text-outline'} uppercase font-bold shrink-0">
                ${ev.severity}
              </span>
            </div>
        `).join('');

    } catch (err) {
        container.innerHTML = `<div class="text-xs text-error py-4">Timeline load failed: ${err.message}</div>`;
    }
}

// ── 8. Threat Detection ──
async function loadThreats() {
    const container = document.getElementById('threats-list-container');
    try {
        const caseId = activeCase ? activeCase.id : '';
        const items = await CyberTraceAPI.getThreats({ case_id: caseId });

        if (!items || items.length === 0) {
            container.innerHTML = '<div class="text-xs text-outline py-8 text-center bg-surface-container-lowest p-4">No threat detections logged for this case.</div>';
            return;
        }

        container.innerHTML = items.map(t => `
            <div class="bg-surface-container-low border border-white/5 p-3.5 space-y-2">
              <div class="flex items-center justify-between">
                <span class="font-code-md text-xs font-bold text-on-surface">${t.category}</span>
                <div class="flex items-center gap-1.5">
                  <span class="font-label-caps text-[9px] px-2 py-0.5 ${t.severity === 'CRITICAL' ? 'bg-error-container text-on-error-container' : 'bg-surface-container-highest text-primary'} font-bold">
                    ${t.severity}
                  </span>
                  <span class="font-label-caps text-[9px] px-2 py-0.5 bg-surface-container text-secondary font-bold">
                    ${t.status}
                  </span>
                </div>
              </div>
              <p class="text-xs text-on-surface-variant leading-relaxed">${t.description}</p>
              <div class="flex items-center justify-between pt-1 border-t border-white/5 font-code-sm text-[11px] text-outline">
                <span>Method: ${t.detection_source} • Conf: ${(t.confidence * 100).toFixed(0)}%</span>
                <button class="px-2 py-0.5 bg-surface-container text-primary hover:text-white" onclick="triageThreat('${t.id}')">
                  TRIAGE
                </button>
              </div>
            </div>
        `).join('');

    } catch (err) {
        container.innerHTML = `<div class="text-xs text-error py-4">Threats load failed: ${err.message}</div>`;
    }
}

window.triageThreat = async function(threatId) {
    try {
        await CyberTraceAPI.updateThreatStatus(threatId, 'INVESTIGATING');
        showToast("Threat marked as INVESTIGATING", "info");
        loadThreats();
    } catch (err) {
        showToast(`Triage error: ${err.message}`, "error");
    }
};

// ── 9. Knowledge Base ──
async function loadKnowledgeDocs() {
    const container = document.getElementById('knowledge-docs-container');
    try {
        const docs = await CyberTraceAPI.getKnowledgeDocs();
        if (!docs || docs.length === 0) {
            container.innerHTML = '<div class="text-xs text-outline py-6 text-center">No reference knowledge documents uploaded. Ingest NIST or MITRE documents above.</div>';
            return;
        }

        container.innerHTML = docs.map(d => `
            <div class="p-3 bg-surface-container-low border border-white/5 flex items-center justify-between">
              <div class="flex items-center gap-2.5 min-w-0">
                <span class="material-symbols-outlined text-primary text-[18px]">menu_book</span>
                <div class="flex flex-col min-w-0">
                  <span class="font-code-sm text-xs font-semibold text-on-surface truncate">${d.document_name}</span>
                  <span class="text-[10px] text-outline font-label-caps">${d.chunk_count} CHUNKS INDEXED IN CHROMA</span>
                </div>
              </div>
              <span class="font-label-caps text-[9px] px-2 py-0.5 bg-secondary/20 text-secondary font-bold">
                ${d.indexing_status}
              </span>
            </div>
        `).join('');

    } catch (err) {
        container.innerHTML = `<div class="text-xs text-error py-4">Knowledge load failed: ${err.message}</div>`;
    }
}

window.handleKnowledgeUpload = async function(e) {
    const file = e.target.files[0];
    if (!file) return;

    showToast(`Ingesting ${file.name} into knowledge vector store...`, "info");
    try {
        const res = await CyberTraceAPI.uploadKnowledge(file);
        showToast(res.message, "success");
        e.target.value = '';
        loadKnowledgeDocs();
    } catch (err) {
        showToast(`Ingestion failed: ${err.message}`, "error");
    }
};

window.searchKnowledgeBase = async function() {
    const input = document.getElementById('kb-search-input');
    const q = input?.value.trim();
    if (!q) return;

    showToast(`Searching knowledge vectors for "${q}"...`, "info");
    try {
        const res = await CyberTraceAPI.searchKnowledge(q);
        const container = document.getElementById('knowledge-docs-container');
        if (!res.results || res.results.length === 0) {
            showToast("No relevant knowledge vectors matched.", "info");
            return;
        }

        container.innerHTML = res.results.map(r => `
            <div class="p-3 bg-surface-container border border-primary/20 space-y-1">
              <div class="flex justify-between items-center text-xs">
                <span class="font-code-sm text-primary font-bold">${r.filename || 'Knowledge Vector'}</span>
                <span class="text-secondary font-mono text-[10px]">Relevance: ${r.similarity.toFixed(3)}</span>
              </div>
              <p class="text-xs text-on-surface-variant font-mono whitespace-pre-wrap">${r.content}</p>
            </div>
        `).join('');

    } catch (err) {
        showToast(`Search failed: ${err.message}`, "error");
    }
};

// ── 10. Reports ──
async function loadReports() {
    const container = document.getElementById('reports-list-container');
    try {
        const caseId = activeCase ? activeCase.id : '';
        const reports = await CyberTraceAPI.getReports(caseId);

        if (!reports || reports.length === 0) {
            container.innerHTML = '<div class="text-xs text-outline py-6 text-center">No reports generated for this dossier yet. Click GENERATE PDF above.</div>';
            return;
        }

        container.innerHTML = reports.map(r => `
            <div class="p-3 bg-surface-container-low border border-white/5 flex items-center justify-between">
              <div class="flex items-center gap-2.5 min-w-0">
                <span class="material-symbols-outlined text-error text-[20px]">picture_as_pdf</span>
                <div class="flex flex-col min-w-0">
                  <span class="font-code-sm text-xs font-semibold text-on-surface truncate">${r.report_title}</span>
                  <span class="text-[10px] text-outline font-mono">${r.report_number} • ${new Date(r.generated_at).toLocaleDateString()}</span>
                </div>
              </div>
              <button class="h-8 px-3 bg-surface-container hover:bg-surface-container-high border border-white/10 text-primary font-code-sm text-xs font-semibold flex items-center gap-1.5" onclick="downloadReport('${r.id}', '${r.report_number}')">
                <span class="material-symbols-outlined text-[16px]">download</span>
                <span>DOWNLOAD</span>
              </button>
            </div>
        `).join('');

    } catch (err) {
        container.innerHTML = `<div class="text-xs text-error py-4">Reports load failed: ${err.message}</div>`;
    }
}

window.generateCaseReport = async function() {
    if (!activeCase) {
        showToast("Please select an active case first.", "error");
        return;
    }

    showToast(`Compiling forensic report for ${activeCase.case_number}...`, "info");
    try {
        const rep = await CyberTraceAPI.generateReport(activeCase.id, `Examination Report: ${activeCase.title}`);
        showToast(`Report ${rep.report_number} generated successfully!`, "success");
        loadReports();
    } catch (err) {
        showToast(`Report generation failed: ${err.message}`, "error");
    }
};

window.triggerQuickReport = function() {
    switchView('reports');
    generateCaseReport();
};

window.downloadReport = async function(reportId, reportNum) {
    showToast(`Downloading ${reportNum}.pdf...`, "info");
    try {
        await CyberTraceAPI.downloadReport(reportId, reportNum);
    } catch (err) {
        showToast(`Download failed: ${err.message}`, "error");
    }
};

// ── 11. Settings & Health ──
async function loadSettings() {
    const container = document.getElementById('settings-details-container');
    try {
        const [settings, health] = await Promise.all([
            CyberTraceAPI.getSettings(),
            CyberTraceAPI.getHealth()
        ]);

        container.innerHTML = `
            <!-- Health Card -->
            <div class="bg-surface-container-lowest border border-white/10 p-4 space-y-3">
              <div class="flex items-center justify-between border-b border-white/10 pb-2">
                <span class="font-code-md text-xs font-bold text-on-surface">SUBSYSTEM STATUS</span>
                <span class="font-label-caps text-[9px] px-2 py-0.5 bg-secondary/20 text-secondary font-bold">
                  ${health.status.toUpperCase()}
                </span>
              </div>
              <div class="space-y-1.5 font-code-sm text-xs">
                <div class="flex justify-between">
                  <span class="text-outline">Database:</span>
                  <span class="text-on-surface">${health.database}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-outline">Vector DB:</span>
                  <span class="text-on-surface">${health.vector_database.status}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-outline">AI Provider:</span>
                  <span class="text-on-surface">${health.ai_provider.status}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-outline">Storage Directories:</span>
                  <span class="text-secondary">${health.storage.status}</span>
                </div>
              </div>
            </div>

            <!-- Parameters Card -->
            <div class="bg-surface-container-lowest border border-white/10 p-4 space-y-3">
              <div class="flex items-center justify-between border-b border-white/10 pb-2">
                <span class="font-code-md text-xs font-bold text-on-surface">FORENSIC ENGINE PARAMS</span>
                <span class="font-code-sm text-xs text-primary font-bold">v${settings.version}</span>
              </div>
              <div class="space-y-1.5 font-code-sm text-xs">
                <div class="flex justify-between">
                  <span class="text-outline">Embedding Model:</span>
                  <span class="text-on-surface font-mono">${settings.embedding_model.split('/').pop()}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-outline">LLM Provider:</span>
                  <span class="text-on-surface">${settings.llm_provider} (${settings.gemini_model})</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-outline">RAG Top-K:</span>
                  <span class="text-primary font-bold">${settings.rag_top_k}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-outline">Max Upload:</span>
                  <span class="text-on-surface">${settings.max_upload_size_mb} MB</span>
                </div>
              </div>
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<div class="text-xs text-error py-4">Settings load failed: ${err.message}</div>`;
    }
}

// ── Auth Handling ──
window.showLoginModal = function() {
    document.getElementById('login-modal').classList.remove('hidden');
};

window.handleLoginSubmit = async function(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    try {
        const res = await CyberTraceAPI.login(email, password);
        showToast(`Authenticated as ${res.user.full_name}`, "success");
        document.getElementById('login-modal').classList.add('hidden');
        updateUserUI(res.user);
        loadOverview();
    } catch (err) {
        showToast(`Login failed: ${err.message}`, "error");
    }
};

window.logout = function() {
    CyberTraceAPI.removeToken();
    showToast("Session terminated.", "info");
    document.getElementById('user-badge').innerText = '?';
    document.getElementById('drawer-user-name').innerText = 'ANONYMOUS';
    document.getElementById('drawer-user-role').innerText = 'UNAUTHENTICATED';
    showLoginModal();
};

function updateUserUI(user) {
    if (!user) return;
    const initial = user.full_name ? user.full_name[0].toUpperCase() : 'C';
    document.getElementById('user-badge').innerText = initial;
    document.getElementById('drawer-user-avatar').innerText = initial;
    document.getElementById('drawer-user-name').innerText = user.full_name.toUpperCase();
    document.getElementById('drawer-user-role').innerText = `L3 ${user.role}`;
}

// ── App Initialization ──
async function initApp() {
    // Check if token exists, else attempt auto-login using demonstration admin account
    let token = CyberTraceAPI.getToken();
    if (!token) {
        try {
            await CyberTraceAPI.login('admin@cybertrace.ai', 'CyberTrace2026!');
        } catch {
            // Seed DB might not have run yet, which is fine
        }
    }

    const user = CyberTraceAPI.getUser();
    if (user) {
        updateUserUI(user);
    }

    // Load initial cases and overview
    await loadOverview();
    await loadCases();
}

window.addEventListener('DOMContentLoaded', initApp);

const API_BASE = (window.CYBERTRACE_API_URL || window.location.origin).replace(/\/$/, '') + '/api';


class CyberTraceAPI {
    static getToken() {
        return localStorage.getItem('cybertrace_token') || '';
    }

    static setToken(token) {
        localStorage.setItem('cybertrace_token', token);
    }

    static removeToken() {
        localStorage.removeItem('cybertrace_token');
        localStorage.removeItem('cybertrace_user');
    }

    static getUser() {
        try {
            return JSON.parse(localStorage.getItem('cybertrace_user') || 'null');
        } catch {
            return null;
        }
    }

    static setUser(user) {
        localStorage.setItem('cybertrace_user', JSON.stringify(user));
    }

    static async request(endpoint, options = {}) {
        const headers = options.headers || {};
        const token = this.getToken();
        if (token && !headers['Authorization']) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const res = await fetch(`${API_BASE}${endpoint}`, config);

            if (res.status === 401 && !endpoint.includes('/auth/login')) {
                this.removeToken();
                window.showLoginModal && window.showLoginModal();
                throw new Error("Authentication required or session expired.");
            }

            if (!res.ok) {
                const errData = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(errData.detail || "API request failed");
            }

            // If binary file response (e.g. PDF download)
            const contentType = res.headers.get('content-type') || '';
            if (contentType.includes('application/pdf') || contentType.includes('application/octet-stream')) {
                return res.blob();
            }

            if (res.status === 204) {
                return null;
            }

            return await res.json();
        } catch (err) {
            console.error(`[API Error] ${endpoint}:`, err);
            window.showToast && window.showToast(err.message, 'error');
            throw err;
        }
    }

    // ── Auth ──
    static async login(email, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        this.setToken(data.access_token);
        this.setUser(data.user);
        return data;
    }

    static async getProfile() {
        return this.request('/auth/me');
    }

    static async register(full_name, email, password, role = 'INVESTIGATOR') {
        return this.request('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name, email, password, role })
        });
    }

    // ── Dashboard ──
    static async getDashboardOverview() {
        return this.request('/dashboard/overview');
    }

    static async getDashboardAnalytics() {
        return this.request('/dashboard/analytics');
    }

    static async getRecentActivity() {
        return this.request('/dashboard/recent-activity');
    }

    // ── Cases ──
    static async getCases(params = {}) {
        const q = new URLSearchParams(params).toString();
        return this.request(`/cases?${q}`);
    }

    static async getCase(caseId) {
        return this.request(`/cases/${caseId}`);
    }

    static async createCase(caseData) {
        return this.request('/cases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(caseData)
        });
    }

    static async updateCase(caseId, updateData) {
        return this.request(`/cases/${caseId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });
    }

    // ── Evidence ──
    static async getEvidence(params = {}) {
        const q = new URLSearchParams(params).toString();
        return this.request(`/evidence?${q}`);
    }

    static async getEvidenceDetail(evidenceId) {
        return this.request(`/evidence/${evidenceId}`);
    }

    static async getEvidencePreview(evidenceId) {
        return this.request(`/evidence/${evidenceId}/preview`);
    }

    static async verifyHash(evidenceId) {
        return this.request(`/evidence/${evidenceId}/hash`);
    }

    static async getCustody(evidenceId) {
        return this.request(`/evidence/${evidenceId}/custody`);
    }

    static async uploadEvidence(caseId, file) {
        const formData = new FormData();
        formData.append('case_id', caseId);
        formData.append('file', file);
        return this.request('/evidence/upload', {
            method: 'POST',
            body: formData
        });
    }

    // ── AI RAG Investigation ──
    static async chatRAG(caseId, question, sessionId = 'default-session') {
        return this.request('/investigation/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                case_id: caseId,
                session_id: sessionId,
                question: question
            })
        });
    }

    static async getChatHistory(caseId) {
        return this.request(`/investigation/history/${caseId}`);
    }

    // ── Log Analysis ──
    static async analyzeLog(file, caseId = '', logFormat = 'auto') {
        const formData = new FormData();
        formData.append('file', file);
        if (caseId) formData.append('case_id', caseId);
        formData.append('log_format', logFormat);
        return this.request('/logs/analyze', {
            method: 'POST',
            body: formData
        });
    }

    // ── IP Intelligence ──
    static async analyzeIP(ipAddress, caseId = '') {
        return this.request('/ip/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip_address: ipAddress, case_id: caseId || null })
        });
    }

    // ── Timeline ──
    static async getTimeline(caseId, params = {}) {
        const q = new URLSearchParams(params).toString();
        return this.request(`/timeline/${caseId}?${q}`);
    }

    // ── Threats ──
    static async getThreats(params = {}) {
        const q = new URLSearchParams(params).toString();
        return this.request(`/threats?${q}`);
    }

    static async updateThreatStatus(threatId, status) {
        return this.request(`/threats/${threatId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
    }

    // ── Reports ──
    static async getReports(caseId = '') {
        const q = caseId ? `?case_id=${caseId}` : '';
        return this.request(`/reports${q}`);
    }

    static async generateReport(caseId, reportTitle = '') {
        return this.request('/reports/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ case_id: caseId, report_title: reportTitle })
        });
    }

    static async downloadReport(reportId, reportNum = 'report') {
        const blob = await this.request(`/reports/${reportId}/download`);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${reportNum}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    }

    // ── Knowledge Base ──
    static async getKnowledgeDocs() {
        return this.request('/knowledge/documents');
    }

    static async uploadKnowledge(file, category = 'Digital Forensics') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', category);
        return this.request('/knowledge/upload', {
            method: 'POST',
            body: formData
        });
    }

    static async searchKnowledge(query) {
        return this.request(`/knowledge/search?query=${encodeURIComponent(query)}`);
    }

    // ── System Settings & Health ──
    static async getSettings() {
        return this.request('/settings');
    }

    static async getHealth() {
        return this.request('/health');
    }
}

window.CyberTraceAPI = CyberTraceAPI;

/**
 * Smart CRM API Client
 *
 * A JavaScript client for communicating with the Smart CRM Flask API.
 * Handles authentication, API requests, and error handling.
 */

// Use relative URL so it works in both development and production
const API_BASE_URL = '/api';

// Token management
let authToken = localStorage.getItem('crm_token');

/**
 * Set the authentication token
 */
function setToken(token) {
    authToken = token;
    if (token) {
        localStorage.setItem('crm_token', token);
    } else {
        localStorage.removeItem('crm_token');
    }
}

/**
 * Get the current token
 */
function getToken() {
    return authToken || localStorage.getItem('crm_token');
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!getToken();
}

/**
 * Make an API request
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    // Add auth token if available
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP error ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ==================== AUTH API ====================

const AuthAPI = {
    /**
     * Login with email and password
     */
    async login(email, password) {
        const response = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        if (response.token) {
            setToken(response.token);
        }

        return response;
    },

    /**
     * Logout current user
     */
    async logout() {
        try {
            await apiRequest('/auth/logout', { method: 'POST' });
        } finally {
            setToken(null);
        }
    },

    /**
     * Get current user info
     */
    async getCurrentUser() {
        return apiRequest('/auth/me');
    },

    /**
     * Register new user (admin only)
     */
    async register(userData) {
        return apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    },

    /**
     * List all users (admin only)
     */
    async listUsers() {
        return apiRequest('/auth/users');
    },

    /**
     * Update user profile
     */
    async updateUser(userId, userData) {
        return apiRequest(`/auth/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(userData)
        });
    }
};

// ==================== LEADS API ====================

const LeadsAPI = {
    /**
     * Get all leads with optional filters
     */
    async getAll(filters = {}) {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                params.append(key, value);
            }
        });
        const query = params.toString() ? `?${params.toString()}` : '';
        return apiRequest(`/leads${query}`);
    },

    /**
     * Get lead by ID
     */
    async getById(leadId) {
        return apiRequest(`/leads/${leadId}`);
    },

    /**
     * Create new lead
     */
    async create(leadData) {
        return apiRequest('/leads', {
            method: 'POST',
            body: JSON.stringify(leadData)
        });
    },

    /**
     * Update lead
     */
    async update(leadId, leadData) {
        return apiRequest(`/leads/${leadId}`, {
            method: 'PUT',
            body: JSON.stringify(leadData)
        });
    },

    /**
     * Delete lead
     */
    async delete(leadId) {
        return apiRequest(`/leads/${leadId}`, { method: 'DELETE' });
    },

    /**
     * Get top scored leads
     */
    async getTopScored(limit = 10) {
        return apiRequest(`/leads/top-scored?limit=${limit}`);
    },

    /**
     * Check for duplicate leads
     */
    async checkDuplicate(params) {
        const queryParams = new URLSearchParams(params).toString();
        return apiRequest(`/leads/check-duplicate?${queryParams}`);
    },

    /**
     * Recalculate lead score
     */
    async recalculateScore(leadId) {
        return apiRequest(`/leads/${leadId}/score`, { method: 'POST' });
    },

    /**
     * Get lead interactions
     */
    async getInteractions(leadId) {
        return apiRequest(`/leads/${leadId}/interactions`);
    },

    /**
     * Add interaction to lead
     */
    async addInteraction(leadId, interactionData) {
        return apiRequest(`/leads/${leadId}/interactions`, {
            method: 'POST',
            body: JSON.stringify(interactionData)
        });
    },

    /**
     * Get lead statistics
     */
    async getStats() {
        return apiRequest('/leads/stats');
    }
};

// ==================== DEALS API ====================

const DealsAPI = {
    /**
     * Get all deals
     */
    async getAll(filters = {}) {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                params.append(key, value);
            }
        });
        const query = params.toString() ? `?${params.toString()}` : '';
        return apiRequest(`/deals${query}`);
    },

    /**
     * Get pipeline data (grouped by stage)
     */
    async getPipeline() {
        return apiRequest('/deals/pipeline');
    },

    /**
     * Get deal by ID
     */
    async getById(dealId) {
        return apiRequest(`/deals/${dealId}`);
    },

    /**
     * Create new deal
     */
    async create(dealData) {
        return apiRequest('/deals', {
            method: 'POST',
            body: JSON.stringify(dealData)
        });
    },

    /**
     * Update deal
     */
    async update(dealId, dealData) {
        return apiRequest(`/deals/${dealId}`, {
            method: 'PUT',
            body: JSON.stringify(dealData)
        });
    },

    /**
     * Update deal stage (for drag-and-drop)
     */
    async updateStage(dealId, stage) {
        return apiRequest(`/deals/${dealId}/stage`, {
            method: 'PATCH',
            body: JSON.stringify({ stage })
        });
    },

    /**
     * Delete deal
     */
    async delete(dealId) {
        return apiRequest(`/deals/${dealId}`, { method: 'DELETE' });
    },

    /**
     * Get deal statistics
     */
    async getStats() {
        return apiRequest('/deals/stats');
    },

    /**
     * Get revenue statistics
     */
    async getRevenue(startDate, endDate) {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        const query = params.toString() ? `?${params.toString()}` : '';
        return apiRequest(`/deals/revenue${query}`);
    },

    /**
     * Get work logs for a deal
     */
    async getWorkLogs(dealId) {
        return apiRequest(`/deals/${dealId}/work-logs`);
    },

    /**
     * Add work log to deal
     */
    async addWorkLog(dealId, logData) {
        return apiRequest(`/deals/${dealId}/work-logs`, {
            method: 'POST',
            body: JSON.stringify(logData)
        });
    }
};

// ==================== TASKS API ====================

const TasksAPI = {
    /**
     * Get all tasks
     */
    async getAll(filters = {}) {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                params.append(key, value);
            }
        });
        const query = params.toString() ? `?${params.toString()}` : '';
        return apiRequest(`/tasks${query}`);
    },

    /**
     * Get task by ID
     */
    async getById(taskId) {
        return apiRequest(`/tasks/${taskId}`);
    },

    /**
     * Create new task
     */
    async create(taskData) {
        return apiRequest('/tasks', {
            method: 'POST',
            body: JSON.stringify(taskData)
        });
    },

    /**
     * Update task
     */
    async update(taskId, taskData) {
        return apiRequest(`/tasks/${taskId}`, {
            method: 'PUT',
            body: JSON.stringify(taskData)
        });
    },

    /**
     * Update task status
     */
    async updateStatus(taskId, status) {
        return apiRequest(`/tasks/${taskId}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status })
        });
    },

    /**
     * Mark task as handled
     */
    async markHandled(taskId) {
        return apiRequest(`/tasks/${taskId}/handle`, { method: 'PATCH' });
    },

    /**
     * Delete task
     */
    async delete(taskId) {
        return apiRequest(`/tasks/${taskId}`, { method: 'DELETE' });
    },

    /**
     * Get tasks due today
     */
    async getDueToday() {
        return apiRequest('/tasks/due-today');
    },

    /**
     * Get overdue tasks
     */
    async getOverdue() {
        return apiRequest('/tasks/overdue');
    },

    /**
     * Get tasks due this week
     */
    async getThisWeek() {
        return apiRequest('/tasks/this-week');
    },

    /**
     * Get task statistics
     */
    async getStats() {
        return apiRequest('/tasks/stats');
    }
};

// ==================== ANALYTICS API ====================

const AnalyticsAPI = {
    /**
     * Get dashboard data
     */
    async getDashboard() {
        return apiRequest('/analytics/dashboard');
    },

    /**
     * Get profitability report
     */
    async getProfitability(startDate, endDate) {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        const query = params.toString() ? `?${params.toString()}` : '';
        return apiRequest(`/analytics/profitability${query}`);
    },

    /**
     * Get pipeline analytics
     */
    async getPipeline() {
        return apiRequest('/analytics/pipeline');
    },

    /**
     * Get lead source analytics
     */
    async getLeadSources() {
        return apiRequest('/analytics/lead-sources');
    },

    /**
     * Get representative performance (admin only)
     */
    async getRepPerformance() {
        return apiRequest('/analytics/representative-performance');
    },

    /**
     * Get revenue chart data
     */
    async getRevenueChart() {
        return apiRequest('/analytics/revenue-chart');
    }
};

// ==================== CHAT API ====================

const ChatAPI = {
    /**
     * Create new chat session
     */
    async createSession(visitorData = {}) {
        return apiRequest('/chat/session', {
            method: 'POST',
            body: JSON.stringify(visitorData)
        });
    },

    /**
     * Get chat session
     */
    async getSession(sessionId) {
        return apiRequest(`/chat/session/${sessionId}`);
    },

    /**
     * Change chat mode
     */
    async changeMode(sessionId, mode) {
        return apiRequest(`/chat/session/${sessionId}/mode`, {
            method: 'PATCH',
            body: JSON.stringify({ mode })
        });
    },

    /**
     * Send message and get AI response
     */
    async sendMessage(sessionId, content) {
        return apiRequest('/chat/message', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId, content })
        });
    },

    /**
     * Get chat history
     */
    async getHistory(sessionId, limit = 100) {
        return apiRequest(`/chat/history/${sessionId}?limit=${limit}`);
    },

    /**
     * Escalate to human
     */
    async escalate(sessionId) {
        return apiRequest(`/chat/session/${sessionId}/escalate`, { method: 'POST' });
    },

    /**
     * Close chat session
     */
    async close(sessionId) {
        return apiRequest(`/chat/session/${sessionId}/close`, { method: 'POST' });
    },

    /**
     * Update visitor info
     */
    async updateVisitor(sessionId, visitorData) {
        return apiRequest(`/chat/session/${sessionId}/update`, {
            method: 'PATCH',
            body: JSON.stringify(visitorData)
        });
    }
};

// ==================== RAG API ====================

const RAGAPI = {
    /**
     * Query CRM data with natural language
     */
    async query(question) {
        return apiRequest('/rag/query', {
            method: 'POST',
            body: JSON.stringify({ question })
        });
    },

    /**
     * Refresh the vector store index
     */
    async refreshIndex() {
        return apiRequest('/rag/index/refresh', { method: 'POST' });
    }
};

// ==================== EXPORTS ====================

// Export all APIs
const CRM = {
    Auth: AuthAPI,
    Leads: LeadsAPI,
    Deals: DealsAPI,
    Tasks: TasksAPI,
    Analytics: AnalyticsAPI,
    Chat: ChatAPI,
    RAG: RAGAPI,

    // Utility functions
    setToken,
    getToken,
    isAuthenticated,
    apiRequest
};

// For ES6 modules
export {
    CRM,
    AuthAPI,
    LeadsAPI,
    DealsAPI,
    TasksAPI,
    AnalyticsAPI,
    ChatAPI,
    RAGAPI,
    setToken,
    getToken,
    isAuthenticated,
    apiRequest
};

// For script tag usage
if (typeof window !== 'undefined') {
    window.CRM = CRM;
}

# ==================== ADMIN DASHBOARD ====================
@app.route('/admin')
def serve_admin():
    """Serve the enhanced admin dashboard"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - AIMatrix</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary: #f43f5e;
            --dark: #0f172a;
            --muted: #6b7280;
            --bg: #f8fafc;
            --card: #ffffff;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #3b82f6;
        }
        
        body { 
            font-family: 'Poppins', sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: var(--bg); 
            color: var(--dark); 
        }
        
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
        }
        
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 30px; 
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        
        .stat-card { 
            background: white; 
            padding: 25px; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            text-align: center; 
            border-left: 4px solid var(--primary);
        }
        
        .stat-number { 
            font-size: 2.5em; 
            font-weight: 700; 
            color: var(--primary); 
            margin: 10px 0; 
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .btn-primary { background: var(--primary); color: white; }
        .btn-success { background: var(--success); color: white; }
        .btn-danger { background: var(--danger); color: white; }
        .btn-warning { background: var(--warning); color: white; }
        .btn-info { background: var(--info); color: white; }
        
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .submissions-grid {
            display: grid;
            gap: 15px;
        }
        
        .submission-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-left: 4px solid var(--success);
        }
        
        .submission-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .submission-meta {
            color: var(--muted);
            font-size: 12px;
            margin: 5px 0;
        }
        
        .submission-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .status-badge, .priority-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status-new { background: #dbeafe; color: #1e40af; }
        .status-read { background: #dcfce7; color: #166534; }
        .status-archived { background: #f3f4f6; color: #374151; }
        .status-replied { background: #fef3c7; color: #92400e; }
        
        .priority-low { background: #d1fae5; color: #065f46; }
        .priority-normal { background: #dbeafe; color: #1e40af; }
        .priority-high { background: #fef3c7; color: #92400e; }
        .priority-urgent { background: #fee2e2; color: #991b1b; }
        
        .loading { 
            text-align: center; 
            padding: 40px; 
            color: var(--muted); 
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--muted);
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .alert-success { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .alert-error { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        
        .system-status {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f1f5f9;
        }
        
        .tab-container {
            margin: 20px 0;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .tab {
            padding: 10px 20px;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .tab.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .bulk-actions {
            background: #f8fafc;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            display: none;
        }
        
        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 5px 0;
        }
        
        @media (max-width: 768px) {
            .header { flex-direction: column; align-items: flex-start; }
            .stats { grid-template-columns: 1fr 1fr; }
            .dashboard-grid { grid-template-columns: 1fr; }
            .submission-actions { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-rocket"></i> AIMatrix Admin Dashboard v2.1</h1>
            <div class="controls">
                <button class="btn btn-primary" onclick="loadDashboard()"><i class="fas fa-sync-alt"></i> Refresh</button>
                <button class="btn btn-success" onclick="exportData()"><i class="fas fa-download"></i> Export CSV</button>
                <button class="btn btn-info" onclick="showSystemHealth()"><i class="fas fa-heartbeat"></i> System Health</button>
                <button class="btn btn-warning" onclick="showAdvancedAnalytics()"><i class="fas fa-chart-bar"></i> Analytics</button>
            </div>
        </div>
        
        <div id="alert-container"></div>
        <div id="system-health" class="system-status" style="display: none;"></div>
        
        <div class="tab-container">
            <div class="tabs">
                <div class="tab active" onclick="switchTab('overview')">📊 Overview</div>
                <div class="tab" onclick="switchTab('submissions')">📨 Submissions</div>
                <div class="tab" onclick="switchTab('analytics')">📈 Analytics</div>
                <div class="tab" onclick="switchTab('system')">⚙️ System</div>
            </div>
            
            <div id="tab-overview" class="tab-content active">
                <div class="stats" id="stats">
                    <div class="loading">Loading analytics...</div>
                </div>
                
                <div class="dashboard-grid">
                    <div class="chart-container">
                        <h3><i class="fas fa-chart-line"></i> Submission Trends</h3>
                        <canvas id="trendsChart" width="400" height="200"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3><i class="fas fa-chart-pie"></i> Status Distribution</h3>
                        <canvas id="statusChart" width="400" height="200"></canvas>
                    </div>
                </div>
            </div>
            
            <div id="tab-submissions" class="tab-content">
                <div class="controls">
                    <select id="status-filter" onchange="loadSubmissions()">
                        <option value="all">All Status</option>
                        <option value="new">New</option>
                        <option value="read">Read</option>
                        <option value="replied">Replied</option>
                        <option value="archived">Archived</option>
                    </select>
                    <select id="priority-filter" onchange="loadSubmissions()">
                        <option value="all">All Priority</option>
                        <option value="low">Low</option>
                        <option value="normal">Normal</option>
                        <option value="high">High</option>
                        <option value="urgent">Urgent</option>
                    </select>
                    <button class="btn btn-info" onclick="toggleBulkActions()"><i class="fas fa-tasks"></i> Bulk Actions</button>
                </div>
                
                <div id="bulk-actions" class="bulk-actions">
                    <h4>Bulk Actions</h4>
                    <div id="selected-count">0 submissions selected</div>
                    <div class="submission-actions">
                        <button class="btn btn-success" onclick="bulkUpdate('read')"><i class="fas fa-eye"></i> Mark as Read</button>
                        <button class="btn btn-warning" onclick="bulkUpdate('replied')"><i class="fas fa-reply"></i> Mark as Replied</button>
                        <button class="btn btn-info" onclick="bulkUpdate('archived')"><i class="fas fa-archive"></i> Archive</button>
                        <button class="btn btn-danger" onclick="bulkDelete()"><i class="fas fa-trash"></i> Delete</button>
                    </div>
                </div>
                
                <div id="submissions">
                    <div class="loading">Loading submissions...</div>
                </div>
            </div>
            
            <div id="tab-analytics" class="tab-content">
                <div class="chart-container">
                    <h3><i class="fas fa-chart-bar"></i> Advanced Analytics</h3>
                    <div id="advanced-analytics">
                        <div class="loading">Loading advanced analytics...</div>
                    </div>
                </div>
            </div>
            
            <div id="tab-system" class="tab-content">
                <div class="system-status">
                    <h3><i class="fas fa-cogs"></i> System Information</h3>
                    <div id="system-logs">
                        <div class="loading">Loading system logs...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const BACKEND_URL = window.location.origin;
        let selectedSubmissions = new Set();
        let trendsChart = null;
        let statusChart = null;
        
        function showAlert(message, type = 'success') {
            const alertContainer = document.getElementById('alert-container');
            const alertId = 'alert-' + Date.now();
            alertContainer.innerHTML = `
                <div id="${alertId}" class="alert alert-${type}">
                    <i class="fas fa-${type === 'success' ? 'check' : 'exclamation-triangle'}"></i>
                    ${message}
                    <button onclick="document.getElementById('${alertId}').remove()" 
                            style="float: right; background: none; border: none; cursor: pointer;">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            setTimeout(() => {
                const alert = document.getElementById(alertId);
                if (alert) alert.remove();
            }, 5000);
        }
        
        function switchTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(`tab-${tabName}`).classList.add('active');
            event.target.classList.add('active');
            
            // Load tab-specific data
            if (tabName === 'analytics') {
                loadAdvancedAnalytics();
            } else if (tabName === 'system') {
                loadSystemLogs();
            }
        }
        
        async function loadDashboard() {
            try {
                // Load basic analytics
                const analyticsResponse = await fetch(BACKEND_URL + '/api/analytics');
                if (!analyticsResponse.ok) throw new Error('Analytics API failed');
                const analytics = await analyticsResponse.json();
                
                if (analytics.success) {
                    document.getElementById('stats').innerHTML = `
                        <div class="stat-card">
                            <div class="stat-number">${analytics.data.submissions.total}</div>
                            <div>Total Submissions</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${analytics.data.submissions.today}</div>
                            <div>Today</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${analytics.data.submissions.unique_emails}</div>
                            <div>Unique Emails</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${analytics.data.submissions.this_week}</div>
                            <div>This Week</div>
                        </div>
                    `;
                    
                    // Load charts
                    loadCharts(analytics.data);
                }
                
                // Load submissions for submissions tab
                loadSubmissions();
                
            } catch (error) {
                console.error('Dashboard error:', error);
                showAlert('Error loading dashboard: ' + error.message, 'error');
            }
        }
        
        function loadCharts(data) {
            // Trends Chart
            const trendsCtx = document.getElementById('trendsChart').getContext('2d');
            if (trendsChart) trendsChart.destroy();
            
            trendsChart = new Chart(trendsCtx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Submissions',
                        data: [12, 19, 8, 15, 12, 18, 14],
                        borderColor: '#f43f5e',
                        backgroundColor: 'rgba(244, 63, 94, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            
            // Status Chart
            const statusCtx = document.getElementById('statusChart').getContext('2d');
            if (statusChart) statusChart.destroy();
            
            statusChart = new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['New', 'Read', 'Replied', 'Archived'],
                    datasets: [{
                        data: [
                            data.status_distribution.new || 0,
                            data.status_distribution.read || 0,
                            data.status_distribution.replied || 0,
                            data.status_distribution.archived || 0
                        ],
                        backgroundColor: [
                            '#dbeafe',
                            '#dcfce7',
                            '#fef3c7',
                            '#f3f4f6'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
        
        async function loadSubmissions() {
            try {
                const status = document.getElementById('status-filter').value;
                const priority = document.getElementById('priority-filter').value;
                
                const response = await fetch(`${BACKEND_URL}/api/submissions?status=${status}&priority=${priority}`);
                if (!response.ok) throw new Error('Failed to load submissions');
                
                const result = await response.json();
                
                if (result.success) {
                    const submissionsDiv = document.getElementById('submissions');
                    
                    if (result.data.submissions.length === 0) {
                        submissionsDiv.innerHTML = `
                            <div class="empty-state">
                                <i class="fas fa-inbox" style="font-size: 48px; margin-bottom: 20px;"></i>
                                <h3>No submissions found</h3>
                                <p>Try changing your filters or check back later.</p>
                            </div>
                        `;
                        return;
                    }
                    
                    submissionsDiv.innerHTML = `
                        <div class="submissions-grid">
                            ${result.data.submissions.map(sub => `
                                <div class="submission-card" data-id="${sub.id}">
                                    <div class="submission-header">
                                        <div>
                                            <h4>${sub.name}</h4>
                                            <div class="submission-meta">${sub.email}</div>
                                        </div>
                                        <div>
                                            <span class="status-badge status-${sub.status}">${sub.status}</span>
                                            <span class="priority-badge priority-${sub.priority}">${sub.priority}</span>
                                        </div>
                                    </div>
                                    <p>${sub.message}</p>
                                    <div class="submission-meta">
                                        <i class="far fa-clock"></i> ${new Date(sub.submitted_at).toLocaleString()}
                                        <i class="fas fa-globe"></i> ${sub.ip_address || 'Unknown IP'}
                                    </div>
                                    <div class="submission-actions">
                                        <input type="checkbox" class="bulk-select" data-id="${sub.id}" onchange="toggleSelection(${sub.id})">
                                        <button class="btn btn-success btn-sm" onclick="updateSubmission(${sub.id}, 'read')">
                                            <i class="fas fa-eye"></i> Read
                                        </button>
                                        <button class="btn btn-warning btn-sm" onclick="updateSubmission(${sub.id}, 'replied')">
                                            <i class="fas fa-reply"></i> Replied
                                        </button>
                                        <button class="btn btn-info btn-sm" onclick="updateSubmission(${sub.id}, 'archived')">
                                            <i class="fas fa-archive"></i> Archive
                                        </button>
                                        <button class="btn btn-danger btn-sm" onclick="deleteSubmission(${sub.id})">
                                            <i class="fas fa-trash"></i> Delete
                                        </button>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading submissions:', error);
                showAlert('Error loading submissions: ' + error.message, 'error');
            }
        }
        
        // The rest of your JavaScript functions continue here...
        // You need to add the missing JavaScript functions
        
        function toggleSelection(id) {
            if (selectedSubmissions.has(id)) {
                selectedSubmissions.delete(id);
            } else {
                selectedSubmissions.add(id);
            }
            document.getElementById('selected-count').textContent = `${selectedSubmissions.size} submissions selected`;
        }
        
        function toggleBulkActions() {
            const bulkDiv = document.getElementById('bulk-actions');
            bulkDiv.style.display = bulkDiv.style.display === 'none' ? 'block' : 'none';
        }
        
        async function bulkUpdate(action) {
            if (selectedSubmissions.size === 0) {
                showAlert('Please select submissions first', 'error');
                return;
            }
            
            try {
                const response = await fetch(`${BACKEND_URL}/api/submissions/bulk`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        submission_ids: Array.from(selectedSubmissions),
                        action: action
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    showAlert(result.message);
                    selectedSubmissions.clear();
                    loadSubmissions();
                    loadDashboard();
                } else {
                    showAlert(result.error, 'error');
                }
            } catch (error) {
                showAlert('Error: ' + error.message, 'error');
            }
        }
        
        async function bulkDelete() {
            if (!confirm(`Are you sure you want to delete ${selectedSubmissions.size} submissions?`)) return;
            
            try {
                const response = await fetch(`${BACKEND_URL}/api/submissions/bulk`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        submission_ids: Array.from(selectedSubmissions),
                        action: 'delete'
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    showAlert(result.message);
                    selectedSubmissions.clear();
                    loadSubmissions();
                    loadDashboard();
                } else {
                    showAlert(result.error, 'error');
                }
            } catch (error) {
                showAlert('Error: ' + error.message, 'error');
            }
        }
        
        async function updateSubmission(id, status) {
            try {
                const response = await fetch(`${BACKEND_URL}/api/submissions/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status })
                });
                
                const result = await response.json();
                if (result.success) {
                    showAlert('Submission updated');
                    loadSubmissions();
                }
            } catch (error) {
                showAlert('Error updating submission: ' + error.message, 'error');
            }
        }
        
        async function deleteSubmission(id) {
            if (!confirm('Are you sure you want to delete this submission?')) return;
            
            try {
                const response = await fetch(`${BACKEND_URL}/api/submissions/${id}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                if (result.success) {
                    showAlert('Submission deleted');
                    loadSubmissions();
                    loadDashboard();
                }
            } catch (error) {
                showAlert('Error deleting submission: ' + error.message, 'error');
            }
        }
        
        async function exportData() {
            try {
                const response = await fetch(`${BACKEND_URL}/api/submissions/export`);
                if (!response.ok) throw new Error('Export failed');
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `submissions_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                showAlert('Data exported successfully');
            } catch (error) {
                showAlert('Export error: ' + error.message, 'error');
            }
        }
        
        async function showSystemHealth() {
            try {
                const response = await fetch(`${BACKEND_URL}/api/system/health`);
                if (!response.ok) throw new Error('Health check failed');
                
                const result = await response.json();
                const healthDiv = document.getElementById('system-health');
                
                if (result.success) {
                    healthDiv.innerHTML = `
                        <h3><i class="fas fa-heartbeat"></i> System Health</h3>
                        <div class="status-item">
                            <span>Status:</span>
                            <span style="color: ${result.data.status === 'healthy' ? 'var(--success)' : 'var(--danger)'}">
                                <i class="fas fa-${result.data.status === 'healthy' ? 'check-circle' : 'exclamation-circle'}"></i>
                                ${result.data.status}
                            </span>
                        </div>
                        <div class="status-item">
                            <span>Total Submissions:</span>
                            <span>${result.data.metrics.total_submissions}</span>
                        </div>
                        <div class="status-item">
                            <span>Today's Submissions:</span>
                            <span>${result.data.metrics.today_submissions}</span>
                        </div>
                        <div class="status-item">
                            <span>Pending:</span>
                            <span>${result.data.metrics.pending_submissions}</span>
                        </div>
                        <div class="status-item">
                            <span>Database:</span>
                            <span style="color: var(--success)">
                                <i class="fas fa-check-circle"></i> Connected
                            </span>
                        </div>
                        <div class="status-item">
                            <span>Email Service:</span>
                            <span style="color: ${result.data.services.email_service === 'configured' ? 'var(--success)' : 'var(--warning)'}">
                                <i class="fas fa-${result.data.services.email_service === 'configured' ? 'check-circle' : 'exclamation-triangle'}"></i>
                                ${result.data.services.email_service}
                            </span>
                        </div>
                        <button class="btn btn-primary" onclick="healthDiv.style.display = 'none'" style="margin-top: 15px;">
                            Close
                        </button>
                    `;
                    healthDiv.style.display = 'block';
                }
            } catch (error) {
                showAlert('Health check error: ' + error.message, 'error');
            }
        }
        
        async function showAdvancedAnalytics() {
            try {
                const response = await fetch(`${BACKEND_URL}/api/analytics/advanced`);
                if (!response.ok) throw new Error('Analytics failed');
                
                const result = await response.json();
                const analyticsDiv = document.getElementById('advanced-analytics');
                
                if (result.success) {
                    analyticsDiv.innerHTML = `
                        <h4>Daily Trends (Last 30 Days)</h4>
                        <div style="max-height: 300px; overflow-y: auto;">
                            ${result.data.daily_trends.map(day => `
                                <div class="status-item">
                                    <span>${day.date}:</span>
                                    <span>${day.count} submissions (${day.unique_emails} unique)</span>
                                </div>
                            `).join('')}
                        </div>
                        <h4 style="margin-top: 20px;">Email Performance</h4>
                        ${result.data.email_performance.map(email => `
                            <div class="status-item">
                                <span>${email.email_type}:</span>
                                <span>${email.status} (${email.count})</span>
                            </div>
                        `).join('')}
                    `;
                    
                    // Show the system health div to display analytics
                    const healthDiv = document.getElementById('system-health');
                    healthDiv.innerHTML = analyticsDiv.innerHTML;
                    healthDiv.style.display = 'block';
                }
            } catch (error) {
                showAlert('Analytics error: ' + error.message, 'error');
            }
        }
        
        async function loadAdvancedAnalytics() {
            await showAdvancedAnalytics();
        }
        
        async function loadSystemLogs() {
            try {
                const response = await fetch(`${BACKEND_URL}/api/system/logs`);
                if (!response.ok) throw new Error('Failed to load logs');
                
                const result = await response.json();
                const logsDiv = document.getElementById('system-logs');
                
                if (result.success) {
                    logsDiv.innerHTML = `
                        <h4>Recent System Logs</h4>
                        <div style="max-height: 400px; overflow-y: auto;">
                            ${result.data.logs.map(log => `
                                <div class="status-item">
                                    <div>
                                        <strong>${log.action}</strong><br>
                                        <small>${log.details}</small>
                                    </div>
                                    <div style="text-align: right;">
                                        <small>${new Date(log.timestamp).toLocaleString()}</small><br>
                                        <small>${log.ip_address || 'N/A'}</small>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }
            } catch (error) {
                showAlert('Error loading logs: ' + error.message, 'error');
            }
        }
        
        // Initialize dashboard on load
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboard();
        });
    </script>
</body>
</html>
'''  # <-- THIS WAS MISSING! You need this closing triple quote

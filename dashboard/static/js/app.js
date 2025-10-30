function getScoreClass(score) {
    if (score >= 70) return 'score-high';
    if (score >= 50) return 'score-medium';
    return 'score-low';
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num;
}

function formatDuration(seconds) {
    const sec = parseInt(seconds) || 0;
    if (sec === 0) return 'N/A';
    
    const hours = Math.floor(sec / 3600);
    const minutes = Math.floor((sec % 3600) / 60);
    const secs = sec % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

function showNotification(message, type = 'info') {
    // Create notification container if it doesn't exist
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    const icons = {
        success: { bg: '#10b981', icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M7 10L9 12L13 8M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>' },
        error: { bg: '#ef4444', icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 6V10M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>' },
        info: { bg: '#3b82f6', icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 14V10M10 6H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>' },
        warning: { bg: '#f59e0b', icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 6V10M10 14H10.01M8.5 2.5L1.5 15C1.18 15.6 1.66 16.33 2.38 16.33H17.62C18.34 16.33 18.82 15.6 18.5 15L11.5 2.5C11.18 1.9 10.32 1.9 10 2.5H8.5Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>' }
    };
    const color = icons[type] || icons.info;
    
    notification.style.cssText = `
        background: ${color.bg};
        color: white;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 300px;
        max-width: 500px;
        animation: slideIn 0.3s ease-out;
        font-size: 14px;
        font-weight: 500;
    `;
    
    notification.innerHTML = `
        <span style="display: flex; align-items: center; justify-content: center;">${color.icon}</span>
        <span style="flex: 1;">${message}</span>
        <button onclick="this.parentElement.remove()" style="
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        " onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">×</button>
    `;
    
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Add CSS animations if not already present
if (!document.getElementById('notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        // Handle case where no data is available yet
        if (!data.total || data.total === 0) {
            document.getElementById('stats-container').innerHTML = 
                '<div class="loading">Aucune donnée disponible. Lancez un scraping pour commencer.</div>';
            return;
        }
        
        const features = data.features_moyennes || {};
        
        const statsHtml = `
            <div class="stat-card">
                <div class="stat-label">Vidéos Analysées</div>
                <div class="stat-value">${data.total || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Score Moyen</div>
                <div class="stat-value">${data.avg_score || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Longueur Moyenne</div>
                <div class="stat-value">${features.longueur || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Emojis Moyens</div>
                <div class="stat-value">${features.emojis || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Hashtags Moyens</div>
                <div class="stat-value">${features.hashtags || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Exclamations Moyennes</div>
                <div class="stat-value">${features.exclamations || 0}</div>
            </div>
        `;
        
        document.getElementById('stats-container').innerHTML = statsHtml;
    } catch (error) {
        console.error('Erreur stats:', error);
        document.getElementById('stats-container').innerHTML = 
            '<div class="loading">Erreur lors du chargement des statistiques</div>';
    }
}

async function loadVideos() {
    try {
        const response = await fetch('/api/top/100'); // Fetch more for client-side sorting
        const videos = await response.json();
        
        currentVideos = videos;
        renderVideos(videos.slice(0, currentLimit));
    } catch (error) {
        console.error('Erreur videos:', error);
        document.getElementById('videos-container').innerHTML = 
            '<div class="loading">Erreur lors du chargement des vidéos</div>';
    }
}

async function loadData() {
    await Promise.all([loadStats(), loadVideos()]);
}

async function startScraping() {
    const startBtn = document.getElementById('start-scrape-btn');
    const stopBtn = document.getElementById('stop-scrape-btn');
    const statusBar = document.getElementById('status-bar');
    
    console.log('[DEBUG] startScraping called');
    console.log('[DEBUG] Elements:', { startBtn, stopBtn, statusBar });
    
    try {
        // Disable start button, show stop button
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.textContent = 'Démarrage...';
        }
        if (stopBtn) stopBtn.style.display = 'inline-block';
        
        console.log('[DEBUG] Calling /api/scrape...');
        const response = await fetch('/api/scrape', { method: 'POST' });
        const data = await response.json();
        
        console.log('[DEBUG] Scrape API response:', data);
        
        if (data.status === 'started') {
            showNotification('Analyse démarrée avec succès', 'success');
            
            // Show status bar
            if (statusBar) {
                console.log('[DEBUG] Showing status bar');
                statusBar.style.display = 'block';
            } else {
                console.error('[DEBUG] Status bar element not found!');
            }
            
            // Update status
            updateStatus('Scraping en cours...', 'Collecte des données YouTube');
            
            // Start polling for status
            startStatusPolling();
        } else {
            console.error('[DEBUG] Unexpected response status:', data);
            showNotification('Erreur: ' + data.message, 'error');
            resetButtons();
        }
    } catch (error) {
        console.error('Erreur scraping:', error);
        showNotification('Erreur lors du lancement', 'error');
        resetButtons();
    }
}

let statusPollInterval = null;

function startStatusPolling() {
    if (statusPollInterval) clearInterval(statusPollInterval);
    
    statusPollInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/scrape/status');
            const data = await response.json();
            
            console.log('[DEBUG] Status poll response:', data);
            
            if (data.scraping) {
                // Ensure status bar is visible
                const statusBar = document.getElementById('status-bar');
                if (statusBar && statusBar.style.display === 'none') {
                    console.log('[DEBUG] Making status bar visible');
                    statusBar.style.display = 'block';
                }
                
                // Update progress if available
                if (data.countries_total && data.countries_done !== undefined) {
                    const percent = Math.round((data.countries_done / data.countries_total) * 100);
                    const progressText = `${data.countries_done}/${data.countries_total} pays analysés - ${data.items_scraped || 0} vidéos`;
                    console.log('[DEBUG] Updating progress:', percent, progressText);
                    updateProgress(percent, progressText);
                } else if (data.items_scraped) {
                    const progressText = `${data.items_scraped} vidéos collectées`;
                    console.log('[DEBUG] Updating progress (items only):', progressText);
                    updateProgress(0, progressText);
                }
                
                // Update details
                if (data.current_country) {
                    updateStatus('Analyse en cours...', `Pays: ${data.current_country}`);
                } else {
                    updateStatus('Analyse en cours...', 'Collecte des données YouTube');
                }
                
                // Only refresh data every 10 seconds during scraping to reduce load
                const now = Date.now();
                if (!window.lastDataRefresh || (now - window.lastDataRefresh) > 10000) {
                    await loadVideos();
                    window.lastDataRefresh = now;
                }
            } else {
                // Scraping finished
                console.log('[DEBUG] Scraping finished, stopping polling');
                clearInterval(statusPollInterval);
                statusPollInterval = null;
                
                // Show completion message
                if (data.status === 'finished' || data.items_scraped > 0) {
                    showNotification(`Scraping terminé! ${data.items_scraped || 0} vidéos collectées`, 'success');
                }
                
                // Final data refresh
                await loadVideos();
                await loadStats();
                
                // Hide status bar and reset buttons
                hideStatusBar();
                resetButtons();
            }
        } catch (error) {
            console.error('Status poll error:', error);
        }
    }, 3000); // Poll every 3 seconds instead of 2
}

function updateStatus(title, details) {
    const statusTitle = document.querySelector('.status-title');
    const statusDetails = document.getElementById('status-details');
    if (statusTitle) statusTitle.textContent = title;
    if (statusDetails) statusDetails.textContent = details;
}

function updateProgress(percent, text) {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    console.log('[DEBUG] updateProgress called:', {percent, text, progressFill, progressText});
    if (progressFill) progressFill.style.width = percent + '%';
    if (progressText) progressText.textContent = text || `${percent}%`;
}

function hideStatusBar() {
    const statusBar = document.getElementById('status-bar');
    if (statusBar) {
        statusBar.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => statusBar.style.display = 'none', 300);
    }
}

function resetButtons() {
    const startBtn = document.getElementById('start-scrape-btn');
    const stopBtn = document.getElementById('stop-scrape-btn');
    if (startBtn) {
        startBtn.disabled = false;
        startBtn.textContent = 'Démarrer l\'Analyse';
    }
    if (stopBtn) stopBtn.style.display = 'none';
}

async function stopScraping() {
    if (!confirm('Êtes-vous sûr de vouloir arrêter l\'analyse en cours ?')) {
        return;
    }
    
    const stopBtn = document.getElementById('stop-scrape-btn');
    const originalText = stopBtn ? stopBtn.textContent : '';
    if (stopBtn) {
        stopBtn.disabled = true;
        stopBtn.textContent = 'Arrêt...';
    }
    
    try {
        const response = await fetch('/api/scrape/stop', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'stopped') {
            if (statusPollInterval) {
                clearInterval(statusPollInterval);
                statusPollInterval = null;
            }
            hideStatusBar();
            resetButtons();
            
            // Wait and reload data
            setTimeout(async () => {
                await loadData();
                showNotification('Analyse arrêtée. Données chargées.', 'info');
            }, 1000);
        } else {
            showNotification('Erreur: ' + (data.message || 'Impossible d\'arrêter'), 'error');
            if (stopBtn) {
                stopBtn.disabled = false;
                stopBtn.textContent = originalText;
            }
        }
    } catch (error) {
        console.error('Erreur stop:', error);
        showNotification('Erreur lors de l\'arrêt', 'error');
        if (stopBtn) {
            stopBtn.disabled = false;
            stopBtn.textContent = originalText;
        }
    }
}

function toggleStatusDetails() {
    const extended = document.getElementById('status-extended');
    const icon = document.getElementById('toggle-icon');
    if (extended && icon) {
        if (extended.style.display === 'none') {
            extended.style.display = 'block';
            icon.textContent = '▲';
        } else {
            extended.style.display = 'none';
            icon.textContent = '▼';
        }
    }
}

// Sorting and filtering functions
let currentVideos = [];
let currentLimit = 20;

function sortVideos(sortBy) {
    if (!currentVideos.length) return;
    
    let sorted = [...currentVideos];
    switch(sortBy) {
        case 'score':
            sorted.sort((a, b) => (b.score_psychologique || 0) - (a.score_psychologique || 0));
            break;
        case 'views':
            sorted.sort((a, b) => (b.vues || 0) - (a.vues || 0));
            break;
        case 'recent':
            sorted.sort((a, b) => new Date(b.date_scraping || 0) - new Date(a.date_scraping || 0));
            break;
    }
    
    renderVideos(sorted.slice(0, currentLimit));
}

function updateLimit(limit) {
    currentLimit = parseInt(limit) || 20;
    const select = document.getElementById('sort-select');
    if (select) {
        sortVideos(select.value);
    }
}

function renderVideos(videos) {
    const container = document.getElementById('videos-container');
    if (!container) return;
    
    if (videos.length === 0) {
        container.innerHTML = '<div class="loading">Aucune vidéo disponible. Lancez une analyse.</div>';
        return;
    }
    
    const videosHtml = videos.map((video, index) => {
        const features = video.features || {};
        const score = video.score_psychologique || 0;
        const scoreClass = getScoreClass(score);
        
        return `
            <div class="video-card">
                <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:15px;">
                    <div style="flex: 1;">
                        <span class="video-rank">#${index + 1}</span>
                        <span class="video-title">${video.titre}</span>
                    </div>
                    <span class="score-badge ${scoreClass}">${score}</span>
                </div>
                
                <div class="video-meta-container">
                    <div class="meta-item-styled">
                        <span class="meta-label">Canal</span>
                        <span class="meta-value">${video.canal || 'Inconnu'}</span>
                    </div>
                    <div class="meta-item-styled">
                        <span class="meta-label">Vues</span>
                        <span class="meta-value">${formatNumber(video.vues || 0)}</span>
                    </div>
                    <div class="meta-item-styled">
                        <span class="meta-label">Durée</span>
                        <span class="meta-value">${formatDuration(video.duree || '0')}</span>
                    </div>
                    <div class="meta-item-styled">
                        <span class="meta-label">Publié</span>
                        <span class="meta-value">${video.heure || 'N/A'}</span>
                    </div>
                    <div class="meta-item-styled">
                        <span class="meta-label">Pays</span>
                        <span class="meta-value">${video.pays || 'World'}</span>
                    </div>
                </div>
                
                <div class="features-grid">
                    <div class="feature-tag">
                        <div class="feature-value">${features.longueur || 0}</div>
                        <div class="feature-label">Caractères</div>
                    </div>
                    <div class="feature-tag">
                        <div class="feature-value">${features.nb_emojis || 0}</div>
                        <div class="feature-label">Emojis</div>
                    </div>
                    <div class="feature-tag">
                        <div class="feature-value">${features.nb_hashtags || 0}</div>
                        <div class="feature-label">Hashtags</div>
                    </div>
                    <div class="feature-tag">
                        <div class="feature-value">${features.nb_exclamations || 0}</div>
                        <div class="feature-label">Exclamations</div>
                    </div>
                    <div class="feature-tag">
                        <div class="feature-value">${features.nb_questions || 0}</div>
                        <div class="feature-label">Questions</div>
                    </div>
                    <div class="feature-tag">
                        <div class="feature-value">${(features.pourcentage_majuscules || 0).toFixed(1)}%</div>
                        <div class="feature-label">Majuscules</div>
                    </div>
                </div>
                
                ${video.url ? `<div style="margin-top:15px;"><a href="${video.url}" target="_blank" class="video-link">Voir la vidéo</a></div>` : ''}
            </div>
        `;
    }).join('');
    
    container.innerHTML = videosHtml;
}

// Start scraping and wait endpoint
async function startScrapingAndWait() {
    const statusDiv = document.getElementById('scraping-status');
    const videosDiv = document.getElementById('videos-container');

    try {
        statusDiv.style.display = 'block';
        videosDiv.innerHTML = '<div class="loading">Scraping en cours, veuillez patienter...</div>';

        // show progress modal and logs while we wait
        startProgressModal();
        startLogStream();

        const headers = { 'Content-Type': 'application/json' };
        const token = localStorage.getItem('scrape_token');
        if (token) headers['X-Scrape-Token'] = token;
        const response = await fetch('/api/scrape/wait', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ timeout: 600 })
        });

        const data = await response.json();
        statusDiv.style.display = 'none';
        stopProgressModal();
        stopLogStream();

        if (data.finished) {
            await loadData();
            alert('Scraping termine. ' + data.videos_count + ' videos charges.');
        } else {
            // timed out but still running
            await loadData();
            alert('Le scraping n\'a pas termine avant le timeout. Il tourne toujours en arriere-plan.');
        }
    } catch (err) {
        console.error('Erreur wait-scrape', err);
        statusDiv.style.display = 'none';
        alert('Erreur lors du lancement du scraping');
        await loadData();
    }
}

// Logs via SSE
let logEventSource = null;
function startLogStream() {
    document.getElementById('log-area').style.display = 'block';
    const logContent = document.getElementById('log-content');
    logContent.textContent = '';
    try {
        if (typeof(EventSource) !== 'undefined') {
            // Default to active run logs; apps can call startRunLog(runId) to stream a specific run
            logEventSource = new EventSource('/api/scrape/logs');
            logEventSource.onmessage = function(e) {
                logContent.textContent += e.data + '\n';
                logContent.parentElement.scrollTop = logContent.parentElement.scrollHeight;
            };
            logEventSource.onerror = function(e) {
                // don't spam console
            };
        }
    } catch (e) {
        console.error('SSE not available', e);
    }
}

function toggleLogs() {
    const area = document.getElementById('log-area');
    const modal = document.getElementById('progress-modal');
    const statusDiv = document.getElementById('scraping-status');
    const btn = document.getElementById('toggle-logs-btn');
    if (!area || !btn) return;
    if (area.style.display === 'none' || area.style.display === '') {
        // show all
        area.style.display = 'block';
        if (modal) modal.style.display = 'flex';
        if (statusDiv) statusDiv.style.display = 'block';
        btn.textContent = 'Masquer les logs';
    } else {
        // hide all
        area.style.display = 'none';
        if (modal) modal.style.display = 'none';
        if (statusDiv) statusDiv.style.display = 'none';
        btn.textContent = 'Afficher les logs';
    }
}

// Start streaming logs for a specific run id
let runLogSource = null;
function startRunLog(runId) {
    stopRunLog();
    document.getElementById('log-area').style.display = 'block';
    const logContent = document.getElementById('log-content');
    logContent.textContent = '';
    if (typeof(EventSource) !== 'undefined') {
        runLogSource = new EventSource(`/api/runs/${runId}/logs`);
        runLogSource.onmessage = function(e) {
            logContent.textContent += e.data + '\n';
            logContent.parentElement.scrollTop = logContent.parentElement.scrollHeight;
        };
    }
}

function stopRunLog() {
    if (runLogSource) {
        runLogSource.close();
        runLogSource = null;
    }
}

// Progress SSE for a specific run
let progressEventSource = null;
function startRunProgress(runId) {
    stopRunProgress();
    if (typeof(EventSource) !== 'undefined') {
        progressEventSource = new EventSource(`/api/scrape/progress-sse?run=${runId}`);
        progressEventSource.onmessage = function(e) {
            try {
                const data = JSON.parse(e.data);
                updateProgressUI(data || {});
            } catch (err) {
                // ignore parse
            }
        };
    }
}

function stopRunProgress() {
    if (progressEventSource) {
        progressEventSource.close();
        progressEventSource = null;
    }
}

// Load runs list and render
async function loadRuns() {
    try {
        const resp = await fetch('/api/runs');
        const runs = await resp.json();
        const list = document.getElementById('runs-list');
        list.innerHTML = '';
        if (!runs || runs.length === 0) {
            list.innerHTML = '<div style="color:#666;">Aucun run disponible</div>';
            return;
        }
        runs.forEach(r => {
            const el = document.createElement('div');
            el.style.border = '1px solid #e5e7eb';
            el.style.padding = '8px';
            el.style.borderRadius = '6px';
            el.style.minWidth = '220px';
            el.style.background = '#fff';
            el.innerHTML = `<div style="font-weight:600;">${r.run_id || r.run}</div><div style="font-size:0.9em;color:#666">${r.started_at || ''}</div>`;
            const btnView = document.createElement('button');
            btnView.textContent = 'Voir logs';
            btnView.className = 'refresh-btn';
            btnView.style.marginTop = '8px';
            btnView.onclick = () => {
                // show log area and stream that run
                document.getElementById('scraping-status').style.display = 'block';
                startRunLog(r.run_id);
                startRunProgress(r.run_id);
            };
            el.appendChild(btnView);
            list.appendChild(el);
        });
    } catch (e) {
        console.error('Erreur loadRuns', e);
    }
}

// Login modal controls
function openLoginModal() { document.getElementById('login-modal').style.display = 'flex'; }
function closeLoginModal() { document.getElementById('login-modal').style.display = 'none'; }
function submitLogin() {
    const token = document.getElementById('ui-token-input').value;
    if (!token) return alert('Entrez un token');
    localStorage.setItem('scrape_token', token);
    closeLoginModal();
    alert('Token enregistré localement');
}

function stopLogStream() {
    if (logEventSource) {
        logEventSource.close();
        logEventSource = null;
    }
    document.getElementById('log-area').style.display = 'none';
}

// Progress polling (reads scrape_status.json)
let progressInterval = null;
function startProgressModal() {
    document.getElementById('progress-modal').style.display = 'flex';
    updateProgressUI({status: 'running', items_scraped: 0});
    if (progressInterval) clearInterval(progressInterval);
    progressInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/scrape/progress');
            const data = await res.json();
            updateProgressUI(data || {});
            if (data && data.status === 'finished') {
                stopProgressModal();
            }
        } catch (e) {
            // ignore
        }
    }, 1000);
}

function stopProgressModal() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    document.getElementById('progress-modal').style.display = 'none';
}

function updateProgressUI(data) {
    const bar = document.getElementById('progress-bar');
    const text = document.getElementById('progress-text');
    let percent = 0;
    // update small indicator with items scraped
    const ind = document.getElementById('scrape-indicator');
    if (data.countries_total && data.countries_total > 0) {
        percent = Math.round(( (data.countries_done || 0) / data.countries_total ) * 100);
        text.textContent = `Pays: ${data.countries_done || 0}/${data.countries_total} — Videos: ${data.items_scraped || 0}`;
        if (ind) { ind.style.display='inline'; ind.textContent = `Scraping: ${data.items_scraped || 0} vidéos`; }
    } else if (data.items_scraped) {
        // unknown total — show items count
        percent = Math.min(99, data.items_scraped % 100); // pseudo-progress
        text.textContent = `Videos scrapees: ${data.items_scraped}`;
        if (ind) { ind.style.display='inline'; ind.textContent = `Scraping: ${data.items_scraped || 0} vidéos`; }
    } else {
        text.textContent = 'Initialisation...';
    }
    bar.style.width = percent + '%';
}

function closeProgressModal() {
    stopProgressModal();
}

async function downloadLogs() {
    try {
        const resp = await fetch('/api/scrape/logs/download');
        if (!resp.ok) {
            alert('Aucun log disponible');
            return;
        }
        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'scrape_output.log';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (e) {
        console.error('Erreur download logs', e);
        alert('Erreur lors du téléchargement des logs');
    }
}

// Charger les données au démarrage
document.addEventListener('DOMContentLoaded', function() {
    loadData();
});


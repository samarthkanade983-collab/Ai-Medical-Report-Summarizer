document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname === '/history') loadHistory();
    initMedicalChat();
});

const analyzeForm = document.getElementById('analyze-form');
const fileInput = document.getElementById('pdf-upload');

if (fileInput) {
    fileInput.addEventListener('change', (e) => {
        const fileName = e.target.files[0] ? e.target.files[0].name : "Click or Drag to Upload Report (PDF, JPG, PNG)";
        const labelSpan = e.target.parentElement.querySelector('span');
        if (labelSpan) labelSpan.textContent = fileName;
    });
}


if (analyzeForm) {
    analyzeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fileInput = document.getElementById('pdf-upload').files[0];
        const textInput = document.getElementById('text-input').value.trim();
        const resultsDiv = document.getElementById('results');
        const loadingDiv = document.getElementById('loading');
        const errorMsg = document.getElementById('error-msg');
        
        if (!fileInput && !textInput) {
            errorMsg.textContent = 'Please upload a PDF or paste report text.';
            errorMsg.classList.remove('hidden');
            return;
        }

        errorMsg.classList.add('hidden');
        resultsDiv.classList.add('hidden');
        loadingDiv.classList.remove('hidden');
        
        const formData = new FormData();
        if (fileInput) formData.append('pdf', fileInput);
        if (textInput) formData.append('text', textInput);
        
        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });

            const ct = response.headers.get('content-type') || '';
            let data;
            if (ct.includes('application/json')) {
                data = await response.json();
            } else {
                const raw = await response.text();
                throw new Error(
                    response.status >= 500
                        ? `Server error (${response.status}). The page may have returned HTML instead of JSON.`
                        : `Unexpected response (${response.status}): ${raw.slice(0, 120)}`
                );
            }

            if (!response.ok) {
                errorMsg.textContent = data.error || 'Server error occurred.';
                errorMsg.classList.remove('hidden');
                loadingDiv.classList.add('hidden');
                return;
            }
            
            // Populate Details
            document.getElementById('nlp-summary').textContent = data.nlp_summary || 'No text to summarize.';
            document.getElementById('rule-summary').textContent = data.rule_summary || 'No rules matched.';
            
            // Issues
            populateList('issues-list', data.issues, 'times-circle');
            
            // Explanations
            populateList('explanations-list', data.explanations, 'info-circle');

            // Diseases
            populateList('diseases-list', data.diseases, 'virus');

            // Advice
            populateList('advice-list', data.advice, 'check-circle');
            
            // Probabilistic Analysis (NB + RF + GMM + HMM)
            window.currentProbabilisticAnalysis = data.probabilistic_analysis || {};
            if (data.probabilistic_analysis) {
                const pData = data.probabilistic_analysis;
                const dept = pData.department || {};
                document.getElementById('predDepartment').textContent = dept.predicted || '—';
                document.getElementById('deptConfidence').textContent = `${dept.confidence || ''} Confidence`;
                document.getElementById('deptProbList').innerHTML = (dept.probabilities || [])
                    .map(p => `<strong>${p.department}:</strong> ${p.probability}%`)
                    .join('<br>');

                const dr = pData.disease_risk || {};
                const ens = dr.ensemble_detail || {};
                const ensLine = document.getElementById('ensemble-detail-line');
                if (ensLine) {
                    if (ens.method && ens.method !== 'N/A') {
                        ensLine.textContent = `${ens.method}. Peaks — NB: ${ens.naive_bayes_peak}, RF: ${ens.random_forest_peak}.`;
                    } else ensLine.textContent = '';
                }

                document.getElementById('predRisk').textContent = dr.primary_risk || '—';
                document.getElementById('riskProbabilityPercent').textContent =
                    dr.max_probability === 'N/A' || dr.max_probability === undefined
                        ? 'N/A'
                        : `${dr.max_probability}% Probable`;
                document.getElementById('riskProbList').innerHTML = (dr.all_probabilities || [])
                    .map(p => `<strong>${p.risk_category}:</strong> ${p.probability}%`)
                    .join('<br>');

                const rf = dr.random_forest || {};
                const rfNote = document.getElementById('rf-note');
                const rfList = document.getElementById('rfProbList');
                if (rfNote) rfNote.textContent = rf.tree_ensemble_note || '';
                if (rfList) {
                    rfList.innerHTML = (rf.top_probabilities || [])
                        .map(p => `<strong>${p.risk_category}:</strong> ${p.probability}%`)
                        .join('<br>') || '<span class="text-muted">—</span>';
                }

                const hmm = dr.hidden_markov || {};
                const hmmN = document.getElementById('hmm-block-note');
                const hmmP = document.getElementById('hmmPrimaryRisk');
                const hmmL = document.getElementById('hmmPathList');
                if (hmmN) hmmN.textContent = hmm.note || '';
                if (hmmP) hmmP.textContent = hmm.available ? (hmm.primary_risk || '—') : '—';
                if (hmmL) {
                    hmmL.innerHTML = (hmm.path_summary || [])
                        .map(p => `<strong>${p.risk_category}:</strong> ${p.along_path_percent}% of sequence`)
                        .join('<br>') || '<span class="text-muted">—</span>';
                }

                const gmm = dr.gmm_mixture || {};
                const gmmNoteEl = document.getElementById('gmm-note');
                const gmmPrimary = document.getElementById('gmmPrimary');
                const gmmConf = document.getElementById('gmmConfidence');
                const gmmList = document.getElementById('gmmProbList');
                if (gmmNoteEl) gmmNoteEl.textContent = gmm.note || '';
                if (gmmPrimary) gmmPrimary.textContent = gmm.primary_profile || '—';
                if (gmmConf) {
                    gmmConf.textContent =
                        gmm.profile_confidence_percent != null && gmm.profile_confidence_percent !== ''
                            ? `${gmm.profile_confidence_percent}% mixture`
                            : '';
                }
                if (gmmList) {
                    gmmList.innerHTML = (gmm.mixture_probabilities || [])
                        .map(p => `<strong>${p.risk_profile}:</strong> ${p.probability}%`)
                        .join('<br>') || '<span class="text-muted">—</span>';
                }
            }
            
            // Render Graph
            renderChart(data.values, data.abnormal_params);
            
            // Chat context (labs + full probabilistic payload)
            window.currentMedicalValues = data.values;
            window.currentDiseases = data.diseases;
            window.medicalChatHistory = [];
            window.lastAssistantReplyHtml = '';
            window.lastAnalysisData = data;

            const scoreEl = document.getElementById('wellness-score');
            if (scoreEl) {
                const abnormalCount = (data.abnormal_params || []).length;
                const total = Math.max(1, Object.keys(data.values || {}).length);
                const score = Math.max(0, Math.round(((total - abnormalCount) / total) * 100));
                scoreEl.textContent = `Wellness score: ${score}/100`;
                scoreEl.className = score >= 80 ? 'badge none' : 'badge';
            }

            loadingDiv.classList.add('hidden');
            resultsDiv.classList.remove('hidden');
            resultsDiv.scrollIntoView({behavior: 'smooth'});
            
        } catch (err) {
            console.error("Analysis Error:", err);
            errorMsg.textContent = 'An error occurred while fetching analysis (check console).';
            errorMsg.classList.remove('hidden');
            loadingDiv.classList.add('hidden');
        }
    });

    // Populate helper
    function populateList(id, items, icon) {
        const el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = '';
        if (items && items.length > 0) {
            items.forEach(item => {
                el.innerHTML += `<div class="issue-item" style="${icon === 'check-circle' ? 'background: var(--success-bg); color: var(--success);' : ''}"><i class="fa-solid fa-${icon}"></i> ${item}</div>`;
            });
        } else {
            el.innerHTML = '<div class="text-muted" style="padding:1rem;">None detected.</div>';
        }
    }

    // Dynamic Chart rendering
    function renderChart(values, abnormalParams) {
        const ctx = document.getElementById('medical-chart');
        if (!ctx) return;
        
        if (window.medicalChartInstance) {
            window.medicalChartInstance.destroy();
        }
        
        const labels = Object.keys(values);
        const dataPoints = Object.values(values);
        if (labels.length === 0) return;

        // Dynamic highlight abnormal values in red
        const bgColors = labels.map(label => 
            abnormalParams && abnormalParams.includes(label) 
                ? 'rgba(239, 68, 68, 0.8)' 
                : 'rgba(16, 185, 129, 0.8)'
        );

        window.medicalChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Extracted Value',
                    data: dataPoints,
                    backgroundColor: bgColors,
                    borderRadius: 8,
                    barPercentage: 0.6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(148,163,184,0.1)' } },
                    x: { grid: { display: false } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    const copySummaryBtn = document.getElementById('copy-summary-btn');
    if (copySummaryBtn) {
        copySummaryBtn.addEventListener('click', async () => {
            const data = window.lastAnalysisData || {};
            const text = [
                `Rule summary: ${data.rule_summary || ''}`,
                `Clinical summary: ${data.nlp_summary || ''}`,
                `Issues: ${(data.issues || []).join(', ') || 'None'}`,
                `Advice: ${(data.advice || []).join(', ') || 'None'}`
            ].join('\n');
            try {
                await navigator.clipboard.writeText(text);
                copySummaryBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied';
                setTimeout(() => {
                    copySummaryBtn.innerHTML = '<i class="fa-solid fa-copy"></i> Copy summary';
                }, 1200);
            } catch {
                copySummaryBtn.innerHTML = '<i class="fa-solid fa-xmark"></i> Copy failed';
            }
        });
    }
}

function initMedicalChat() {
    if (window._medicalChatInited) return;
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatClearBtn = document.getElementById('chat-clear-btn');
    if (!chatMessages || !chatInput || !chatSendBtn) return;

    window._medicalChatInited = true;
    window.medicalChatHistory = window.medicalChatHistory || [];
    window.currentMedicalValues = window.currentMedicalValues || {};
    window.currentDiseases = window.currentDiseases || [];
    window.currentProbabilisticAnalysis = window.currentProbabilisticAnalysis || {};

    function appendChatBubble(role, html, options) {
        const wrap = document.createElement('div');
        const isUser = role === 'user';
        wrap.className = isUser ? 'genz-chat-bubble genz-chat-bubble--user' : 'genz-chat-bubble genz-chat-bubble--assistant';
        const meta = isUser ? 'You' : 'Assistant';
        wrap.innerHTML = `<span class="genz-chat-meta">${meta}</span><div class="genz-chat-body">${html}</div>`;
        chatMessages.appendChild(wrap);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        if (!isUser && !(options && options.skipTrackLast)) {
            window.lastAssistantReplyHtml = html;
        }
    }

    async function sendChatMessage() {
        const text = chatInput.value.trim();
        if (!text) return;
        chatInput.value = '';
        appendChatBubble('user', text.replace(/</g, '&lt;'));
        chatSendBtn.disabled = true;
        const typing = document.createElement('div');
        typing.id = 'chat-typing';
        typing.className = 'genz-typing';
        typing.textContent = 'Thinking…';
        chatMessages.appendChild(typing);

        const simpleModeEl = document.getElementById('chat-simple-mode');

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({
                    message: text,
                    simplify: !!(simpleModeEl && simpleModeEl.checked),
                    history: window.medicalChatHistory || [],
                    values: window.currentMedicalValues || {},
                    diseases: window.currentDiseases || [],
                    probabilistic_analysis: window.currentProbabilisticAnalysis || {}
                })
            });
            const aiData = await res.json();
            document.getElementById('chat-typing')?.remove();
            if (!res.ok) {
                appendChatBubble('assistant', `<span class="text-danger">${(aiData.error || 'Request failed')}</span>`, { skipTrackLast: true });
                return;
            }
            window.medicalChatHistory = (window.medicalChatHistory || []).concat([
                { role: 'user', content: text },
                { role: 'assistant', content: aiData.response || '' }
            ]);
            appendChatBubble('assistant', aiData.response || '');
        } catch (e) {
            document.getElementById('chat-typing')?.remove();
            appendChatBubble('assistant', '<span class="text-danger">Could not reach the server.</span>', { skipTrackLast: true });
        } finally {
            chatSendBtn.disabled = false;
        }
    }

    const simplifyLastBtn = document.getElementById('chat-simplify-last-btn');
    async function simplifyLastReply() {
        if (!simplifyLastBtn || !window.lastAssistantReplyHtml) {
            const tip = document.createElement('div');
            tip.className = 'genz-typing';
            tip.textContent = 'Send a message first — then tap Simplify ✂️';
            chatMessages.appendChild(tip);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            setTimeout(() => tip.remove(), 3200);
            return;
        }
        simplifyLastBtn.disabled = true;
        const typing = document.createElement('div');
        typing.className = 'genz-typing';
        typing.id = 'simplify-typing';
        typing.textContent = 'Simplifying…';
        chatMessages.appendChild(typing);

        try {
            const res = await fetch('/api/simplify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({ text: window.lastAssistantReplyHtml })
            });
            const data = await res.json();
            document.getElementById('simplify-typing')?.remove();
            if (!res.ok) {
                appendChatBubble('assistant', `<span class="text-danger">${data.error || 'Simplify failed'}</span>`, { skipTrackLast: true });
                return;
            }
            appendChatBubble('assistant', data.response || '');
            window.medicalChatHistory = (window.medicalChatHistory || []).concat([
                { role: 'user', content: '[Simplify last reply]' },
                { role: 'assistant', content: data.response || '' }
            ]);
        } catch (err) {
            document.getElementById('simplify-typing')?.remove();
            appendChatBubble('assistant', '<span class="text-danger">Could not simplify right now.</span>', { skipTrackLast: true });
        } finally {
            simplifyLastBtn.disabled = false;
        }
    }

    chatSendBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter') {
            ev.preventDefault();
            sendChatMessage();
        }
    });
    if (simplifyLastBtn) simplifyLastBtn.addEventListener('click', simplifyLastReply);
    if (chatClearBtn) {
        chatClearBtn.addEventListener('click', () => {
            window.medicalChatHistory = [];
            window.lastAssistantReplyHtml = '';
            chatMessages.innerHTML = '';
        });
    }
}

// History loading
async function loadHistory() {
    const list = document.getElementById('history-list');
    if (!list) return;

    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        
        list.innerHTML = '';
        if (data.length === 0) {
            list.innerHTML = '<div class="text-center text-muted" style="padding: 2rem;">No analysis history found.</div>';
            return;
        }
        
        data.forEach(item => {
            const hItems = document.createElement('div');
            hItems.className = 'history-item fade-in';
            
            let issuesHTML = item.issues.map(i => `<span class="badge">${i}</span>`).join('');
            if(!issuesHTML) issuesHTML = '<span class="badge none">No Risks</span>';
            
            let diseasesHTML = item.diseases.map(d => `<span class="badge" style="background:var(--warning); color:white;">${d}</span>`).join('');
            
            hItems.innerHTML = `
                <div class="history-item-header">
                    <div class="history-date"><i class="fa-regular fa-clock"></i> ${item.date_time}</div>
                    <button class="btn-danger" style="padding: 0.4rem 0.8rem;" onclick="deleteRecord(${item.id})"><i class="fa-solid fa-trash"></i></button>
                </div>
                <div style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 0.5rem;">
                    <strong>Summary: </strong> ${item.summary}
                </div>
                <div style="margin-bottom: 0.5rem;">
                    ${issuesHTML} ${diseasesHTML}
                </div>
            `;
            list.appendChild(hItems);
        });
    } catch(e) {
        list.innerHTML = '<div class="text-danger">Failed to load history records.</div>';
    }
}

window.deleteRecord = async (id) => {
    if(!confirm("Delete this record?")) return;
    await fetch('/api/history/'+id, { method: 'DELETE' });
    loadHistory();
};

window.clearHistory = async () => {
    if(!confirm("Clear all history?")) return;
    await fetch('/api/history/clear', { method: 'DELETE' });
    loadHistory();
};

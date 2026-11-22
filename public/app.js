/**
 * MarketPulse Multi-Agent Client Application
 * Features:
 *  - Real-time Server-Sent Events (SSE) streaming
 *  - Reactive agent pipeline visualizer
 *  - Dynamic tab navigation and interactive SWOT / Competitor cards
 *  - Built-in zero-dependency Markdown renderer
 *  - Export to Markdown and Print / PDF
 *  - Local storage persistence for theme and provider settings
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const queryInput = document.getElementById('queryInput');
  const runResearchBtn = document.getElementById('runResearchBtn');
  const exampleChips = document.querySelectorAll('.chip');
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const themeIcon = document.getElementById('themeIcon');

  const providerBadgeBtn = document.getElementById('providerBadgeBtn');
  const currentEngineLabel = document.getElementById('currentEngineLabel');
  const settingsModal = document.getElementById('settingsModal');
  const closeSettingsBtn = document.getElementById('closeSettingsBtn');
  const cancelSettingsBtn = document.getElementById('cancelSettingsBtn');
  const saveSettingsBtn = document.getElementById('saveSettingsBtn');
  const providerSelect = document.getElementById('providerSelect');
  const apiKeyGroup = document.getElementById('apiKeyGroup');
  const apiKeyInput = document.getElementById('apiKeyInput');
  const modelGroup = document.getElementById('modelGroup');
  const modelInput = document.getElementById('modelInput');

  const pipelineSection = document.getElementById('pipelineSection');
  const workflowStateBadge = document.getElementById('workflowStateBadge');
  const progressText = document.getElementById('progressText');
  const progressFill = document.getElementById('progressFill');
  const tickerFeed = document.getElementById('tickerFeed');

  const resultsSection = document.getElementById('resultsSection');
  const resultTitle = document.getElementById('resultTitle');
  const resultGeography = document.getElementById('resultGeography');
  const resultIndustry = document.getElementById('resultIndustry');
  const resultConfidence = document.getElementById('resultConfidence');
  const resultQueryDisplay = document.getElementById('resultQueryDisplay');

  const kpiSam = document.getElementById('kpiSam');
  const kpiTam = document.getElementById('kpiTam');
  const kpiCagr = document.getElementById('kpiCagr');
  const kpiOrders = document.getElementById('kpiOrders');
  const kpiAov = document.getElementById('kpiAov');
  const kpiPayments = document.getElementById('kpiPayments');

  const copyMarkdownBtn = document.getElementById('copyMarkdownBtn');
  const downloadMdBtn = document.getElementById('downloadMdBtn');
  const printReportBtn = document.getElementById('printReportBtn');

  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  const executiveContent = document.getElementById('executiveContent');
  const playersContainer = document.getElementById('playersContainer');
  const swotStrengths = document.getElementById('swotStrengths');
  const swotWeaknesses = document.getElementById('swotWeaknesses');
  const swotOpportunities = document.getElementById('swotOpportunities');
  const swotThreats = document.getElementById('swotThreats');
  const regulatoryContainer = document.getElementById('regulatoryContainer');
  const agentOutputsAccordion = document.getElementById('agentOutputsAccordion');
  const criticContainer = document.getElementById('criticContainer');

  // State
  let currentBrief = null;
  let activeEventSource = null;
  const agentOrder = ['planner', 'market_analyst', 'competitor_swot', 'risk_ops', 'synthesis', 'critic'];
  let completedCount = 0;

  // Local Storage Settings
  const savedSettings = JSON.parse(localStorage.getItem('marketpulse_settings') || '{}');
  let currentProvider = savedSettings.provider || 'simulated';
  let currentApiKey = savedSettings.apiKey || '';
  let currentModel = savedSettings.model || '';

  // Theme Init
  const savedTheme = localStorage.getItem('marketpulse_theme') || 'dark';
  applyTheme(savedTheme);

  function applyTheme(theme) {
    if (theme === 'light') {
      document.body.classList.remove('theme-dark');
      document.body.classList.add('theme-light');
      themeIcon.textContent = '🌙';
    } else {
      document.body.classList.remove('theme-light');
      document.body.classList.add('theme-dark');
      themeIcon.textContent = '☀️';
    }
    localStorage.setItem('marketpulse_theme', theme);
  }

  themeToggleBtn.addEventListener('click', () => {
    const isLight = document.body.classList.contains('theme-light');
    applyTheme(isLight ? 'dark' : 'light');
  });

  // Update Provider Label
  function updateProviderBadge() {
    if (currentProvider === 'simulated') {
      currentEngineLabel.textContent = 'Autonomous Engine (Ready)';
    } else {
      currentEngineLabel.textContent = `${currentProvider.toUpperCase()} (${currentApiKey ? 'Key Configured' : 'No Key'})`;
    }
  }
  updateProviderBadge();

  // Settings Modal Handlers
  providerBadgeBtn.addEventListener('click', () => {
    providerSelect.value = currentProvider;
    apiKeyInput.value = currentApiKey;
    modelInput.value = currentModel;
    toggleKeyInputs();
    settingsModal.classList.remove('hidden');
  });

  function toggleKeyInputs() {
    const val = providerSelect.value;
    const needsKey = (val === 'gemini' || val === 'openai' || val === 'groq');
    apiKeyGroup.style.display = needsKey ? 'flex' : 'none';
    modelGroup.style.display = (val !== 'simulated') ? 'flex' : 'none';
  }

  providerSelect.addEventListener('change', toggleKeyInputs);

  const closeSettings = () => settingsModal.classList.add('hidden');
  closeSettingsBtn.addEventListener('click', closeSettings);
  cancelSettingsBtn.addEventListener('click', closeSettings);

  saveSettingsBtn.addEventListener('click', () => {
    currentProvider = providerSelect.value;
    currentApiKey = apiKeyInput.value.trim();
    currentModel = modelInput.value.trim();

    localStorage.setItem('marketpulse_settings', JSON.stringify({
      provider: currentProvider,
      apiKey: currentApiKey,
      model: currentModel
    }));

    updateProviderBadge();
    closeSettings();
    addTickerLog(`Configured engine: ${currentProvider.toUpperCase()}`, 'info');
  });

  // Example Chips Handlers
  exampleChips.forEach(chip => {
    chip.addEventListener('click', () => {
      exampleChips.forEach(c => c.classList.remove('active-example'));
      chip.classList.add('active-example');
      queryInput.value = chip.getAttribute('data-query');
      queryInput.focus();
    });
  });

  // Tab Navigation Handlers
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');
    });
  });

  // Add Log Item to Ticker Feed
  function addTickerLog(text, type = 'agent-action') {
    const item = document.createElement('div');
    item.className = `ticker-item ${type}`;
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    item.textContent = `[${timeStr}] ${text}`;
    tickerFeed.appendChild(item);
    tickerFeed.scrollTop = tickerFeed.scrollHeight;
  }

  // Lightweight Zero-Dependency Markdown Renderer
  function renderMarkdown(md) {
    if (!md) return '';
    let html = md
      // Escape HTML tags to prevent XSS
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      // Headers
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      // Bold & Italic
      .replace(/\*\*\*(.*?)\*\*\*/gim, '<strong><em>$1</em></strong>')
      .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/gim, '<em>$1</em>')
      // Blockquotes
      .replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>')
      // Bullet lists
      .replace(/^\- (.*$)/gim, '<li>$1</li>')
      .replace(/^\* (.*$)/gim, '<li>$1</li>')
      // Paragraphs & Line breaks
      .replace(/\n\n+/g, '</p><p>')
      .replace(/\n/g, '<br>');

    // Wrap consecutive <li> items in <ul>
    html = html.replace(/(<li>.*?<\/li>)+/gim, (match) => `<ul>${match}</ul>`);
    return `<p>${html}</p>`;
  }

  // Reset Agent Pipeline State
  function resetPipeline() {
    completedCount = 0;
    progressFill.style.width = '0%';
    progressText.textContent = '0 / 6 Agents Completed';
    workflowStateBadge.className = 'live-tag active';
    workflowStateBadge.textContent = 'Running';

    agentOrder.forEach(agentId => {
      const card = document.getElementById(`agent-${agentId}`);
      if (card) {
        card.className = 'agent-card';
        const badge = card.querySelector('.agent-status-badge');
        if (badge) {
          badge.className = 'agent-status-badge status-waiting';
          badge.textContent = 'Waiting';
        }
        const note = document.getElementById(`note-${agentId}`);
        if (note) note.textContent = 'Standby...';
      }
    });

    tickerFeed.innerHTML = '';
  }

  // Main Research Execution Function
  function startResearch() {
    const query = queryInput.value.trim();
    if (!query) {
      queryInput.focus();
      return;
    }

    if (activeEventSource) {
      activeEventSource.close();
      activeEventSource = null;
    }

    resetPipeline();
    runResearchBtn.disabled = true;
    runResearchBtn.innerHTML = '<span class="btn-text">Agents Collaborating...</span>';
    resultsSection.classList.add('hidden');

    addTickerLog(`Initiating multi-agent collaboration for: "${query}"`, 'info');

    const params = new URLSearchParams({
      q: query,
      provider: currentProvider,
      apiKey: currentApiKey,
      model: currentModel
    });

    const streamUrl = `/api/research/stream?${params.toString()}`;
    const eventSource = new EventSource(streamUrl);
    activeEventSource = eventSource;

    eventSource.addEventListener('workflow_init', (e) => {
      const data = JSON.parse(e.data);
      addTickerLog(`Workflow started in [${data.mode}] mode. Assigned 6 specialist agents.`, 'info');
    });

    eventSource.addEventListener('agent_status', (e) => {
      const data = JSON.parse(e.data);
      const card = document.getElementById(`agent-${data.id}`);
      if (!card) return;

      const badge = card.querySelector('.agent-status-badge');
      const note = document.getElementById(`note-${data.id}`);

      if (data.status === 'running') {
        card.className = 'agent-card state-running';
        if (badge) {
          badge.className = 'agent-status-badge status-running';
          badge.textContent = 'Analyzing';
        }
        if (note) note.textContent = data.message || 'Processing workstream...';
        addTickerLog(`[${card.querySelector('.agent-name').textContent}] ${data.message || 'Started analysis'}`);
      } else if (data.status === 'completed') {
        card.className = 'agent-card state-completed';
        if (badge) {
          badge.className = 'agent-status-badge status-completed';
          badge.textContent = 'Complete';
        }
        if (note) note.textContent = 'Analysis compiled successfully.';
        completedCount++;
        const pct = Math.round((completedCount / 6) * 100);
        progressFill.style.width = `${pct}%`;
        progressText.textContent = `${completedCount} / 6 Agents Completed`;
      }
    });

    eventSource.addEventListener('agent_log', (e) => {
      const data = JSON.parse(e.data);
      const card = document.getElementById(`agent-${data.id}`);
      const agentName = card ? card.querySelector('.agent-name').textContent : data.id;
      addTickerLog(`[${agentName}] ${data.text}`);
    });

    eventSource.addEventListener('workflow_complete', (e) => {
      const brief = JSON.parse(e.data);
      currentBrief = brief;
      workflowStateBadge.className = 'live-tag';
      workflowStateBadge.textContent = 'Completed';
      addTickerLog('All agent deliverables synthesized. Rendering Executive Brief.', 'info');

      renderResults(brief);
      runResearchBtn.disabled = false;
      runResearchBtn.innerHTML = '<span class="btn-text">Generate Brief</span><span class="btn-icon">✨</span>';

      eventSource.close();
      activeEventSource = null;
    });

    eventSource.addEventListener('workflow_error', (e) => {
      const err = JSON.parse(e.data);
      addTickerLog(`Error: ${err.message}`, 'info');
      workflowStateBadge.className = 'live-tag';
      workflowStateBadge.textContent = 'Error';
      runResearchBtn.disabled = false;
      runResearchBtn.innerHTML = '<span class="btn-text">Retry Brief</span>';
      eventSource.close();
      activeEventSource = null;
    });

    eventSource.onerror = (err) => {
      console.warn('SSE stream closed or interrupted.');
      runResearchBtn.disabled = false;
      runResearchBtn.innerHTML = '<span class="btn-text">Generate Brief</span><span class="btn-icon">✨</span>';
      if (activeEventSource) {
        activeEventSource.close();
        activeEventSource = null;
      }
    };
  }

  // Render Brief Results
  function renderResults(brief) {
    resultsSection.classList.remove('hidden');

    // Hero Meta
    resultTitle.textContent = `Market Brief: ${brief.entity || brief.query}`;
    resultGeography.textContent = brief.geography || 'Target Market';
    resultIndustry.textContent = brief.industry || 'Market Sector';
    resultConfidence.textContent = `${brief.critic_notes?.confidence_score || 92}% Confidence`;
    resultQueryDisplay.textContent = `Query: "${brief.query}" &bull; Generated: ${new Date(brief.timestamp).toLocaleString()}`;

    // Metrics Dashboard
    if (brief.metrics) {
      kpiSam.textContent = brief.metrics.sam || '$35M - $45M';
      kpiTam.textContent = `TAM: ${brief.metrics.tam || '$65M - $85M'}`;
      kpiCagr.textContent = brief.metrics.cagr || '19.5%';
      kpiOrders.textContent = brief.metrics.order_volume ? brief.metrics.order_volume.split(' ')[0] + ' daily' : '30K - 35K';
      kpiAov.textContent = `AOV: ${brief.metrics.avg_order_value || 'NPR 750'}`;
      kpiPayments.textContent = brief.metrics.digital_payment_share ? brief.metrics.digital_payment_share.split(' ')[0] : '65%';
    }

    // Tab 1: Executive Brief
    executiveContent.innerHTML = renderMarkdown(brief.synthesis_markdown);

    // Tab 2: Competitors
    playersContainer.innerHTML = '';
    if (brief.key_players && brief.key_players.length > 0) {
      brief.key_players.forEach(player => {
        const pCard = document.createElement('div');
        pCard.className = 'player-card';
        pCard.innerHTML = `
          <div class="player-card-header">
            <div>
              <div class="player-card-title">${player.name}</div>
              <div class="player-role-badge">${player.role}</div>
            </div>
            <span class="player-share-pill">${player.market_share} Share</span>
          </div>
          <div class="player-detail-row">
            <strong>Core Strengths & Moats:</strong>
            <p>${player.strengths}</p>
          </div>
          <div class="player-detail-row">
            <strong>Vulnerabilities:</strong>
            <p>${player.weaknesses}</p>
          </div>
        `;
        playersContainer.appendChild(pCard);
      });
    }

    // Tab 3: SWOT Matrix
    if (brief.swot) {
      swotStrengths.innerHTML = (brief.swot.strengths || []).map(s => `<li>${s}</li>`).join('');
      swotWeaknesses.innerHTML = (brief.swot.weaknesses || []).map(w => `<li>${w}</li>`).join('');
      swotOpportunities.innerHTML = (brief.swot.opportunities || []).map(o => `<li>${o}</li>`).join('');
      swotThreats.innerHTML = (brief.swot.threats || []).map(t => `<li>${t}</li>`).join('');
    }

    // Tab 4: Regulatory & Ops
    if (brief.raw_agents?.risk_ops) {
      regulatoryContainer.innerHTML = renderMarkdown(brief.raw_agents.risk_ops);
    }

    // Tab 5: Specialist Agent Workspaces Accordion
    agentOutputsAccordion.innerHTML = '';
    const agentRolesMap = {
      planner: 'Lead Research Coordinator (Dr. Evelyn Cross)',
      market_analyst: 'Market Dynamics Analyst (Marcus Vance)',
      competitor_swot: 'Competitive & SWOT Specialist (Elena Rostova)',
      risk_ops: 'Regulatory & Risk Analyst (Tariq Al-Mansoor)',
      synthesis: 'Executive Strategy Director (Sophia Sterling)',
      critic: 'Quality Assurance Critic (Dr. Arthur Pendelton)'
    };

    Object.entries(brief.raw_agents || {}).forEach(([agentId, output], idx) => {
      const item = document.createElement('div');
      item.className = 'accordion-item';
      const isOpen = idx === 0 ? 'open' : '';
      item.innerHTML = `
        <div class="accordion-header">
          <span>${agentRolesMap[agentId] || agentId}</span>
          <span class="accordion-toggle">▼</span>
        </div>
        <div class="accordion-body" style="display: ${idx === 0 ? 'block' : 'none'};">
          <div class="markdown-body">${renderMarkdown(output)}</div>
        </div>
      `;

      const header = item.querySelector('.accordion-header');
      const body = item.querySelector('.accordion-body');
      const toggle = item.querySelector('.accordion-toggle');

      header.addEventListener('click', () => {
        const isHidden = body.style.display === 'none';
        body.style.display = isHidden ? 'block' : 'none';
        toggle.textContent = isHidden ? '▲' : '▼';
      });

      agentOutputsAccordion.appendChild(item);
    });

    // Tab 6: Quality Critic Review
    if (brief.raw_agents?.critic) {
      criticContainer.innerHTML = renderMarkdown(brief.raw_agents.critic);
    }

    // Auto-scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // Event Listeners
  runResearchBtn.addEventListener('click', startResearch);
  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') startResearch();
  });

  // Export: Copy Markdown
  copyMarkdownBtn.addEventListener('click', () => {
    if (!currentBrief) return;
    const fullMarkdown = `# Market Research Brief: ${currentBrief.entity || currentBrief.query}
**Industry:** ${currentBrief.industry}
**Geography:** ${currentBrief.geography}
**Date:** ${new Date(currentBrief.timestamp).toLocaleDateString()}

${currentBrief.synthesis_markdown}

---
## Quality Assurance & Audit Review
${currentBrief.raw_agents?.critic || ''}
`;
    navigator.clipboard.writeText(fullMarkdown).then(() => {
      const origText = copyMarkdownBtn.innerHTML;
      copyMarkdownBtn.innerHTML = '<span>✅ Copied!</span>';
      setTimeout(() => { copyMarkdownBtn.innerHTML = origText; }, 2000);
    }).catch(err => {
      alert('Failed to copy to clipboard.');
    });
  });

  // Export: Download Markdown
  downloadMdBtn.addEventListener('click', () => {
    if (!currentBrief) return;
    const fullMarkdown = `# Market Research Brief: ${currentBrief.entity || currentBrief.query}
**Industry:** ${currentBrief.industry}
**Geography:** ${currentBrief.geography}
**Date:** ${new Date(currentBrief.timestamp).toLocaleDateString()}

${currentBrief.synthesis_markdown}

---
## Competitive & SWOT Intelligence
${currentBrief.raw_agents?.competitor_swot || ''}

---
## Regulatory, Infrastructure & Risk
${currentBrief.raw_agents?.risk_ops || ''}

---
## Independent Quality Review
${currentBrief.raw_agents?.critic || ''}
`;
    const blob = new Blob([fullMarkdown], { type: 'text/markdown;charset=utf-8;' });
    const link = document.createElement('a');
    const filename = `market_brief_${(currentBrief.entity || 'research').toLowerCase().replace(/[^a-z0-9]+/g, '_')}.md`;
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });

  // Export: Print / PDF
  printReportBtn.addEventListener('click', () => {
    window.print();
  });
});


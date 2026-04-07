'use strict';

// ── LookingGlass class ────────────────────────────────────────────────────────
class LookingGlass {
  constructor() {
    this.selectedSource  = 'local';
    this.selectedServers = new Set();
    this.maxServers      = 5;
    this.servers         = {};
    this.sources         = [];
    this.results         = [];
    this.currentCat      = 'gaming';
  }

  async init() {
    try {
      const [serversRes, sourcesRes] = await Promise.all([
        fetch('/servers'),
        fetch('/sources'),
      ]);
      this.servers = await serversRes.json();
      this.sources = await sourcesRes.json();
    } catch (e) {
      console.error('LookingGlass init error:', e);
      return;
    }

    this._renderSources();
    this._renderCatTabs();
    this._renderServers(this.currentCat);
    this._bindRunBtn();
    this._bindShareBtn();
  }

  // ── Source selector ────────────────────────────────────────────────────────

  _renderSources() {
    const grid = document.getElementById('source-grid');
    if (!grid) return;
    grid.innerHTML = '';
    this.sources.forEach(src => {
      const card = document.createElement('div');
      card.className = 'source-card' + (src.id === this.selectedSource ? ' selected' : '');
      card.dataset.id = src.id;
      card.innerHTML = `
        <div class="source-card-header">
          <span class="source-emoji">${src.emoji}</span>
          <div>
            <div class="source-name">${src.name}</div>
            <div class="source-loc">${src.location}</div>
          </div>
        </div>
        <div class="source-desc">${src.description}</div>
      `;
      card.addEventListener('click', () => this.selectSource(src.id));
      grid.appendChild(card);
    });
  }

  selectSource(sourceId) {
    this.selectedSource = sourceId;
    document.querySelectorAll('.source-card').forEach(c => {
      c.classList.toggle('selected', c.dataset.id === sourceId);
    });
  }

  // ── Server category tabs + grid ────────────────────────────────────────────

  _renderCatTabs() {
    const tabs = document.getElementById('cat-tabs');
    if (!tabs) return;
    tabs.querySelectorAll('.cat-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.querySelectorAll('.cat-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.currentCat = tab.dataset.cat;
        this._renderServers(this.currentCat);
      });
    });
  }

  _renderServers(cat) {
    const grid    = document.getElementById('server-grid');
    const servers = this.servers[cat] || [];
    grid.innerHTML = '';
    servers.forEach(srv => {
      const selected = this.selectedServers.has(srv.id);
      const disabled = !selected && this.selectedServers.size >= this.maxServers;
      const card = document.createElement('div');
      card.className = 'server-card' +
        (selected ? ' selected' : '') +
        (disabled ? ' disabled' : '');
      card.dataset.id = srv.id;
      card.innerHTML = `
        <span class="checkmark">✓</span>
        <div class="server-card-emoji">${srv.emoji}</div>
        <div class="server-card-name">${srv.name}</div>
        <div class="server-card-loc">${srv.flag} ${srv.location}</div>
      `;
      if (!disabled) {
        card.addEventListener('click', () => this.toggleServer(srv.id));
      }
      grid.appendChild(card);
    });
  }

  toggleServer(serverId) {
    if (this.selectedServers.has(serverId)) {
      this.selectedServers.delete(serverId);
    } else {
      if (this.selectedServers.size >= this.maxServers) return;
      this.selectedServers.add(serverId);
    }
    this._updateCounter();
    this._renderServers(this.currentCat);
    this._updateRunBtn();
  }

  _updateCounter() {
    const counter = document.getElementById('server-counter');
    if (counter) counter.textContent = `${this.selectedServers.size}/${this.maxServers} valgt`;
  }

  _updateRunBtn() {
    const btn = document.getElementById('run-lg-btn');
    if (btn) btn.disabled = this.selectedServers.size === 0;
  }

  _bindRunBtn() {
    const btn = document.getElementById('run-lg-btn');
    if (btn) btn.addEventListener('click', () => this.runTest());
  }

  // ── Test runner ────────────────────────────────────────────────────────────

  async runTest() {
    const btn = document.getElementById('run-lg-btn');
    if (btn) { btn.disabled = true; btn.classList.add('running'); btn.textContent = '⏳ Kjører…'; }

    // Reset sections
    ['traceroute-section','comparison-section','report-section'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = 'none';
    });

    // Animate traceroute for the first selected server
    const firstId = [...this.selectedServers][0];
    if (firstId) await this.animateTraceroute(firstId);

    // Ping all selected servers
    const targets = [...this.selectedServers].join(',');
    let results = [];
    try {
      const resp = await fetch(`/ping/multi?targets=${targets}&source=${this.selectedSource}`);
      results = await resp.json();
      this.results = results;
    } catch (e) {
      console.error('ping/multi error:', e);
    }

    if (results.length > 0) {
      this.showComparisonTable(results);
      this.showReportCard(results);
    }

    if (btn) { btn.disabled = false; btn.classList.remove('running'); btn.textContent = '🚀 KJØR TEST PÅ NYTT'; }
  }

  // ── Traceroute animation ───────────────────────────────────────────────────

  async animateTraceroute(targetId) {
    const section             = document.getElementById('traceroute-section');
    const tracerouteSubtitle  = document.getElementById('traceroute-subtitle');
    const hopsList            = document.getElementById('hops-list');
    if (!section) return;

    hopsList.innerHTML = '';
    section.style.display = 'block';

    let hops = [];
    try {
      const resp = await fetch(`/traceroute?target=${targetId}&source=${this.selectedSource}`);
      const data = await resp.json();
      hops = data.hops || [];
      if (data.server) {
        tracerouteSubtitle.textContent = `Ruten fra ${this._sourceName()} til ${data.server.name} (${data.server.location} ${data.server.flag})`;
      }
    } catch (e) {
      tracerouteSubtitle.textContent = 'Klarte ikke hente rutedata';
      return;
    }

    const maxMs = Math.max(...hops.map(h => h.ms));

    for (const hop of hops) {
      await new Promise(r => setTimeout(r, 600));

      const msClass = hop.ms < 5 ? 'fast' : hop.ms < 15 ? 'medium' : 'slow';
      const barPct  = Math.round((hop.ms / maxMs) * 100);

      const item = document.createElement('div');
      item.className = 'hop-item';
      item.innerHTML = `
        <div class="hop-num">${hop.hop}</div>
        <div class="hop-emoji">${hop.emoji}</div>
        <div class="hop-body">
          <div class="hop-name">${hop.name}</div>
          <div class="hop-desc">${hop.description}</div>
          <div class="hop-bar"><div class="hop-bar-fill" style="width:${barPct}%"></div></div>
        </div>
        <div class="hop-ms ${msClass}">${hop.ms} ms</div>
      `;
      hopsList.appendChild(item);
      item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  _sourceName() {
    const src = this.sources.find(s => s.id === this.selectedSource);
    return src ? src.name : this.selectedSource;
  }

  // ── Comparison table ───────────────────────────────────────────────────────

  showComparisonTable(results) {
    const section = document.getElementById('comparison-section');
    const tbody   = document.getElementById('comparison-tbody');
    if (!section || !tbody) return;

    tbody.innerHTML = '';
    results.forEach(r => {
      const server  = this._findServer(r.id);
      const tlClass = r.ms < 20 ? 'tl-green' : r.ms < 50 ? 'tl-yellow' : 'tl-red';
      const scClass = r.score >= 90 ? 'score-green' : r.score >= 70 ? 'score-yellow' : 'score-red';
      const statusLabel = { excellent: 'Utmerket', good: 'Bra', ok: 'OK', poor: 'Tregt' }[r.status] || r.status;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <div class="server-cell">
            <span class="server-cell-emoji">${server ? server.emoji : '🖥️'}</span>
            <div>
              <div>${server ? server.name : r.id}</div>
              <div style="font-size:0.72rem;color:var(--text2)">${r.message}</div>
            </div>
          </div>
        </td>
        <td><span class="traffic-light ${tlClass}"></span>${r.ms} ms</td>
        <td>${r.jitter} ms</td>
        <td><span class="score-badge ${scClass}">${r.score}</span></td>
        <td>${statusLabel}</td>
      `;
      tbody.appendChild(tr);
    });

    section.style.display = 'block';
  }

  _findServer(id) {
    for (const cat of Object.values(this.servers)) {
      const s = cat.find(x => x.id === id);
      if (s) return s;
    }
    return null;
  }

  // ── Report card ────────────────────────────────────────────────────────────

  showReportCard(results) {
    const section = document.getElementById('report-section');
    const card    = document.getElementById('report-card');
    if (!section || !card) return;

    // Map result IDs to categories
    const catScores = { gaming: [], streaming: [], work: [], general: [] };
    results.forEach(r => {
      for (const [cat, servers] of Object.entries(this.servers)) {
        if (servers.find(s => s.id === r.id)) {
          catScores[cat].push(r.score);
        }
      }
    });

    const catInfo = [
      { key: 'gaming',    icon: '🎮', label: 'Gaming' },
      { key: 'streaming', icon: '📺', label: 'Streaming' },
      { key: 'work',      icon: '💼', label: 'Hjemmekontor' },
      { key: 'general',   icon: '🌐', label: 'Infrastruktur' },
    ];

    const catsHtml = catInfo
      .filter(ci => catScores[ci.key].length > 0)
      .map(ci => {
        const avg   = Math.round(catScores[ci.key].reduce((a,b)=>a+b,0) / catScores[ci.key].length);
        const color = avg >= 90 ? 'var(--green)' : avg >= 70 ? 'var(--yellow)' : 'var(--red)';
        return `
          <div class="report-cat">
            <div class="report-cat-icon">${ci.icon}</div>
            <div class="report-cat-name">${ci.label}</div>
            <div class="report-cat-score" style="color:${color}">${avg}</div>
          </div>
        `;
      }).join('');

    const best  = results.length > 0 ? results.reduce((a,b) => a.score > b.score ? a : b) : null;
    const worst = results.length > 0 ? results.reduce((a,b) => a.score < b.score ? a : b) : null;
    if (!best || !worst) return;
    const bestSrv  = this._findServer(best.id);
    const worstSrv = this._findServer(worst.id);

    card.innerHTML = `
      <div class="report-categories">${catsHtml}</div>
      <div class="report-highlights">
        <div class="highlight-box">
          <div class="highlight-label">🏆 Beste server</div>
          <div class="highlight-value">${bestSrv ? bestSrv.emoji + ' ' + bestSrv.name : best.id} — ${best.ms} ms</div>
        </div>
        <div class="highlight-box">
          <div class="highlight-label">🐌 Tregeste server</div>
          <div class="highlight-value">${worstSrv ? worstSrv.emoji + ' ' + worstSrv.name : worst.id} — ${worst.ms} ms</div>
        </div>
      </div>
    `;

    section.style.display = 'block';
  }

  // ── Share ──────────────────────────────────────────────────────────────────

  generateShareText(results) {
    const lines = ['🔭 Heimnett Nett-reise resultat', ''];
    results.forEach(r => {
      const srv   = this._findServer(r.id);
      const name  = srv ? srv.name : r.id;
      const emoji = srv ? srv.emoji : '🖥️';
      lines.push(`${emoji} ${name}: ${r.ms} ms (score ${r.score}/100)`);
    });
    lines.push('');
    lines.push(`Kilde: ${this._sourceName()}`);
    lines.push('Testet med Heimnett SpeedTest');
    return lines.join('\n');
  }

  _bindShareBtn() {
    const btn = document.getElementById('share-btn');
    if (!btn) return;
    btn.addEventListener('click', async () => {
      const text = this.generateShareText(this.results);
      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = 'Kopiert! ✅';
        setTimeout(() => { btn.textContent = 'Del resultat 📤'; }, 2000);
      } catch (e) {
        // Clipboard API unavailable — show the text so user can copy manually
        window.prompt('Kopier teksten under (Ctrl+C / Cmd+C):', text);
      }
    });
  }
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const lg = new LookingGlass();
  lg.init();
});

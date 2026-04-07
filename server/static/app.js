'use strict';

// ── SpeedTest class ────────────────────────────────────────────────────────────
class SpeedTest {
  constructor() {
    this.downloadSpeed = 0;
    this.uploadSpeed   = 0;
    this.ping          = 0;
    this.running       = false;
  }

  async measurePing() {
    const samples = [];
    for (let i = 0; i < 5; i++) {
      const t0 = performance.now();
      await fetch('/ping');
      samples.push(performance.now() - t0);
    }
    samples.sort((a, b) => a - b);
    return Math.round(samples[2] * 10) / 10; // median
  }

  async measureDownload(sizeMb = 25) {
    const url = `/download?size_mb=${sizeMb}`;
    const t0   = performance.now();
    const resp = await fetch(url);
    const reader = resp.body.getReader();
    let bytes = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      bytes += value.length;
    }
    const elapsed = (performance.now() - t0) / 1000;
    return Math.round((bytes * 8) / elapsed / 1e6 * 10) / 10; // Mbit/s
  }

  async measureUpload(sizeMb = 10) {
    const RANDOM_SEED_SIZE = 65536; // 64 KB — enough to prevent trivial compression
    const bytes   = sizeMb * 1024 * 1024;
    const payload = new Uint8Array(bytes);
    // Randomise only the first 64 KB — the rest stays zero-filled,
    // which is sufficient for measuring TCP throughput.
    crypto.getRandomValues(payload.subarray(0, Math.min(bytes, RANDOM_SEED_SIZE)));
    const t0 = performance.now();
    await fetch('/upload', { method: 'POST', body: payload });
    const elapsed = (performance.now() - t0) / 1000;
    return Math.round((bytes * 8) / elapsed / 1e6 * 10) / 10; // Mbit/s
  }

  async runFull(onProgress) {
    this.running = true;

    onProgress({ phase: 'ping', progress: 5 });
    this.ping = await this.measurePing();
    onProgress({ phase: 'ping', ping: this.ping, progress: 20 });

    onProgress({ phase: 'download', progress: 25 });
    this.downloadSpeed = await this.measureDownload(25);
    onProgress({ phase: 'download', ping: this.ping, download: this.downloadSpeed, progress: 70 });

    onProgress({ phase: 'upload', progress: 72 });
    this.uploadSpeed = await this.measureUpload(10);
    onProgress({ phase: 'upload', ping: this.ping, download: this.downloadSpeed, upload: this.uploadSpeed, progress: 100 });

    this.running = false;
    return { ping: this.ping, download: this.downloadSpeed, upload: this.uploadSpeed };
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function pingClass(ms) {
  if (ms < 20)  return 'good';
  if (ms < 60)  return 'ok';
  return 'bad';
}

function speedClass(mbit) {
  if (mbit >= 50)  return 'good';
  if (mbit >= 10)  return 'ok';
  return 'bad';
}

function speedVerdict(dl, ul, ping) {
  if (dl >= 100 && ping < 20) return { text: '🚀 Fantastisk! Topp-internett', cls: 'good' };
  if (dl >= 50  && ping < 40) return { text: '✅ Meget bra internett',          cls: 'good' };
  if (dl >= 20  && ping < 80) return { text: '👍 Bra nok for de fleste',        cls: 'ok' };
  if (dl >= 5)                 return { text: '⚠️ Moderat — kan være tregt',     cls: 'ok' };
  return                               { text: '❌ Tregt internett', cls: 'bad' };
}

// ── UI binding ────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(s => s.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${tab}`).classList.add('active');
    });
  });

  // Speedtest
  const startBtn     = document.getElementById('start-test');
  const hintText     = document.getElementById('hint-text');
  const progressWrap = document.getElementById('progress-wrap');
  const progressBar  = document.getElementById('progress-bar');
  const phaseLabel   = document.getElementById('phase-label');
  const valPing      = document.getElementById('val-ping');
  const valDownload  = document.getElementById('val-download');
  const valUpload    = document.getElementById('val-upload');
  const resultSummary= document.getElementById('result-summary');
  const resultVerdict= document.getElementById('result-verdict');
  const resultDetail = document.getElementById('result-detail');

  const phaseNames = {
    ping:     'Måler forsinkelse (ping)…',
    download: 'Måler nedlastingshastighet…',
    upload:   'Måler opplastingshastighet…',
  };

  startBtn.addEventListener('click', async () => {
    if (startBtn.classList.contains('running')) return;

    // Reset
    startBtn.classList.remove('done');
    startBtn.classList.add('running');
    startBtn.querySelector('.start-label').textContent = 'TESTER…';
    hintText.textContent = '';
    progressWrap.style.display = 'block';
    resultSummary.style.display = 'none';
    valPing.textContent = valDownload.textContent = valUpload.textContent = '…';
    ['card-ping','card-download','card-upload'].forEach(id => {
      const c = document.getElementById(id);
      c.className = 'metric-card';
    });

    const st = new SpeedTest();
    try {
      await st.runFull(({ phase, ping, download, upload, progress }) => {
        progressBar.style.width = progress + '%';
        if (phase) phaseLabel.textContent = phaseNames[phase] || '';
        if (ping     != null) { valPing.textContent = ping;     valPing.className     = pingClass(ping); }
        if (download != null) { valDownload.textContent = download; valDownload.className = speedClass(download); }
        if (upload   != null) { valUpload.textContent = upload;   valUpload.className   = speedClass(upload); }
      });

      const v = speedVerdict(st.downloadSpeed, st.uploadSpeed, st.ping);
      resultVerdict.textContent = v.text;
      resultVerdict.className   = 'result-verdict ' + v.cls;
      resultDetail.textContent  = `Nedlasting ${st.downloadSpeed} Mbit/s · Opplasting ${st.uploadSpeed} Mbit/s · Ping ${st.ping} ms`;
      resultSummary.style.display = 'block';

      startBtn.classList.remove('running');
      startBtn.classList.add('done');
      startBtn.querySelector('.start-label').textContent = 'TA EN NY TEST';
      phaseLabel.textContent = 'Test fullført!';
      progressBar.style.width = '100%';
    } catch (err) {
      phaseLabel.textContent = 'Feil under test: ' + err.message;
      startBtn.classList.remove('running');
      startBtn.querySelector('.start-label').textContent = 'PRØV IGJEN';
    }
  });
});
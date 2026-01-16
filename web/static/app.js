// AI Document Processor - Clean Implementation
class DocumentProcessor {
    constructor() {
        this.file = null;
        this.ws = null;
        this.processing = false;

        this.init();
    }

    init() {
        this.cacheElements();
        this.setupEvents();
        this.connectWebSocket();
    }

    cacheElements() {
        // Upload
        this.uploadZone = document.getElementById('uploadZone');
        this.fileInput = document.getElementById('fileInput');
        this.filePreview = document.getElementById('filePreview');
        this.fileName = document.getElementById('fileName');
        this.fileSize = document.getElementById('fileSize');
        this.removeFileBtn = document.getElementById('removeFile');

        // Cards
        this.uploadCard = document.getElementById('uploadCard');
        this.configCard = document.getElementById('configCard');
        this.processingCard = document.getElementById('processingCard');
        this.resultsCard = document.getElementById('resultsCard');

        // Config
        this.processBtn = document.getElementById('processBtn');
        this.ocrSettings = document.getElementById('ocrSettings');
        this.ocrAI = document.getElementById('ocrAI');
        this.aiProviderGroup = document.getElementById('aiProviderGroup');

        // Processing
        this.agentScout = document.getElementById('agentScout');
        this.agentMaker = document.getElementById('agentMaker');
        this.agentChecker = document.getElementById('agentChecker');
        this.agentCurator = document.getElementById('agentCurator');
        this.logsContent = document.getElementById('logsContent');
        this.clearLogsBtn = document.getElementById('clearLogs');

        // Results
        this.resultsContent = document.getElementById('resultsContent');
        this.startOverBtn = document.getElementById('startOver');

        // Status
        this.statusPill = document.getElementById('statusPill');
    }

    setupEvents() {
        // Upload
        this.uploadZone.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFile(e.target.files[0]));
        this.uploadZone.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadZone.addEventListener('drop', (e) => this.handleDrop(e));
        this.removeFileBtn.addEventListener('click', () => this.removeFile());

        // Processing type
        document.querySelectorAll('input[name="type"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.handleTypeChange(e.target.value));
        });

        // OCR AI toggle
        this.ocrAI.addEventListener('change', (e) => {
            this.aiProviderGroup.style.display = e.target.checked ? 'block' : 'none';
        });

        // Process button
        this.processBtn.addEventListener('click', () => this.processDocument());

        // Other
        this.clearLogsBtn.addEventListener('click', () => this.clearLogs());
        this.startOverBtn.addEventListener('click', () => this.reset());
    }

    // WebSocket
    connectWebSocket() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${location.host}/ws`;

        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
            this.updateStatus(true);
            this.log('Connected to server', 'success');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWSMessage(data);
        };

        this.ws.onerror = () => {
            this.updateStatus(false);
            this.log('Connection error', 'error');
        };

        this.ws.onclose = () => {
            this.updateStatus(false);
            setTimeout(() => this.connectWebSocket(), 3000);
        };
    }

    handleWSMessage(data) {
        switch (data.type) {
            case 'log':
                this.log(data.message, data.level?.toLowerCase() || 'info');
                break;
            case 'agent_status':
                this.updateAgent(data.agent, data.status);
                break;
            case 'result':
                this.showResults(data.data);
                break;
            case 'error':
                this.log(data.message, 'error');
                this.processing = false;
                this.processBtn.disabled = false;
                break;
        }
    }

    updateStatus(connected) {
        if (connected) {
            this.statusPill.classList.add('connected');
            this.statusPill.querySelector('.status-text').textContent = 'Connected';
        } else {
            this.statusPill.classList.remove('connected');
            this.statusPill.querySelector('.status-text').textContent = 'Disconnected';
        }
    }

    // File Handling
    handleDragOver(e) {
        e.preventDefault();
        this.uploadZone.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.uploadZone.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.uploadZone.classList.remove('dragover');

        const file = e.dataTransfer.files[0];
        if (file) this.handleFile(file);
    }

    handleFile(file) {
        if (!file) return;

        this.file = file;
        this.fileName.textContent = file.name;
        this.fileSize.textContent = this.formatBytes(file.size);

        // Show file preview, hide upload zone
        this.uploadZone.style.display = 'none';
        this.filePreview.style.display = 'flex';

        // Show config card
        this.configCard.style.display = 'block';
        this.configCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        // Auto-select OCR for images
        if (this.isImageFile(file.name)) {
            document.getElementById('typeOCR').checked = true;
            this.ocrSettings.style.display = 'block';
            this.log('Image file detected - OCR mode selected', 'info');
        }

        this.log(`File selected: ${file.name} (${this.formatBytes(file.size)})`, 'info');
    }

    removeFile() {
        this.file = null;
        this.fileInput.value = '';
        this.uploadZone.style.display = 'block';
        this.filePreview.style.display = 'none';
        this.configCard.style.display = 'none';
        this.processingCard.style.display = 'none';
        this.resultsCard.style.display = 'none';
    }

    isImageFile(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        return ['png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp'].includes(ext);
    }

    handleTypeChange(type) {
        this.ocrSettings.style.display = type === 'ocr' ? 'block' : 'none';
    }

    // Processing
    async processDocument() {
        if (!this.file || this.processing) return;

        this.processing = true;
        this.processBtn.disabled = true;
        this.processBtn.innerHTML = '<span>Processing...</span>';

        // Show processing card
        this.processingCard.style.display = 'block';
        this.processingCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        // Reset agents
        this.resetAgents();

        this.log('Starting document processing...', 'info');

        try {
            const config = this.buildConfig();
            const formData = new FormData();
            formData.append('file', this.file);
            formData.append('workflow_config', JSON.stringify(config));

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Upload failed: ${error}`);
            }

            const result = await response.json();

            if (result.success) {
                this.log('Processing completed successfully!', 'success');
            } else {
                this.log('Processing failed', 'error');
                if (result.errors) {
                    result.errors.forEach(err => this.log(err, 'error'));
                }
            }

        } catch (error) {
            this.log(`Error: ${error.message}`, 'error');
            console.error('Processing error:', error);
        } finally {
            this.processing = false;
            this.processBtn.disabled = false;
            this.processBtn.innerHTML = '<span>Process Document</span>';
        }
    }

    buildConfig() {
        const type = document.querySelector('input[name="type"]:checked').value;

        const config = {
            workflow_name: `${type}_workflow`,
            scout_config: {
                preview_length: 1000,
                extract_metadata: true
            },
            maker_config: {
                transformation_type: type,
                max_output_length: 1000
            },
            checker_config: {
                min_quality_score: 0.5
            }
        };

        // Add OCR config if selected
        if (type === 'ocr') {
            config.maker_config.ocr_config = {
                language: document.getElementById('ocrLanguage').value,
                preprocess: document.getElementById('ocrPreprocess').checked,
                deskew: document.getElementById('ocrDeskew').checked,
                ai_postprocess: document.getElementById('ocrAI').checked
            };

            if (config.maker_config.ocr_config.ai_postprocess) {
                config.maker_config.ocr_config.ai_provider = document.getElementById('aiProvider').value;
            }
        }

        return config;
    }

    resetAgents() {
        [this.agentScout, this.agentMaker, this.agentChecker, this.agentCurator].forEach(agent => {
            agent.classList.remove('active', 'completed', 'failed');
            agent.querySelector('.agent-status').textContent = 'Waiting...';
        });
    }

    updateAgent(name, status) {
        const agentMap = {
            scout: this.agentScout,
            maker: this.agentMaker,
            checker: this.agentChecker,
            curator: this.agentCurator
        };

        const agent = agentMap[name];
        if (!agent) return;

        agent.classList.remove('active', 'completed', 'failed');

        if (status === 'running') {
            agent.classList.add('active');
            agent.querySelector('.agent-status').textContent = 'Processing...';
        } else if (status === 'completed') {
            agent.classList.add('completed');
            agent.querySelector('.agent-status').textContent = 'Completed';
        } else if (status === 'failed') {
            agent.classList.add('failed');
            agent.querySelector('.agent-status').textContent = 'Failed';
        }
    }

    // Logging
    log(message, level = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${level}`;

        const time = new Date().toLocaleTimeString();
        entry.innerHTML = `<span class="log-time">${time}</span> ${this.escapeHtml(message)}`;

        this.logsContent.appendChild(entry);
        this.logsContent.scrollTop = this.logsContent.scrollHeight;
    }

    clearLogs() {
        this.logsContent.innerHTML = '';
        this.log('Logs cleared', 'info');
    }

    // Results
    showResults(data) {
        this.resultsCard.style.display = 'block';
        this.resultsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        const isOCR = data.workflow_name?.includes('ocr');
        const metadata = data.metadata || {};

        let html = '<div class="results-grid">';

        // Stats for OCR
        if (isOCR && metadata.maker_metadata) {
            const ocrMeta = metadata.maker_metadata;
            html += '<div class="stats-grid">';

            if (ocrMeta.average_confidence !== undefined) {
                const conf = (ocrMeta.average_confidence * 100).toFixed(1);
                html += `
                    <div class="stat-box">
                        <div class="stat-value">${conf}%</div>
                        <div class="stat-label">Confidence</div>
                    </div>
                `;
            }

            if (ocrMeta.pages_processed) {
                html += `
                    <div class="stat-box">
                        <div class="stat-value">${ocrMeta.pages_processed}</div>
                        <div class="stat-label">Pages</div>
                    </div>
                `;
            }

            if (ocrMeta.total_words) {
                html += `
                    <div class="stat-box">
                        <div class="stat-value">${ocrMeta.total_words}</div>
                        <div class="stat-label">Words</div>
                    </div>
                `;
            }

            if (data.processing_time_ms) {
                html += `
                    <div class="stat-box">
                        <div class="stat-value">${(data.processing_time_ms / 1000).toFixed(1)}s</div>
                        <div class="stat-label">Time</div>
                    </div>
                `;
            }

            html += '</div>';
        }

        // Main output
        html += `
            <div class="result-section">
                <h3>${isOCR ? 'Extracted Text' : 'Output'}</h3>
                <div class="result-value">
                    ${typeof data.final_output === 'string'
                        ? this.escapeHtml(data.final_output)
                        : `<pre>${JSON.stringify(data.final_output, null, 2)}</pre>`}
                </div>
            </div>
        `;

        // Metadata
        if (Object.keys(metadata).length > 0) {
            html += `
                <div class="result-section">
                    <h3>Details</h3>
                    <div class="result-value">
                        <pre>${JSON.stringify(metadata, null, 2)}</pre>
                    </div>
                </div>
            `;
        }

        html += '</div>';
        this.resultsContent.innerHTML = html;
    }

    // Utilities
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    reset() {
        this.removeFile();
        this.logsContent.innerHTML = '';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DocumentProcessor();
});

// AI Document Processor - Clean Implementation
class DocumentProcessor {
    constructor() {
        this.file = null;
        this.ws = null;
        this.chatWs = null;
        this.processing = false;
        this.currentDocumentId = null;

        this.init();
    }

    init() {
        this.cacheElements();
        this.setupEvents();
        this.connectWebSocket();
        this.connectChatWebSocket();
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

        // Chat
        this.chatFab = document.getElementById('chatFab');
        this.chatPanel = document.getElementById('chatPanel');
        this.chatClose = document.getElementById('chatClose');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.chatSend = document.getElementById('chatSend');
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

        // Chat
        this.chatFab.addEventListener('click', () => this.toggleChat());
        this.chatClose.addEventListener('click', () => this.toggleChat());
        this.chatSend.addEventListener('click', () => this.sendChatMessage());
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });
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

    // Chat WebSocket
    connectChatWebSocket() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${location.host}/chat`;

        this.chatWs = new WebSocket(url);

        this.chatWs.onopen = () => {
            console.log('Chat WebSocket connected');
        };

        this.chatWs.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleChatMessage(data);
        };

        this.chatWs.onerror = () => {
            console.error('Chat WebSocket error');
        };

        this.chatWs.onclose = () => {
            console.log('Chat WebSocket disconnected');
            setTimeout(() => this.connectChatWebSocket(), 3000);
        };
    }

    handleChatMessage(data) {
        if (data.type === 'sources') {
            this.currentSources = data.sources;
        } else if (data.type === 'answer') {
            this.removeTypingIndicator();

            if (!this.currentAnswer) {
                this.currentAnswer = '';
                this.currentAnswerBubble = this.addChatMessage('assistant', '');
            }

            this.currentAnswer += data.content;
            this.currentAnswerBubble.textContent = this.currentAnswer;

            if (data.done) {
                if (this.currentSources && this.currentSources.length > 0) {
                    this.addSourcesToMessage(
                        this.currentAnswerBubble.parentElement,
                        this.currentSources
                    );
                }

                this.currentAnswer = null;
                this.currentAnswerBubble = null;
                this.currentSources = null;
            }

            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }

    toggleChat() {
        this.chatPanel.classList.toggle('open');
        if (this.chatPanel.classList.contains('open')) {
            this.chatInput.focus();
        }
    }

    enableChat() {
        this.chatFab.style.display = 'flex';
        this.chatInput.disabled = false;
        this.chatSend.disabled = false;
        this.currentDocumentId = this.file ? this.file.name : null;

        // Clear welcome message
        const welcome = this.chatMessages.querySelector('.chat-welcome');
        if (welcome) {
            welcome.remove();
        }

        // Add success message
        this.addChatMessage(
            'assistant',
            `✅ Document processed! Ask me anything about "${this.currentDocumentId}".`
        );
    }

    sendChatMessage() {
        const question = this.chatInput.value.trim();
        if (!question || !this.chatWs) return;

        // Add user message
        this.addChatMessage('user', question);

        // Clear input
        this.chatInput.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        // Send to server
        this.chatWs.send(JSON.stringify({
            type: 'question',
            question: question,
            document_id: this.currentDocumentId
        }));
    }

    addChatMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = content;

        messageDiv.appendChild(bubble);
        this.chatMessages.appendChild(messageDiv);

        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;

        return bubble;
    }

    addSourcesToMessage(messageElement, sources) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';

        sources.forEach((source, index) => {
            const badge = document.createElement('span');
            badge.className = 'source-badge';
            badge.textContent = `Source ${index + 1}`;
            badge.title = source.content;
            sourcesDiv.appendChild(badge);
        });

        messageElement.appendChild(sourcesDiv);
    }

    showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'chat-message assistant';
        indicator.id = 'typingIndicator';

        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;

        indicator.appendChild(typingDiv);
        this.chatMessages.appendChild(indicator);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    removeTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    // Results
    showResults(data) {
        this.resultsCard.style.display = 'block';
        this.resultsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        const workflowType = data.workflow_name?.split('_')[0] || 'unknown';
        const metadata = data.metadata || {};

        let html = '<div class="results-grid">';

        // Stats Grid
        html += '<div class="stats-grid">';

        // Always show processing time
        if (data.processing_time_ms) {
            html += `
                <div class="stat-box">
                    <div class="stat-value">${(data.processing_time_ms / 1000).toFixed(1)}s</div>
                    <div class="stat-label">Processing Time</div>
                </div>
            `;
        }

        // OCR-specific stats
        if (workflowType === 'ocr' && metadata.maker_metadata) {
            const ocrMeta = metadata.maker_metadata;

            if (ocrMeta.average_confidence !== undefined) {
                const conf = (ocrMeta.average_confidence * 100).toFixed(1);
                html += `
                    <div class="stat-box">
                        <div class="stat-value" style="color: ${conf > 80 ? 'var(--success)' : conf > 60 ? 'var(--warning)' : 'var(--error)'}">
                            ${conf}%
                        </div>
                        <div class="stat-label">OCR Confidence</div>
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
                        <div class="stat-label">Words Extracted</div>
                    </div>
                `;
            }
        }

        html += '</div>';

        // Main output with nice formatting
        const outputTitle = {
            'ocr': 'Extracted Text',
            'summarization': 'Summary',
            'extraction': 'Extracted Information',
            'classification': 'Classification Result'
        }[workflowType] || 'Output';

        html += `
            <div class="result-highlight">
                <h3>${outputTitle}</h3>
                <div class="result-text">
                    ${typeof data.final_output === 'string'
                        ? this.formatOutput(data.final_output)
                        : `<pre>${JSON.stringify(data.final_output, null, 2)}</pre>`}
                </div>
            </div>
        `;

        // Document metadata
        if (metadata.scout_metadata) {
            const scoutMeta = metadata.scout_metadata;
            html += `
                <div class="result-section">
                    <h3>Document Information</h3>
                    <div class="result-value">
                        ${scoutMeta.file_type ? `<div><strong>Type:</strong> ${scoutMeta.file_type}</div>` : ''}
                        ${scoutMeta.page_count ? `<div><strong>Pages:</strong> ${scoutMeta.page_count}</div>` : ''}
                        ${scoutMeta.character_count ? `<div><strong>Characters:</strong> ${scoutMeta.character_count.toLocaleString()}</div>` : ''}
                    </div>
                </div>
            `;
        }

        html += '</div>';
        this.resultsContent.innerHTML = html;

        // Enable chat after showing results
        this.enableChat();
    }

    formatOutput(text) {
        // Convert line breaks to HTML
        return this.escapeHtml(text).replace(/\n/g, '<br>');
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
        this.chatMessages.innerHTML = '<div class="chat-welcome">Upload and process a document to start asking questions about it.</div>';
        this.chatFab.style.display = 'none';
        this.chatPanel.classList.remove('open');
        this.chatInput.disabled = true;
        this.chatSend.disabled = true;
        this.currentDocumentId = null;
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DocumentProcessor();
});

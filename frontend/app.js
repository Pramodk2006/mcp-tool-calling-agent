// MCP Tool-Calling Agent Frontend JavaScript

class MCPAgent {
    constructor() {
        this.baseURL = window.location.origin;
        this.isProcessing = false;
        this.currentUpload = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.checkAgentHealth();
        this.loadUploadedFiles();
    }
    
    bindEvents() {
        // Query input and buttons
        document.getElementById('run-agent-btn').addEventListener('click', () => this.runAgent());
        document.getElementById('clear-btn').addEventListener('click', () => this.clearQuery());
        
        // Example query buttons
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const query = e.currentTarget.getAttribute('data-query');
                document.getElementById('query-input').value = query;
            });
        });
        
        // Enter key in textarea
        document.getElementById('query-input').addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.runAgent();
            }
        });
        
        // PDF Upload
        document.getElementById('upload-btn').addEventListener('click', () => {
            document.getElementById('pdf-input').click();
        });
        
        document.getElementById('pdf-input').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.uploadPDF(e.target.files[0]);
            }
        });
        
        // Drag and drop
        const uploadArea = document.getElementById('upload-area');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            
            const files = Array.from(e.dataTransfer.files);
            const pdfFile = files.find(file => file.name.toLowerCase().endsWith('.pdf'));
            
            if (pdfFile) {
                this.uploadPDF(pdfFile);
            } else {
                this.showError('Please upload a PDF file.');
            }
        });
        
        uploadArea.addEventListener('click', () => {
            document.getElementById('pdf-input').click();
        });
        
        // Toggle buttons for collapsible sections
        document.getElementById('toggle-steps').addEventListener('click', () => {
            this.toggleSection('steps-content', 'toggle-steps');
        });
        
        document.getElementById('toggle-outputs').addEventListener('click', () => {
            this.toggleSection('outputs-content', 'toggle-outputs');
        });
        
        // Modal close events
        document.getElementById('close-error').addEventListener('click', () => {
            this.hideModal('error-modal');
        });
        
        document.getElementById('error-ok').addEventListener('click', () => {
            this.hideModal('error-modal');
        });
        
        // Close modal on outside click
        document.getElementById('error-modal').addEventListener('click', (e) => {
            if (e.target.id === 'error-modal') {
                this.hideModal('error-modal');
            }
        });
    }
    
    async checkAgentHealth() {
        try {
            const response = await fetch(`${this.baseURL}/health`);
            const data = await response.json();
            
            const statusDot = document.getElementById('status-dot');
            const statusText = document.getElementById('status-text');
            
            if (data.status === 'healthy') {
                statusDot.className = 'status-dot healthy';
                statusText.textContent = 'Agent Ready';
            } else {
                statusDot.className = 'status-dot error';
                statusText.textContent = 'Agent Error';
            }
        } catch (error) {
            const statusDot = document.getElementById('status-dot');
            const statusText = document.getElementById('status-text');
            
            statusDot.className = 'status-dot error';
            statusText.textContent = 'Connection Error';
            
            console.error('Health check failed:', error);
        }
    }
    
    async runAgent() {
        if (this.isProcessing) return;
        
        const query = document.getElementById('query-input').value.trim();
        if (!query) {
            this.showError('Please enter a query.');
            return;
        }
        
        this.isProcessing = true;
        this.showLoading();
        this.updateLoadingStep('step-analyze', 'active');
        
        try {
            const requestBody = {
                query: query,
                context: {}
            };
            
            // Add uploaded file context if available
            if (this.currentUpload) {
                requestBody.context.uploaded_file = this.currentUpload;
            }
            
            this.updateLoadingStatus('Analyzing your query...');
            
            const response = await fetch(`${this.baseURL}/agent`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.updateLoadingStep('step-analyze', 'completed');
            this.updateLoadingStep('step-select', 'active');
            this.updateLoadingStatus('Selecting appropriate tools...');
            
            const data = await response.json();
            
            this.updateLoadingStep('step-select', 'completed');
            this.updateLoadingStep('step-execute', 'active');
            this.updateLoadingStatus('Executing tools...');
            
            // Simulate processing delay for better UX
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.updateLoadingStep('step-execute', 'completed');
            this.updateLoadingStep('step-generate', 'active');
            this.updateLoadingStatus('Generating final answer...');
            
            await new Promise(resolve => setTimeout(resolve, 500));
            this.updateLoadingStep('step-generate', 'completed');
            
            this.hideLoading();
            this.displayResults(data);
            
        } catch (error) {
            console.error('Error processing query:', error);
            this.hideLoading();
            this.showError(`Error processing your request: ${error.message}`);
        } finally {
            this.isProcessing = false;
        }
    }
    
    async uploadPDF(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            this.showError('Please select a PDF file.');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        const statusEl = document.getElementById('upload-status');
        statusEl.className = 'upload-status';
        statusEl.textContent = 'Uploading...';
        statusEl.style.display = 'block';
        
        try {
            const response = await fetch(`${this.baseURL}/upload-pdf`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                statusEl.className = 'upload-status success';
                statusEl.innerHTML = `
                    <i class="fas fa-check-circle"></i> 
                    ${file.name} uploaded successfully! 
                    You can now ask questions about this PDF.
                `;
                
                this.currentUpload = {
                    filename: data.filename,
                    file_path: data.file_path,
                    size_bytes: data.size_bytes
                };
                
                this.loadUploadedFiles();
                
                // Clear the file input
                document.getElementById('pdf-input').value = '';
            } else {
                throw new Error(data.error || 'Upload failed');
            }
            
        } catch (error) {
            console.error('Upload error:', error);
            statusEl.className = 'upload-status error';
            statusEl.innerHTML = `
                <i class="fas fa-exclamation-circle"></i> 
                Upload failed: ${error.message}
            `;
        }
    }
    
    async loadUploadedFiles() {
        try {
            const response = await fetch(`${this.baseURL}/uploads`);
            const data = await response.json();
            
            const filesContainer = document.getElementById('uploaded-files');
            const filesList = document.getElementById('files-list');
            
            if (data.success && data.uploads.length > 0) {
                filesContainer.style.display = 'block';
                filesList.innerHTML = '';
                
                data.uploads.forEach(file => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    fileItem.innerHTML = `
                        <div class="file-info">
                            <i class="fas fa-file-pdf"></i>
                            <div class="file-details">
                                <div class="file-name">${file.filename}</div>
                                <div class="file-meta">${file.size_human} • Uploaded ${new Date(file.upload_time).toLocaleString()}</div>
                            </div>
                        </div>
                        <button class="btn btn-small btn-secondary" onclick="mcpAgent.deleteFile('${file.filename}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    `;
                    filesList.appendChild(fileItem);
                });
                
                // Set current upload to the most recent file
                if (data.uploads.length > 0) {
                    const latestFile = data.uploads[0];
                    this.currentUpload = {
                        filename: latestFile.filename,
                        file_path: latestFile.file_path,
                        size_bytes: latestFile.size_bytes
                    };
                }
            } else {
                filesContainer.style.display = 'none';
                this.currentUpload = null;
            }
            
        } catch (error) {
            console.error('Error loading uploaded files:', error);
        }
    }
    
    async deleteFile(filename) {
        if (!confirm(`Are you sure you want to delete ${filename}?`)) {
            return;
        }
        
        try {
            const response = await fetch(`${this.baseURL}/uploads/${filename}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // If deleted file was the current upload, clear it
                if (this.currentUpload && this.currentUpload.filename === filename) {
                    this.currentUpload = null;
                }
                
                this.loadUploadedFiles();
            } else {
                throw new Error(data.error || 'Delete failed');
            }
            
        } catch (error) {
            console.error('Delete error:', error);
            this.showError(`Error deleting file: ${error.message}`);
        }
    }
    
    displayResults(data) {
        const resultsSection = document.getElementById('results-section');
        const finalAnswerEl = document.getElementById('final-answer');
        const executionTimeEl = document.getElementById('execution-time');
        const toolsUsedEl = document.getElementById('tools-used');
        const stepsList = document.getElementById('steps-list');
        const rawOutputs = document.getElementById('raw-outputs');
        
        // Show results section
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        
        // Display final answer
        finalAnswerEl.innerHTML = this.formatText(data.final_answer);
        
        // Display execution info
        executionTimeEl.textContent = `${data.execution_time_seconds.toFixed(2)}s`;
        toolsUsedEl.textContent = `${data.tools_used.length} tool(s): ${data.tools_used.join(', ')}`;
        
        // Display steps
        stepsList.innerHTML = '';
        data.steps.forEach((step, index) => {
            const li = document.createElement('li');
            li.textContent = step;
            
            // Add error styling for failed steps
            if (step.includes('failed:') || step.includes('✗')) {
                li.classList.add('error');
            }
            
            stepsList.appendChild(li);
        });
        
        // Display raw outputs
        rawOutputs.innerHTML = '';
        data.raw_outputs.forEach((output, index) => {
            const outputItem = document.createElement('div');
            outputItem.className = 'output-item';
            
            const isSuccess = output.success;
            const toolName = output.tool_name || `Tool ${index + 1}`;
            
            outputItem.innerHTML = `
                <div class="output-header">
                    <div class="tool-name">
                        <i class="fas fa-cog"></i> ${toolName}
                    </div>
                    <div class="${isSuccess ? 'success-badge' : 'error-badge'}">
                        ${isSuccess ? 'SUCCESS' : 'ERROR'}
                    </div>
                </div>
                <div class="output-data">${JSON.stringify(output, null, 2)}</div>
            `;
            
            rawOutputs.appendChild(outputItem);
        });
        
        // Reset collapsible sections
        document.getElementById('steps-content').style.display = 'block';
        document.getElementById('outputs-content').style.display = 'none';
        this.updateToggleButton('toggle-steps', false);
        this.updateToggleButton('toggle-outputs', true);
    }
    
    formatText(text) {
        // Simple text formatting for better readability
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }
    
    clearQuery() {
        document.getElementById('query-input').value = '';
        document.getElementById('results-section').style.display = 'none';
    }
    
    showLoading() {
        document.getElementById('loading-overlay').style.display = 'flex';
        document.getElementById('run-agent-btn').disabled = true;
        
        // Reset loading steps
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active', 'completed');
        });
    }
    
    hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
        document.getElementById('run-agent-btn').disabled = false;
    }
    
    updateLoadingStatus(status) {
        document.getElementById('loading-status').textContent = status;
    }
    
    updateLoadingStep(stepId, state) {
        const step = document.getElementById(stepId);
        step.classList.remove('active', 'completed');
        if (state) {
            step.classList.add(state);
        }
    }
    
    toggleSection(contentId, toggleBtnId) {
        const content = document.getElementById(contentId);
        const isHidden = content.style.display === 'none';
        
        content.style.display = isHidden ? 'block' : 'none';
        this.updateToggleButton(toggleBtnId, !isHidden);
    }
    
    updateToggleButton(buttonId, isCollapsed) {
        const button = document.getElementById(buttonId);
        const icon = button.querySelector('i');
        
        if (isCollapsed) {
            icon.className = 'fas fa-chevron-right';
        } else {
            icon.className = 'fas fa-chevron-down';
        }
    }
    
    showError(message) {
        document.getElementById('error-message').textContent = message;
        document.getElementById('error-modal').style.display = 'flex';
    }
    
    hideModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.mcpAgent = new MCPAgent();
});

// Global functions for inline event handlers
function selectExample(query) {
    document.getElementById('query-input').value = query;
}

// Service worker registration for PWA capabilities (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
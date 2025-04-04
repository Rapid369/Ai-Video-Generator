// Main JavaScript file for AI Video Generator SaaS

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Project generation API calls
    setupProjectGenerationHandlers();
    
    // API key visibility toggle
    setupAPIKeyToggles();
    
    // Form validation
    setupFormValidation();
});

// Setup handlers for project generation buttons
function setupProjectGenerationHandlers() {
    // Individual step generation buttons
    const stepButtons = {
        'generate-idea': 'idea',
        'generate-image': 'image',
        'generate-video': 'video',
        'generate-music': 'music',
        'generate-voice': 'voice',
        'create-final-video': 'final'
    };
    
    // Add click handlers to each button if it exists
    Object.keys(stepButtons).forEach(buttonId => {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', function() {
                const projectId = getProjectIdFromUrl();
                if (!projectId) return;
                
                // Disable button and show loading state
                this.disabled = true;
                const originalText = this.innerHTML;
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                
                // Make API call
                generateProjectStep(projectId, stepButtons[buttonId])
                    .then(response => {
                        if (response.status === 'processing' || response.status === 'completed') {
                            // Reload the page to show updated content
                            window.location.reload();
                        } else {
                            // Show error and reset button
                            alert('Error: ' + (response.message || 'Unknown error occurred'));
                            this.disabled = false;
                            this.innerHTML = originalText;
                        }
                    })
                    .catch(error => {
                        console.error('Generation error:', error);
                        alert('An error occurred. Please try again.');
                        this.disabled = false;
                        this.innerHTML = originalText;
                    });
            });
        }
    });
    
    // Generate all button
    const generateAllButton = document.getElementById('generate-all');
    if (generateAllButton) {
        generateAllButton.addEventListener('click', function() {
            const projectId = getProjectIdFromUrl();
            if (!projectId) return;
            
            // Disable button and show loading state
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            
            // Show overlay with progress information
            showGenerationOverlay();
            
            // Make API call
            generateProjectStep(projectId, 'all')
                .then(response => {
                    if (response.status === 'processing') {
                        // Start polling for updates
                        pollGenerationStatus(projectId);
                    } else {
                        // Hide overlay and reload
                        hideGenerationOverlay();
                        window.location.reload();
                    }
                })
                .catch(error => {
                    console.error('Generation error:', error);
                    alert('An error occurred. Please try again.');
                    this.disabled = false;
                    this.innerHTML = 'Generate Complete Video';
                    hideGenerationOverlay();
                });
        });
    }
}

// Make API call to generate a project step
function generateProjectStep(projectId, step) {
    return fetch(`/project/${projectId}/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ step: step })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    });
}

// Poll for generation status updates
function pollGenerationStatus(projectId) {
    const statusInterval = setInterval(() => {
        fetch(`/project/${projectId}/status`)
            .then(response => response.json())
            .then(data => {
                updateGenerationOverlay(data);
                
                if (data.status === 'completed' || data.status === 'error') {
                    clearInterval(statusInterval);
                    setTimeout(() => {
                        hideGenerationOverlay();
                        window.location.reload();
                    }, 1000);
                }
            })
            .catch(error => {
                console.error('Status polling error:', error);
                clearInterval(statusInterval);
                hideGenerationOverlay();
            });
    }, 3000); // Poll every 3 seconds
}

// Show generation overlay with progress information
function showGenerationOverlay() {
    // Create overlay if it doesn't exist
    if (!document.getElementById('generation-overlay')) {
        const overlay = document.createElement('div');
        overlay.id = 'generation-overlay';
        overlay.className = 'spinner-overlay';
        overlay.innerHTML = `
            <div class="spinner-container">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div id="generation-status" class="spinner-text mt-3">
                    Starting generation process...
                </div>
                <div id="generation-progress" class="mt-3" style="width: 300px;">
                    <div class="progress">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    }
}

// Update generation overlay with status information
function updateGenerationOverlay(data) {
    const statusElement = document.getElementById('generation-status');
    const progressBar = document.querySelector('#generation-progress .progress-bar');
    
    if (statusElement && progressBar) {
        statusElement.textContent = data.message || 'Processing...';
        
        // Update progress bar
        if (data.progress) {
            progressBar.style.width = `${data.progress}%`;
        }
    }
}

// Hide generation overlay
function hideGenerationOverlay() {
    const overlay = document.getElementById('generation-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Get project ID from URL
function getProjectIdFromUrl() {
    const urlPath = window.location.pathname;
    const matches = urlPath.match(/\/project\/(\d+)/);
    return matches ? matches[1] : null;
}

// Setup API key visibility toggles
function setupAPIKeyToggles() {
    const apiKeyInputs = document.querySelectorAll('input[type="password"][id$="_api_key"]');
    
    apiKeyInputs.forEach(input => {
        const container = input.parentElement;
        
        // Create toggle button
        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'btn btn-sm btn-outline-secondary position-absolute end-0 top-0 mt-2 me-2';
        toggleButton.innerHTML = '<i class="bi bi-eye"></i>';
        toggleButton.addEventListener('click', function() {
            if (input.type === 'password') {
                input.type = 'text';
                this.innerHTML = '<i class="bi bi-eye-slash"></i>';
            } else {
                input.type = 'password';
                this.innerHTML = '<i class="bi bi-eye"></i>';
            }
        });
        
        // Add position relative to container if not already set
        if (window.getComputedStyle(container).position === 'static') {
            container.style.position = 'relative';
        }
        
        container.appendChild(toggleButton);
    });
}

// Setup form validation
function setupFormValidation() {
    // Get all forms with the class 'needs-validation'
    const forms = document.querySelectorAll('.needs-validation');
    
    // Loop over them and prevent submission
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Password confirmation validation
    const passwordField = document.getElementById('password');
    const confirmPasswordField = document.getElementById('confirm_password');
    
    if (passwordField && confirmPasswordField) {
        confirmPasswordField.addEventListener('input', function() {
            if (this.value !== passwordField.value) {
                this.setCustomValidity('Passwords do not match');
            } else {
                this.setCustomValidity('');
            }
        });
        
        passwordField.addEventListener('input', function() {
            if (confirmPasswordField.value !== '') {
                if (confirmPasswordField.value !== this.value) {
                    confirmPasswordField.setCustomValidity('Passwords do not match');
                } else {
                    confirmPasswordField.setCustomValidity('');
                }
            }
        });
    }
}

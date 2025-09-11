// JavaScript for the transcription game application

document.addEventListener('DOMContentLoaded', function() {
    console.log('Transcription Game application loaded');
    
    // Load fonts and initialize form controls
    loadAvailableFonts().then(() => {
        initializeFormControls();
    }).catch(error => {
        console.error('Failed to load fonts:', error);
        // Initialize with fallback fonts
        initializeFormControls();
    });
});

function initializeFormControls() {
    // Get form elements
    const textContent = document.getElementById('text-content');
    const fontSizeRange = document.getElementById('font-size');
    const fontSizeInput = document.getElementById('font-size-input');
    const fontSizeValue = document.getElementById('font-size-value');
    const generatePdfBtn = document.getElementById('generate-pdf');
    const fontSelect = document.getElementById('font-select');
    
    // Synchronize font size controls
    function updateFontSize(value) {
        fontSizeRange.value = value;
        fontSizeInput.value = value;
        fontSizeValue.textContent = value;
        
        // Update preview font size (will be implemented in preview task)
        updatePreviewStyles();
    }
    
    // Font size range slider event
    fontSizeRange.addEventListener('input', function() {
        updateFontSize(this.value);
    });
    
    // Font size number input event
    fontSizeInput.addEventListener('input', function() {
        let value = parseInt(this.value);
        
        // Validate range
        if (value < 8) value = 8;
        if (value > 72) value = 72;
        
        this.value = value;
        updateFontSize(value);
    });
    
    // Text content change event
    textContent.addEventListener('input', function() {
        const hasText = this.value.trim().length > 0;
        generatePdfBtn.disabled = !hasText;
        
        // Update preview (will be implemented in preview task)
        updatePreview();
    });
    
    // Font selection change event
    fontSelect.addEventListener('change', async function() {
        // Validate the selected font
        const isValid = await validateSelectedFont();
        
        if (!isValid) {
            console.warn(`Font ${this.value} is not valid, falling back to Helvetica`);
            this.value = 'Helvetica';
        }
        
        // Update preview font (will be implemented in preview task)
        updatePreviewStyles();
    });
    
    // Document size change event
    const documentSize = document.getElementById('document-size');
    documentSize.addEventListener('change', function() {
        // Update preview dimensions (will be implemented in preview task)
        updatePreview();
    });
    
    // Initialize formatting and processing controls
    initializeFormattingControls();
    
    // PDF generation button event
    generatePdfBtn.addEventListener('click', async function() {
        if (await validateForm()) {
            await generatePDF();
        }
    });
    
    // Initialize with default values
    updateFontSize(16);
    
    // Generate initial preview if there's content
    const initialText = textContent.value.trim();
    if (initialText) {
        updatePreview();
    }
}

// Preview update functions with enhanced debouncing
let previewUpdateTimeout = null;
let isPreviewGenerating = false;
let pendingPreviewUpdate = false;

function updatePreview() {
    // Debounce preview updates to reduce server load
    if (previewUpdateTimeout) {
        clearTimeout(previewUpdateTimeout);
    }
    
    // If preview is currently generating, mark for pending update
    if (isPreviewGenerating) {
        pendingPreviewUpdate = true;
        return;
    }
    
    previewUpdateTimeout = setTimeout(() => {
        generatePreview();
    }, 300); // 300ms debounce
}

function updatePreviewStyles() {
    // Trigger a full preview update when styles change with shorter debounce
    if (previewUpdateTimeout) {
        clearTimeout(previewUpdateTimeout);
    }
    
    if (isPreviewGenerating) {
        pendingPreviewUpdate = true;
        return;
    }
    
    previewUpdateTimeout = setTimeout(() => {
        generatePreview();
    }, 150); // Shorter debounce for style changes
}

async function generatePreview() {
    // Prevent concurrent preview generation
    if (isPreviewGenerating) {
        pendingPreviewUpdate = true;
        return;
    }
    
    try {
        isPreviewGenerating = true;
        pendingPreviewUpdate = false;
        
        const formData = getFormData();
        
        // Skip preview if no text content
        if (!formData.text_content.trim()) {
            displayEmptyPreview();
            return;
        }
        
        // Client-side validation before sending request
        const validationErrors = validatePreviewData(formData);
        if (validationErrors.length > 0) {
            showPreviewError(`Invalid input: ${validationErrors.join(', ')}`);
            return;
        }
        
        // Show loading state with smooth transition
        showPreviewLoading();
        
        // Add timeout to prevent hanging requests
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout for preview
        
        const response = await fetch('/api/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: formData.text_content,
                options: {
                    font_name: formData.font_name,
                    font_size: formData.font_size,
                    document_size: formData.document_size,
                    guidelines: formData.ruled_lines || formData.dotted_lines,
                    guideline_type: formData.ruled_lines ? 'ruled' : (formData.dotted_lines ? 'dotted' : 'none'),
                    black_text: formData.black_text,
                    gray_text: formData.gray_text,
                    blank_lines: formData.blank_lines
                }
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            
            // Handle specific error types
            if (response.status === 400) {
                if (errorData.error_code === 'VALIDATION_ERROR') {
                    showPreviewError(`Validation error: ${errorData.error}`);
                } else if (errorData.error_code === 'CONTENT_TOO_LARGE') {
                    showPreviewError('Content is too large for preview. Please reduce the text length.');
                } else {
                    showPreviewError(`Invalid input: ${errorData.error || 'Please check your input'}`);
                }
            } else if (response.status === 500) {
                if (errorData.error_code === 'PREVIEW_ERROR') {
                    showPreviewError('Preview generation failed. Please try different settings.');
                } else {
                    showPreviewError('Server error during preview generation. Please try again.');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${errorData.error || response.statusText}`);
            }
            return;
        }
        
        const data = await response.json();
        
        if (data.success && data.data) {
            displayPreview(data.data.preview_html);
            
            // Show warnings if any
            if (data.warnings && data.warnings.length > 0) {
                const warningMessages = data.warnings.map(w => w.message).join('; ');
                console.warn('Preview warnings:', warningMessages);
                
                // Show font fallback warnings to user
                const fontWarnings = data.warnings.filter(w => w.code === 'FONT_FALLBACK');
                if (fontWarnings.length > 0) {
                    showNotification('Font was substituted due to availability issues.', 'warning');
                }
            }
        } else {
            showPreviewError(data.error || 'Failed to generate preview');
        }
        
    } catch (error) {
        console.error('Preview generation error:', error);
        
        let errorMessage = 'Preview generation failed. Please try again.';
        
        if (error.name === 'AbortError') {
            errorMessage = 'Preview generation timed out. Please try again with less content.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Unable to connect to preview service. Please check your connection.';
        } else if (error.message.includes('NetworkError')) {
            errorMessage = 'Network error during preview generation. Please check your connection.';
        }
        
        showPreviewError(errorMessage);
        
    } finally {
        isPreviewGenerating = false;
        
        // Handle pending updates
        if (pendingPreviewUpdate) {
            pendingPreviewUpdate = false;
            setTimeout(() => updatePreview(), 100);
        }
    }
}

function validatePreviewData(formData) {
    const errors = [];
    
    // Validate text length
    if (formData.text_content.length > 10000) {
        errors.push('Text is too long (max 10,000 characters)');
    }
    
    // Validate font size
    if (formData.font_size < 6 || formData.font_size > 72) {
        errors.push('Font size must be between 6 and 72');
    }
    
    // Validate document size
    const validSizes = ['A4', 'Letter', 'Legal'];
    if (!validSizes.includes(formData.document_size)) {
        errors.push('Invalid document size');
    }
    
    // Validate font name
    if (!formData.font_name || formData.font_name.trim() === '') {
        errors.push('Font name is required');
    }
    
    return errors;
}

function showPreviewLoading() {
    const previewContainer = document.getElementById('preview-container');
    
    // Add fade-out effect if there's existing content
    previewContainer.style.opacity = '0.6';
    previewContainer.style.transition = 'opacity 0.3s ease';
    
    setTimeout(() => {
        previewContainer.innerHTML = `
            <div class="preview-loading">
                <div class="loading-spinner"></div>
                <div class="loading-text">Generating preview...</div>
            </div>
        `;
        previewContainer.style.opacity = '1';
    }, 150);
}

function displayPreview(previewHtml) {
    const previewContainer = document.getElementById('preview-container');
    
    // Smooth transition for preview updates
    previewContainer.style.opacity = '0';
    previewContainer.style.transition = 'opacity 0.3s ease';
    
    setTimeout(() => {
        previewContainer.innerHTML = previewHtml;
        previewContainer.style.opacity = '1';
        
        // Add subtle animation to the preview document
        const previewDoc = previewContainer.querySelector('.preview-document');
        if (previewDoc) {
            previewDoc.style.transform = 'scale(0.95)';
            previewDoc.style.transition = 'transform 0.3s ease';
            setTimeout(() => {
                previewDoc.style.transform = 'scale(1)';
            }, 50);
        }
    }, 150);
}

function displayEmptyPreview() {
    const previewContainer = document.getElementById('preview-container');
    previewContainer.style.opacity = '0';
    previewContainer.style.transition = 'opacity 0.3s ease';
    
    setTimeout(() => {
        previewContainer.innerHTML = `
            <div class="preview-placeholder">
                Enter text above to see preview
            </div>
        `;
        previewContainer.style.opacity = '1';
    }, 150);
}

function showPreviewError(errorMessage) {
    const previewContainer = document.getElementById('preview-container');
    previewContainer.style.opacity = '0';
    previewContainer.style.transition = 'opacity 0.3s ease';
    
    setTimeout(() => {
        previewContainer.innerHTML = `
            <div class="preview-error">
                <div class="error-icon">⚠️</div>
                <div class="error-message">${errorMessage}</div>
                <button class="retry-button" onclick="updatePreview()">Retry</button>
            </div>
        `;
        previewContainer.style.opacity = '1';
    }, 150);
}

// Enhanced form validation with comprehensive error handling
async function validateForm() {
    const errors = [];
    const warnings = [];
    
    const textContent = document.getElementById('text-content');
    const fontSelect = document.getElementById('font-select');
    const fontSize = document.getElementById('font-size');
    const documentSize = document.getElementById('document-size');
    
    // Validate text content
    const text = textContent.value;
    if (!text || !text.trim()) {
        errors.push({
            field: 'text-content',
            message: 'Please enter some text content.',
            element: textContent
        });
    } else if (text.length > 10000) {
        errors.push({
            field: 'text-content',
            message: `Text is too long (${text.length} characters). Maximum allowed is 10,000 characters.`,
            element: textContent
        });
    } else if (text.length > 5000) {
        warnings.push({
            field: 'text-content',
            message: `Large text content (${text.length} characters) may take longer to process.`
        });
    }
    
    // Validate font selection
    if (!fontSelect.value) {
        errors.push({
            field: 'font-select',
            message: 'Please select a font.',
            element: fontSelect
        });
    } else {
        // Validate font availability
        try {
            const isFontValid = await validateSelectedFont();
            if (!isFontValid) {
                errors.push({
                    field: 'font-select',
                    message: 'The selected font is not available. Please choose a different font.',
                    element: fontSelect
                });
            }
        } catch (error) {
            console.error('Font validation error:', error);
            warnings.push({
                field: 'font-select',
                message: 'Unable to verify font availability. Proceeding with selected font.'
            });
        }
    }
    
    // Validate font size range
    const fontSizeValue = parseInt(fontSize.value);
    if (isNaN(fontSizeValue) || fontSizeValue < 6 || fontSizeValue > 72) {
        errors.push({
            field: 'font-size',
            message: 'Font size must be between 6 and 72 pixels.',
            element: fontSize
        });
    }
    
    // Validate document size
    const validDocumentSizes = ['A4', 'Letter', 'Legal'];
    if (!validDocumentSizes.includes(documentSize.value)) {
        errors.push({
            field: 'document-size',
            message: 'Please select a valid document size.',
            element: documentSize
        });
    }
    
    // Display validation results
    if (errors.length > 0) {
        displayValidationErrors(errors);
        // Focus on first error field
        if (errors[0].element) {
            errors[0].element.focus();
        }
        return false;
    }
    
    if (warnings.length > 0) {
        displayValidationWarnings(warnings);
    }
    
    return true;
}

function displayValidationErrors(errors) {
    // Clear previous error displays
    clearValidationMessages();
    
    // Create error summary
    const errorMessages = errors.map(error => error.message).join('\n');
    
    // Show user-friendly error notification
    showNotification(`Validation failed:\n${errorMessages}`, 'error');
    
    // Add visual indicators to error fields
    errors.forEach(error => {
        if (error.element) {
            error.element.classList.add('validation-error');
            
            // Remove error class after user interaction
            const removeError = () => {
                error.element.classList.remove('validation-error');
                error.element.removeEventListener('input', removeError);
                error.element.removeEventListener('change', removeError);
            };
            
            error.element.addEventListener('input', removeError);
            error.element.addEventListener('change', removeError);
        }
    });
}

function displayValidationWarnings(warnings) {
    const warningMessages = warnings.map(warning => warning.message).join('\n');
    showNotification(`Warning:\n${warningMessages}`, 'warning');
}

function clearValidationMessages() {
    // Remove validation error classes
    document.querySelectorAll('.validation-error').forEach(element => {
        element.classList.remove('validation-error');
    });
    
    // Remove existing notifications
    document.querySelectorAll('.notification').forEach(notification => {
        notification.remove();
    });
}

function initializeFormattingControls() {
    // Get formatting control elements
    const ruledLinesCheckbox = document.getElementById('ruled-lines');
    const dottedLinesCheckbox = document.getElementById('dotted-lines');
    const blackTextCheckbox = document.getElementById('black-text');
    const grayTextCheckbox = document.getElementById('gray-text');
    const blankLinesCheckbox = document.getElementById('blank-lines');
    const removeSpacesBtn = document.getElementById('remove-spaces');
    const removeLineBreaksBtn = document.getElementById('remove-line-breaks');
    const textContent = document.getElementById('text-content');
    
    // Guideline options - ensure only one is selected at a time
    ruledLinesCheckbox.addEventListener('change', function() {
        if (this.checked) {
            dottedLinesCheckbox.checked = false;
        }
        updatePreview();
    });
    
    dottedLinesCheckbox.addEventListener('change', function() {
        if (this.checked) {
            ruledLinesCheckbox.checked = false;
        }
        updatePreview();
    });
    
    // Text color options - allow both to be selected
    blackTextCheckbox.addEventListener('change', function() {
        updatePreview();
    });
    
    grayTextCheckbox.addEventListener('change', function() {
        updatePreview();
    });
    
    // Blank lines option
    blankLinesCheckbox.addEventListener('change', function() {
        updatePreview();
    });
    
    // Text processing buttons
    removeSpacesBtn.addEventListener('click', function() {
        const currentText = textContent.value;
        const processedText = currentText.replace(/\s+/g, '');
        textContent.value = processedText;
        
        // Trigger input event to update preview and enable/disable PDF button
        textContent.dispatchEvent(new Event('input'));
        
        // Provide visual feedback
        showProcessingFeedback(this, 'Spaces removed!');
    });
    
    removeLineBreaksBtn.addEventListener('click', function() {
        const currentText = textContent.value;
        const processedText = currentText.replace(/\n+/g, ' ').replace(/\s+/g, ' ').trim();
        textContent.value = processedText;
        
        // Trigger input event to update preview and enable/disable PDF button
        textContent.dispatchEvent(new Event('input'));
        
        // Provide visual feedback
        showProcessingFeedback(this, 'Line breaks removed!');
    });
}

// Show temporary feedback for text processing buttons
function showProcessingFeedback(button, message) {
    const originalText = button.textContent;
    button.textContent = message;
    button.disabled = true;
    
    setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
    }, 1500);
}

// Font management functions
async function loadAvailableFonts() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
        
        const response = await fetch('/api/fonts', {
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.data) {
            populateFontSelect(data.data);
            console.log(`Loaded ${data.data.length} fonts`);
            
            // Show warnings if any
            if (data.warnings && data.warnings.length > 0) {
                const fallbackWarning = data.warnings.find(w => w.code === 'FONT_FALLBACK');
                if (fallbackWarning) {
                    showNotification('Using fallback fonts due to font system issues.', 'warning');
                }
            }
        } else {
            console.warn('Font API returned no data, using fallback');
            throw new Error('No font data received from API');
        }
        
    } catch (error) {
        console.error('Error loading fonts:', error);
        
        let errorMessage = 'Failed to load fonts. Using fallback fonts.';
        
        if (error.name === 'AbortError') {
            errorMessage = 'Font loading timed out. Using fallback fonts.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Unable to connect to font service. Using fallback fonts.';
        }
        
        showNotification(errorMessage, 'warning');
        populateFallbackFonts();
    }
}

function populateFontSelect(fonts) {
    const fontSelect = document.getElementById('font-select');
    
    // Clear existing options
    fontSelect.innerHTML = '';
    
    // Add fonts to select
    fonts.forEach(font => {
        const option = document.createElement('option');
        option.value = font.name;
        option.textContent = font.display_name;
        option.dataset.fontType = font.type;
        fontSelect.appendChild(option);
    });
    
    // Set default selection (prefer Helvetica if available)
    const helveticaOption = fontSelect.querySelector('option[value="Helvetica"]');
    if (helveticaOption) {
        helveticaOption.selected = true;
    }
}

function populateFallbackFonts() {
    const fontSelect = document.getElementById('font-select');
    const fallbackFonts = [
        { name: 'Helvetica', display_name: 'Helvetica' },
        { name: 'Times-Roman', display_name: 'Times Roman' },
        { name: 'Courier', display_name: 'Courier' }
    ];
    
    fontSelect.innerHTML = '';
    fallbackFonts.forEach(font => {
        const option = document.createElement('option');
        option.value = font.name;
        option.textContent = font.display_name;
        fontSelect.appendChild(option);
    });
}

async function validateSelectedFont() {
    const fontSelect = document.getElementById('font-select');
    const selectedFont = fontSelect.value;
    
    if (!selectedFont) return false;
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
        
        const response = await fetch('/api/fonts/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ font_name: selectedFont }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('Font validation failed:', errorData);
            
            // Handle specific error types
            if (response.status === 400 && errorData.error_code === 'INVALID_FONT') {
                showNotification(`Font "${selectedFont}" is not available. Please select a different font.`, 'error');
                return false;
            }
            
            throw new Error(`HTTP ${response.status}: ${errorData.error || response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            console.error('Font validation unsuccessful:', data);
            return false;
        }
        
        // Handle font fallback warnings
        if (data.warnings && data.warnings.length > 0) {
            const fallbackWarning = data.warnings.find(w => w.code === 'INVALID_FONT');
            if (fallbackWarning) {
                showNotification(`Font "${selectedFont}" was substituted with a fallback font.`, 'warning');
            }
        }
        
        return data.data.is_valid;
        
    } catch (error) {
        console.error('Font validation error:', error);
        
        if (error.name === 'AbortError') {
            showNotification('Font validation timed out. Please try again.', 'warning');
        } else if (error.message.includes('Failed to fetch')) {
            showNotification('Unable to validate font. Please check your connection.', 'warning');
        } else {
            showNotification('Font validation failed. Proceeding with selected font.', 'warning');
        }
        
        // Return true to allow proceeding with potentially invalid font
        return true;
    }
}

async function getFontMetrics(fontName, fontSize) {
    try {
        const response = await fetch('/api/fonts/metrics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                font_name: fontName, 
                font_size: fontSize 
            })
        });
        
        const data = await response.json();
        return data.success ? data.metrics : null;
    } catch (error) {
        console.error('Font metrics error:', error);
        return null;
    }
}

// PDF Generation with enhanced error handling and progress indication
async function generatePDF() {
    const generateBtn = document.getElementById('generate-pdf');
    const originalText = generateBtn.textContent;
    
    try {
        const formData = getFormData();
        
        // Show loading state with progress indication
        generateBtn.textContent = 'Generating PDF...';
        generateBtn.disabled = true;
        generateBtn.classList.add('btn-loading');
        
        // Add timeout for PDF generation
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        const response = await fetch('/api/generate-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: formData.text_content,
                options: {
                    font_name: formData.font_name,
                    font_size: formData.font_size,
                    document_size: formData.document_size,
                    guidelines: formData.ruled_lines || formData.dotted_lines,
                    guideline_type: formData.ruled_lines ? 'ruled' : (formData.dotted_lines ? 'dotted' : 'none'),
                    black_text: formData.black_text,
                    gray_text: formData.gray_text,
                    blank_lines: formData.blank_lines
                }
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            // Update button to show download progress
            generateBtn.textContent = 'Downloading...';
            
            // Create blob from response
            const blob = await response.blob();
            
            // Validate PDF blob
            if (blob.size === 0) {
                throw new Error('Generated PDF is empty');
            }
            
            // Generate filename with timestamp
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
            const filename = `handwriting_practice_${timestamp}.pdf`;
            
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            setTimeout(() => {
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }, 100);
            
            // Show success feedback with animation
            generateBtn.textContent = '✓ PDF Downloaded!';
            generateBtn.classList.remove('btn-loading');
            generateBtn.classList.add('btn-success');
            
            setTimeout(() => {
                generateBtn.textContent = originalText;
                generateBtn.disabled = false;
                generateBtn.classList.remove('btn-success');
            }, 2500);
            
        } else {
            // Handle HTTP errors
            let errorMessage = 'PDF generation failed';
            
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorData.details || errorMessage;
            } catch (parseError) {
                errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            }
            
            throw new Error(errorMessage);
        }
        
    } catch (error) {
        console.error('PDF generation error:', error);
        
        // Show error feedback with specific error handling
        generateBtn.classList.remove('btn-loading');
        generateBtn.classList.add('btn-error');
        
        let userMessage = 'PDF generation failed';
        
        if (error.name === 'AbortError') {
            generateBtn.textContent = '⚠ Timed Out';
            userMessage = 'PDF generation timed out. The content might be too large or the server is busy. Please try again.';
        } else if (error.message.includes('Failed to fetch')) {
            generateBtn.textContent = '⚠ Connection Error';
            userMessage = 'Unable to connect to the server. Please check your internet connection and try again.';
        } else if (error.message.includes('too long')) {
            generateBtn.textContent = '⚠ Content Too Large';
            userMessage = 'The text content is too large. Please reduce the amount of text and try again.';
        } else {
            generateBtn.textContent = '⚠ Generation Failed';
            userMessage = `PDF generation failed: ${error.message}`;
        }
        
        // Show user-friendly error message
        showNotification(userMessage, 'error');
        
        // Reset button after delay
        setTimeout(() => {
            generateBtn.textContent = originalText;
            generateBtn.disabled = false;
            generateBtn.classList.remove('btn-error');
        }, 4000);
    }
}

// Enhanced notification system for better user feedback
function showNotification(message, type = 'info', duration = 5000) {
    // Remove existing notifications of the same type to avoid spam
    const existingNotifications = document.querySelectorAll(`.notification-${type}`);
    existingNotifications.forEach(n => n.remove());
    
    // Create notification element with enhanced styling
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    // Add appropriate icon based on type
    const icons = {
        'error': '❌',
        'warning': '⚠️',
        'success': '✅',
        'info': 'ℹ️'
    };
    
    const icon = icons[type] || icons['info'];
    
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${icon}</span>
            <span class="notification-message">${escapeHtml(message)}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()" aria-label="Close notification">×</button>
        </div>
    `;
    
    // Add to page with animation
    document.body.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
        notification.classList.add('notification-show');
    }, 10);
    
    // Auto-remove after specified duration
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.remove('notification-show');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300); // Wait for fade-out animation
            }
        }, duration);
    }
    
    return notification;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Enhanced error display for API responses
function handleApiError(error, response = null, context = '') {
    console.error(`API Error ${context}:`, error);
    
    let userMessage = 'An unexpected error occurred. Please try again.';
    let notificationType = 'error';
    
    if (response) {
        // Handle structured error responses
        if (response.error_code) {
            switch (response.error_code) {
                case 'VALIDATION_ERROR':
                    userMessage = `Validation failed: ${response.error}`;
                    break;
                case 'FONT_ERROR':
                    userMessage = `Font error: ${response.error}`;
                    if (response.suggestion) {
                        userMessage += ` ${response.suggestion}`;
                    }
                    break;
                case 'PDF_GENERATION_ERROR':
                    userMessage = `PDF generation failed: ${response.error}`;
                    if (response.suggestions && response.suggestions.length > 0) {
                        userMessage += ` Try: ${response.suggestions.join(', ')}`;
                    }
                    break;
                case 'PREVIEW_ERROR':
                    userMessage = `Preview failed: ${response.error}`;
                    notificationType = 'warning';
                    break;
                case 'CONTENT_TOO_LARGE':
                    userMessage = response.error;
                    break;
                case 'RATE_LIMIT_ERROR':
                    userMessage = `${response.error} Please wait ${response.retry_after || 60} seconds.`;
                    break;
                default:
                    userMessage = response.error || userMessage;
            }
        } else {
            userMessage = response.error || response.message || userMessage;
        }
    } else if (error) {
        // Handle different error types
        if (error.name === 'AbortError') {
            userMessage = 'Request timed out. Please try again.';
        } else if (error.message.includes('Failed to fetch')) {
            userMessage = 'Connection failed. Please check your internet connection.';
        } else if (error.message.includes('NetworkError')) {
            userMessage = 'Network error. Please check your connection and try again.';
        } else {
            userMessage = `Error: ${error.message}`;
        }
    }
    
    showNotification(userMessage, notificationType);
    return userMessage;
}

// Get form data as object
function getFormData() {
    return {
        text_content: document.getElementById('text-content').value,
        font_name: document.getElementById('font-select').value,
        font_size: parseInt(document.getElementById('font-size').value),
        document_size: document.getElementById('document-size').value,
        ruled_lines: document.getElementById('ruled-lines').checked,
        dotted_lines: document.getElementById('dotted-lines').checked,
        black_text: document.getElementById('black-text').checked,
        gray_text: document.getElementById('gray-text').checked,
        blank_lines: document.getElementById('blank-lines').checked
    };
}
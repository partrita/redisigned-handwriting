// JavaScript for the transcription game application

document.addEventListener('DOMContentLoaded', function () {
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
    // Configure font upload
    setupFontUpload();

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
    }

    // Font size range slider event
    fontSizeRange.addEventListener('input', function () {
        updateFontSize(this.value);
    });

    // Font size number input event
    fontSizeInput.addEventListener('input', function () {
        let value = parseInt(this.value);

        // Validate range
        if (value < 8) value = 8;
        if (value > 72) value = 72;

        this.value = value;
        updateFontSize(value);
    });

    // Text content change event
    textContent.addEventListener('input', function () {
        const hasText = this.value.trim().length > 0;
        generatePdfBtn.disabled = !hasText;
    });

    // Font selection change event
    fontSelect.addEventListener('change', async function () {
        // Validate the selected font
        const isValid = await validateSelectedFont();

        if (!isValid) {
            console.warn(`Font ${this.value} is not valid, falling back to Helvetica`);
            this.value = 'Helvetica';
        }

        // Load font preview
        loadFontPreview(this.value);
    });

    // Initialize formatting and processing controls
    initializeFormattingControls();

    // PDF generation button event
    generatePdfBtn.addEventListener('click', async function () {
        if (await validateForm()) {
            await generatePDF();
        }
    });

    // Initialize with default values
    updateFontSize(16);
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
    const validDocumentSizes = ['A4', 'Letter', 'Legal', 'A3', 'A5'];
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
    const removeSpacesBtn = document.getElementById('remove-spaces');
    const removeLineBreaksBtn = document.getElementById('remove-line-breaks');
    const textContent = document.getElementById('text-content');

    // Guideline options - ensure only one is selected at a time
    ruledLinesCheckbox.addEventListener('change', function () {
        if (this.checked) {
            dottedLinesCheckbox.checked = false;
        }
    });

    dottedLinesCheckbox.addEventListener('change', function () {
        if (this.checked) {
            ruledLinesCheckbox.checked = false;
        }
    });

    // Text processing buttons
    removeSpacesBtn.addEventListener('click', function () {
        const currentText = textContent.value;
        const processedText = currentText.replace(/\s+/g, '');
        textContent.value = processedText;

        // Trigger input event to enable/disable PDF button
        textContent.dispatchEvent(new Event('input'));

        // Provide visual feedback
        showProcessingFeedback(this, 'Spaces removed!');
    });

    removeLineBreaksBtn.addEventListener('click', function () {
        const currentText = textContent.value;
        const processedText = currentText.replace(/\n+/g, ' ').replace(/\s+/g, ' ').trim();
        textContent.value = processedText;

        // Trigger input event to enable/disable PDF button
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

    // Load preview for the finally selected font
    loadFontPreview(fontSelect.value);
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

    // Load preview for the finally selected font
    loadFontPreview(fontSelect.value);
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

// PDF Generation with enhanced error handling
async function generatePDF() {
    const generateBtn = document.getElementById('generate-pdf');
    const originalText = generateBtn.textContent;

    try {
        const formData = getFormData();

        // Show loading state
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

// Enhanced notification system
function showNotification(message, type = 'info', duration = 5000) {
    // Remove existing notifications of the same type to avoid spam
    const existingNotifications = document.querySelectorAll(`.notification-${type}`);
    existingNotifications.forEach(n => n.remove());

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;

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
                }, 300);
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

// Font preview functionality
let fontPreviewCache = {};
let fontPreviewAbortController = null;

async function loadFontPreview(fontName) {
    const previewImage = document.getElementById('font-preview-image');
    const previewLoading = document.getElementById('font-preview-loading');
    const previewFallback = document.getElementById('font-preview-fallback');

    if (!fontName) {
        previewImage.style.display = 'none';
        previewLoading.style.display = 'none';
        previewFallback.style.display = 'block';
        return;
    }

    // Check cache first
    if (fontPreviewCache[fontName]) {
        previewImage.src = fontPreviewCache[fontName];
        previewImage.style.display = 'block';
        previewLoading.style.display = 'none';
        previewFallback.style.display = 'none';
        return;
    }

    // Cancel previous request if still pending
    if (fontPreviewAbortController) {
        fontPreviewAbortController.abort();
    }

    // Show loading state
    previewLoading.style.display = 'block';
    previewImage.style.display = 'none';
    previewFallback.style.display = 'none';

    try {
        fontPreviewAbortController = new AbortController();
        const timeoutId = setTimeout(() => fontPreviewAbortController.abort(), 8000);

        const params = new URLSearchParams({
            font_name: fontName,
            preview_text: 'The quick brown fox jumps over the lazy dog',
            font_size: '28'
        });

        const response = await fetch(`/api/fonts/preview-image?${params}`, {
            signal: fontPreviewAbortController.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.data && data.data.preview_image) {
            // Cache the result
            fontPreviewCache[fontName] = data.data.preview_image;

            // Display the preview
            previewImage.src = data.data.preview_image;
            previewImage.alt = `Preview of ${fontName} font`;
            previewImage.style.display = 'block';
            previewLoading.style.display = 'none';
            previewFallback.style.display = 'none';
        } else {
            throw new Error('No preview data received');
        }

    } catch (error) {
        if (error.name === 'AbortError') {
            return; // Request was cancelled, do nothing
        }
        console.warn(`Font preview failed for ${fontName}:`, error.message);
        // Show fallback text
        previewImage.style.display = 'none';
        previewLoading.style.display = 'none';
        previewFallback.textContent = `Preview: ${fontName}`;
        previewFallback.style.display = 'block';
    }
}

// Font upload functionality
function setupFontUpload() {
    const uploadBtn = document.getElementById('upload-font-btn');
    const fileInput = document.getElementById('font-upload-input');
    const fontSelect = document.getElementById('font-select');

    if (!uploadBtn || !fileInput) return;

    uploadBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', async function () {
        if (this.files.length === 0) return;

        const file = this.files[0];

        // Basic validation
        const validExts = ['.ttf', '.otf'];
        const fileName = file.name.toLowerCase();

        if (!validExts.some(ext => fileName.endsWith(ext))) {
            showNotification('Invalid file type. Please upload .ttf or .otf file.', 'error');
            this.value = '';
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            showNotification('File is too large. Max size is 10MB.', 'error');
            this.value = '';
            return;
        }

        // Upload
        const formData = new FormData();
        formData.append('font_file', file);

        // Show loading state on button
        const originalText = uploadBtn.textContent;
        uploadBtn.textContent = 'Uploading...';
        uploadBtn.disabled = true;

        try {
            const response = await fetch('/api/fonts/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Upload failed');
            }

            showNotification(`Font "${result.data.font.display_name}" uploaded successfully!`, 'success');

            // Add custom font to select and select it
            // Check if option already exists
            let option = fontSelect.querySelector(`option[value="${result.data.font.name}"]`);
            if (!option) {
                option = document.createElement('option');
                option.value = result.data.font.name;
                option.textContent = result.data.font.display_name + (result.data.font.is_custom ? " (Custom)" : "");
                fontSelect.appendChild(option);
            }

            // Select the new font
            fontSelect.value = result.data.font.name;

            // Trigger change event to load preview
            fontSelect.dispatchEvent(new Event('change'));

        } catch (error) {
            console.error('Font upload error:', error);
            showNotification(error.message, 'error');
        } finally {
            uploadBtn.textContent = originalText.trim(); // Trim in case of extra spaces
            uploadBtn.disabled = false;
            fileInput.value = '';
        }
    });
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
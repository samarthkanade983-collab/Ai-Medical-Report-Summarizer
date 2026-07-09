/**
 * Medical Report Summarizer - Frontend JavaScript
 * Handles user interactions and API communication
 */

// DOM Elements
const reportInput = document.getElementById('reportInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const clearBtn = document.getElementById('clearBtn');
const themeToggle = document.getElementById('themeToggle');
const loadingIndicator = document.getElementById('loadingIndicator');
const resultsSection = document.getElementById('resultsSection');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');

// PDF Upload Elements
const pdfUpload = document.getElementById('pdfUpload');
const uploadPdfBtn = document.getElementById('uploadPdfBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const removeFileBtn = document.getElementById('removeFileBtn');

// State
let uploadedFile = null;

// Result display elements
const summaryText = document.getElementById('summaryText');
const issuesList = document.getElementById('issuesList');
const noIssuesMessage = document.getElementById('noIssuesMessage');
const adviceText = document.getElementById('adviceText');
const explanationsContainer = document.getElementById('explanationsContainer');
const nlpSummaryText = document.getElementById('nlpSummaryText');
const compressionRatio = document.getElementById('compressionRatio');
const nlpTime = document.getElementById('nlpTime');
const totalTime = document.getElementById('totalTime');
const textLength = document.getElementById('textLength');

// Chart elements
const medicalChartCanvas = document.getElementById('medicalChart');
const noChartDataMessage = document.getElementById('noChartDataMessage');
let medicalChart = null; // Store chart instance

// Theme Toggle Functionality
let isDarkMode = false;

themeToggle.addEventListener('click', () => {
    isDarkMode = !isDarkMode;
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
    themeToggle.textContent = isDarkMode ? '☀️' : '🌙';
    
    // Save preference to localStorage
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
});

// Load saved theme preference
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    isDarkMode = true;
    document.documentElement.setAttribute('data-theme', 'dark');
    themeToggle.textContent = '☀️';
}

// Analyze Button Click Handler
analyzeBtn.addEventListener('click', async () => {
    const reportText = reportInput.value.trim();
    
    // Validate input
    if (!reportText) {
        showError('Please enter a medical report text to analyze.');
        return;
    }
    
    // Clear previous results and errors
    hideError();
    hideResults();
    
    // Show loading indicator
    showLoading(true);
    
    try {
        // Send request to backend API
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                report_text: reportText
            })
        });
        
        // Parse response
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze report');
        }
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An error occurred while analyzing the report.');
    } finally {
        // Hide loading indicator
        showLoading(false);
    }
});

// PDF Upload Button Click Handler
uploadPdfBtn.addEventListener('click', () => {
    pdfUpload.click();
});

// PDF File Selection Handler
pdfUpload.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    
    if (!file) {
        return;
    }
    
    // Validate file type
    if (file.type !== 'application/pdf') {
        showError('Please select a valid PDF file.');
        return;
    }
    
    // Validate file size (max 16MB)
    if (file.size > 16 * 1024 * 1024) {
        showError('File size must be less than 16MB.');
        return;
    }
    
    // Store the file
    uploadedFile = file;
    
    // Show file info
    fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
    fileInfo.style.display = 'flex';
    uploadPdfBtn.style.display = 'none';
    
    // Upload and extract text
    await uploadPDF(file);
});

// Remove File Button Handler
removeFileBtn.addEventListener('click', () => {
    uploadedFile = null;
    pdfUpload.value = '';
    fileInfo.style.display = 'none';
    uploadPdfBtn.style.display = 'inline-flex';
    reportInput.value = '';
});

// Upload PDF Function
async function uploadPDF(file) {
    showLoading(true);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/upload-pdf', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to upload PDF');
        }
        
        // Display extracted text in textarea
        reportInput.value = data.text;
        
        // Show success message
        console.log(`PDF uploaded successfully. Extracted ${data.text.length} characters.`);
        
    } catch (error) {
        console.error('Error uploading PDF:', error);
        showError(error.message || 'Failed to process PDF file. Please try again or paste text manually.');
        
        // Reset upload state on error
        uploadedFile = null;
        pdfUpload.value = '';
        fileInfo.style.display = 'none';
        uploadPdfBtn.style.display = 'inline-flex';
    } finally {
        showLoading(false);
    }
}

// Format file size helper
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Clear Button Click Handler
clearBtn.addEventListener('click', () => {
    reportInput.value = '';
    uploadedFile = null;
    pdfUpload.value = '';
    fileInfo.style.display = 'none';
    uploadPdfBtn.style.display = 'inline-flex';
    hideResults();
    hideError();
    reportInput.focus();
});

// Show/Hide Loading Indicator
function showLoading(show) {
    if (show) {
        loadingIndicator.style.display = 'flex';
        analyzeBtn.disabled = true;
        analyzeBtn.querySelector('.btn-text').style.display = 'none';
        analyzeBtn.querySelector('.loading-spinner').style.display = 'inline';
    } else {
        loadingIndicator.style.display = 'none';
        analyzeBtn.disabled = false;
        analyzeBtn.querySelector('.btn-text').style.display = 'inline';
        analyzeBtn.querySelector('.loading-spinner').style.display = 'none';
    }
}

// Display Results
function displayResults(data) {
    // Summary
    summaryText.textContent = data.summary;
    
    // Issues
    if (data.issues && data.issues.length > 0) {
        issuesList.innerHTML = '';
        data.issues.forEach(issue => {
            const li = document.createElement('li');
            li.textContent = issue;
            issuesList.appendChild(li);
        });
        issuesList.style.display = 'block';
        noIssuesMessage.style.display = 'none';
    } else {
        issuesList.style.display = 'none';
        noIssuesMessage.style.display = 'block';
    }
    
    // Advice
    adviceText.textContent = data.advice;
    
    // Explanations
    if (data.explanations && data.explanations.length > 0) {
        explanationsContainer.innerHTML = '';
        data.explanations.forEach(explanation => {
            const explanationDiv = document.createElement('div');
            explanationDiv.className = `explanation-item ${explanation.severity}`;
            
            explanationDiv.innerHTML = `
                <div class="explanation-metric">${explanation.metric}</div>
                <div class="explanation-value">
                    Value: <strong>${explanation.value}</strong> | 
                    Threshold: ${explanation.threshold}
                </div>
                <div class="explanation-finding">${explanation.finding}</div>
            `;
            
            explanationsContainer.appendChild(explanationDiv);
        });
    } else {
        explanationsContainer.innerHTML = '<p style="color: var(--success-color); font-weight: 600;">No abnormal values detected. All metrics are within normal range.</p>';
    }
    
    // Data Visualization - Chart
    renderMedicalChart(data.extracted_values);
    
    // NLP Summary
    nlpSummaryText.textContent = data.nlp_summary;
    compressionRatio.textContent = `${data.nlp_compression}%`;
    nlpTime.textContent = `${data.processing_time}ms`;

    // Probabilistic Analysis
    if (data.probabilistic_analysis) {
        const d = data.probabilistic_analysis;
        
        // Department mapping
        document.getElementById('predDepartment').textContent = d.department.predicted;
        document.getElementById('deptConfidence').textContent = `${d.department.confidence} Confidence`;
        
        const deptList = document.getElementById('deptProbList');
        deptList.innerHTML = '';
        d.department.probabilities.forEach(p => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>${p.department}</strong>: ${p.probability}%`;
            li.style.marginBottom = "5px";
            deptList.appendChild(li);
        });

        // Disease Risk Mapping
        document.getElementById('predRisk').textContent = d.disease_risk.primary_risk;
        document.getElementById('riskProbabilityPercent').textContent = `${d.disease_risk.max_probability}% Probability`;
        
        const riskList = document.getElementById('riskProbList');
        riskList.innerHTML = '';
        d.disease_risk.all_probabilities.forEach(p => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>${p.risk_category}</strong>: ${p.probability}%`;
            li.style.marginBottom = "5px";
            riskList.appendChild(li);
        });
    }
    
    // Comparison Table
    if (data.comparison) {
        document.getElementById('ruleSpeed').textContent = data.comparison.rule_based.speed;
        document.getElementById('nlpSpeed').textContent = data.comparison.nlp.speed;
    }
    
    // Processing Info
    totalTime.textContent = data.processing_time;
    textLength.textContent = data.original_text_length;
    
    // Show results section with animation
    resultsSection.style.display = 'grid';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Render Medical Values Chart
function renderMedicalChart(values) {
    // Destroy existing chart if it exists
    if (medicalChart) {
        medicalChart.destroy();
    }
    
    // Check if we have any values to display
    const hasValues = values.glucose || values.hemoglobin || values.cholesterol;
    
    if (!hasValues) {
        medicalChartCanvas.parentElement.style.display = 'none';
        noChartDataMessage.style.display = 'block';
        return;
    }
    
    // Show chart container
    medicalChartCanvas.parentElement.style.display = 'block';
    noChartDataMessage.style.display = 'none';
    
    // Prepare data for chart
    const labels = [];
    const dataPoints = [];
    const backgroundColors = [];
    const borderColors = [];
    
    // Reference ranges
    const glucoseNormal = 100; // midpoint of 70-140
    const hemoglobinNormal = 14.5; // midpoint of 12-17
    const cholesterolNormal = 162.5; // midpoint of 125-200
    
    if (values.glucose) {
        labels.push('Glucose (mg/dL)');
        dataPoints.push(values.glucose);
        if (values.glucose > 140 || values.glucose < 70) {
            backgroundColors.push('rgba(231, 76, 60, 0.7)'); // Red for abnormal
            borderColors.push('rgba(231, 76, 60, 1)');
        } else {
            backgroundColors.push('rgba(39, 166, 96, 0.7)'); // Green for normal
            borderColors.push('rgba(39, 166, 96, 1)');
        }
    }
    
    if (values.hemoglobin) {
        labels.push('Hemoglobin (g/dL)');
        dataPoints.push(values.hemoglobin);
        if (values.hemoglobin < 12 || values.hemoglobin > 17) {
            backgroundColors.push('rgba(231, 76, 60, 0.7)'); // Red for abnormal
            borderColors.push('rgba(231, 76, 60, 1)');
        } else {
            backgroundColors.push('rgba(39, 166, 96, 0.7)'); // Green for normal
            borderColors.push('rgba(39, 166, 96, 1)');
        }
    }
    
    if (values.cholesterol) {
        labels.push('Cholesterol (mg/dL)');
        dataPoints.push(values.cholesterol);
        if (values.cholesterol > 200 || values.cholesterol < 125) {
            backgroundColors.push('rgba(231, 76, 60, 0.7)'); // Red for abnormal
            borderColors.push('rgba(231, 76, 60, 1)');
        } else {
            backgroundColors.push('rgba(39, 166, 96, 0.7)'); // Green for normal
            borderColors.push('rgba(39, 166, 96, 1)');
        }
    }
    
    // Get current theme
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#eaeaea' : '#2c3e50';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    
    // Create chart
    const ctx = medicalChartCanvas.getContext('2d');
    medicalChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Extracted Values',
                data: dataPoints,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: textColor,
                        font: {
                            size: 14
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Medical Values vs Normal Range',
                    color: textColor,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y + ' ' + 
                                   (context.label.includes('Glucose') || context.label.includes('Cholesterol') ? 'mg/dL' : 'g/dL');
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        color: gridColor
                    }
                },
                x: {
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        color: gridColor
                    }
                }
            }
        }
    });
}

// Show Error Message
function showError(message) {
    errorText.textContent = message;
    errorMessage.style.display = 'block';
    errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Hide Error Message
function hideError() {
    errorMessage.style.display = 'none';
}

// Hide Results
function hideResults() {
    resultsSection.style.display = 'none';
}

// Keyboard Shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to analyze
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if (reportInput.value.trim()) {
            analyzeBtn.click();
        }
    }
    
    // Escape to clear
    if (e.key === 'Escape') {
        if (document.activeElement === reportInput) {
            clearBtn.click();
        }
    }
});

// Add placeholder example on focus
reportInput.addEventListener('focus', () => {
    if (!reportInput.value.trim()) {
        reportInput.placeholder = `Example:\nPatient blood glucose level is 180 mg/dL.\nHemoglobin count shows 11 g/dL.\nTotal cholesterol measured at 220 mg/dL.\nThe patient reports frequent urination and excessive thirst.\nBlood pressure reading was 140/90 mmHg.`;
    }
});

// Remove placeholder on blur if empty
reportInput.addEventListener('blur', () => {
    if (!reportInput.value.trim()) {
        reportInput.placeholder = `Paste your medical report text here...

Example:
Patient blood glucose level is 180 mg/dL. 
Hemoglobin count shows 11 g/dL. 
Total cholesterol measured at 220 mg/dL.
The patient reports frequent urination and excessive thirst.`;
    }
});

// Console welcome message
console.log('%c🏥 Medical Report Summarizer', 'font-size: 20px; color: #4a90e2; font-weight: bold;');
console.log('%cAI-Powered Health Analysis & Summarization', 'font-size: 14px; color: #7f8c8d;');
console.log('%cFor educational purposes only. Not a substitute for professional medical advice.', 'font-size: 12px; color: #e74c3c;');

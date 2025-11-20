// Modal functionality
async function showModal(ruleIndex) {
    const modal = document.getElementById('sigma-modal');
    const modalTitle = document.getElementById('sigma-modal-title');
    const modalText = document.getElementById('sigma-modal-text');
    const modalPath = document.getElementById('sigma-modal-path');
    
    const rule = rules[ruleIndex];
    
    // Clear any stored conversion data when opening a new rule
    window.currentRawQuery = null;
    window.currentStructuredQuery = null;
    
    // Remove any existing "Back to Structured View" button
    const modalFooter = modal.querySelector('.modal-footer');
    const existingBackButton = modalFooter.querySelector('.back-to-structured-btn');
    if (existingBackButton) {
        existingBackButton.remove();
    }
    
    modalTitle.textContent = rule.title || rule.file_path.split('/').pop();
    modalPath.textContent = rule.file_path;
    
    // Show loading state
    modalText.innerHTML = '<div class="loading">Loading rule content...</div>';
    
    try {
        const response = await fetch('/rule_yaml?' + new URLSearchParams({
            file_path: rule.file_path
        }));
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const content = await response.text();
        modalText.textContent = content;
    } catch (error) {
        console.error('Error loading rule:', error);
        modalText.innerHTML = `
            <div class="error-message">
                <strong>Error loading rule content:</strong><br>
                ${error.message}<br><br>
                <strong>File path:</strong> ${rule.file_path}<br>
                <strong>Rule title:</strong> ${rule.title || 'N/A'}
            </div>
        `;
    }
    
    modal.style.display = 'block';
    modal.dataset.currentRuleIndex = ruleIndex;
}

// Category/Subcategory Filter Logic
const categoryStructure = {
    windows: [
        'builtin', 'create_remote_thread', 'create_stream_hash', 'dns_query', 'driver_load', 'file', 'image_load', 'network_connection', 'pipe_created', 'powershell', 'process_access', 'process_creation', 'process_tampering', 'raw_access_thread', 'registry', 'sysmon', 'wmi_event'
    ],
    linux: [
        'auditd', 'builtin', 'file_event', 'network_connection', 'process_creation'
    ],
    macos: [
        'file_event', 'process_creation'
    ],
    network: [
        'cisco', 'dns', 'firewall', 'huawei', 'juniper', 'zeek'
    ],
    web: [
        'product', 'proxy_generic', 'webserver_generic'
    ],
    cloud: [
        'aws', 'azure', 'bitbucket', 'cisco', 'gcp', 'github', 'm365', 'okta', 'onelogin'
    ],
    category: [
        'antivirus', 'database'
    ],
    application: [
        'django', 'jvm', 'kubernetes', 'nodejs', 'opencanary', 'python', 'rpc_firewall', 'ruby', 'spring', 'sql', 'velocity'
    ],
    'rules-emerging-threats': ['2010', '2014', '2015', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025'],
    'rules-threat-hunting': [],
    'rules-compliance': [],
    'rules-dfir': [],
    customs: []
};

function formatCategoryName(category) {
    // Format category names for display
    const categoryNames = {
        'rules-emerging-threats': 'Emerging Threats',
        'rules-threat-hunting': 'Threat Hunting',
        'rules-compliance': 'Compliance',
        'rules-dfir': 'DFIR'
    };
    
    if (categoryNames[category]) {
        return categoryNames[category];
    }
    
    // Default: capitalize first letter
    return category.charAt(0).toUpperCase() + category.slice(1);
}

function populateCategoryDropdown() {
    const categorySelect = document.getElementById('category-select');
    if (categorySelect) {
        categorySelect.innerHTML = '<option value="">Select Category</option>' +
            Object.keys(categoryStructure).map(cat => `<option value="${cat}">${formatCategoryName(cat)}</option>`).join('');
    }
}

function formatSubcategoryName(subcategory) {
    // Replace underscores with spaces and capitalize each word
    return subcategory.split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function applyFilters() {
    const searchForm = document.getElementById('search-form');
    if (searchForm) searchForm.submit();
}

function populateSubcategoryDropdown(category) {
    const subcategorySelect = document.getElementById('subcategory-select');
    if (!subcategorySelect) return;
    
    if (!category || !categoryStructure[category]) {
        subcategorySelect.innerHTML = '<option value="">Select Subcategory</option>';
        return;
    }
    subcategorySelect.innerHTML = '<option value="">Select Subcategory</option>' +
        categoryStructure[category].map(sub => `<option value="${sub}">${formatSubcategoryName(sub)}</option>`).join('');
}

// Initialize category filter on page load
document.addEventListener('DOMContentLoaded', function() {
    populateCategoryDropdown();
    
    // Set initial values from URL params if they exist
    const params = new URLSearchParams(window.location.search);
    const selectedCategory = params.get('category');
    const selectedSubcategory = params.get('subcategory');
    const selectedDeploymentStatus = params.get('deployment_status');
    
    // Set deployment status
    const deploymentSelectInit = document.getElementById('deployment-select');
    if (deploymentSelectInit && selectedDeploymentStatus) {
        deploymentSelectInit.value = selectedDeploymentStatus;
    }
    
    if (selectedCategory) {
        const categorySelect = document.getElementById('category-select');
        if (categorySelect) {
            categorySelect.value = selectedCategory;
            populateSubcategoryDropdown(selectedCategory);
            if (selectedSubcategory) {
                const subcategorySelect = document.getElementById('subcategory-select');
                if (subcategorySelect) {
                    subcategorySelect.value = selectedSubcategory;
                }
            }
        }
    }

    // Update hidden form fields when filters change
    const categorySelect = document.getElementById('category-select');
    const subcategorySelect = document.getElementById('subcategory-select');
    const deploymentSelect = document.getElementById('deployment-select');
    const categoryHidden = document.getElementById('category-hidden');
    const subcategoryHidden = document.getElementById('subcategory-hidden');
    const deploymentHidden = document.getElementById('deployment-hidden');

    if (categorySelect) {
        categorySelect.addEventListener('change', function(e) {
            populateSubcategoryDropdown(e.target.value);
            if (categoryHidden) categoryHidden.value = e.target.value;
            if (subcategoryHidden) subcategoryHidden.value = ''; // Reset subcategory when category changes
        });
    }

    if (subcategorySelect) {
        subcategorySelect.addEventListener('change', function(e) {
            if (subcategoryHidden) subcategoryHidden.value = e.target.value;
        });
    }

    // Add change event listeners for automatic filtering
    if (categorySelect) {
        categorySelect.addEventListener('change', function(e) {
            if (categoryHidden) categoryHidden.value = e.target.value;
            if (subcategoryHidden) subcategoryHidden.value = ''; // Reset subcategory
            populateSubcategoryDropdown(e.target.value);
            applyFilters();
        });
    }

    if (subcategorySelect) {
        subcategorySelect.addEventListener('change', function(e) {
            if (subcategoryHidden) subcategoryHidden.value = e.target.value;
            applyFilters();
        });
    }

    // Add deployment filter event listener
    if (deploymentSelect) {
        deploymentSelect.addEventListener('change', function(e) {
            console.log('Deployment filter changed:', e.target.value);
            if (deploymentHidden) deploymentHidden.value = e.target.value;
            applyFilters();
        });
    }
});

// Close modal
function closeModal() {
    const modal = document.getElementById('sigma-modal');
    
    // Remove any existing "Back to Structured View" button
    const modalFooter = modal.querySelector('.modal-footer');
    const existingBackButton = modalFooter.querySelector('.back-to-structured-btn');
    if (existingBackButton) {
        existingBackButton.remove();
    }
    
    modal.style.display = 'none';
}

// Custom Rules Modal functionality
function openCustomRulesModal() {
    const modal = document.getElementById('custom-rules-modal');
    modal.style.display = 'block';
    loadCustomRules();
}

function closeCustomRulesModal() {
    const modal = document.getElementById('custom-rules-modal');
    modal.style.display = 'none';
    hideEditor();
}

function hideEditor() {
    const editor = document.getElementById('custom-rule-editor');
    const list = document.getElementById('custom-rules-list');
    editor.style.display = 'none';
    list.style.display = 'block';
}

function showEditor() {
    const editor = document.getElementById('custom-rule-editor');
    const list = document.getElementById('custom-rules-list');
    editor.style.display = 'block';
    list.style.display = 'none';
}

// Add lightweight toast notifications
function showToast(message, type = 'info') {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.style.position = 'fixed';
        toast.style.bottom = '16px';
        toast.style.right = '16px';
        toast.style.zIndex = '9999';
        toast.style.padding = '10px 14px';
        toast.style.borderRadius = '6px';
        toast.style.boxShadow = '0 6px 18px rgba(0,0,0,0.2)';
        toast.style.color = '#23284a';
        toast.style.fontFamily = 'Inter, sans-serif';
        toast.style.fontSize = '14px';
        document.body.appendChild(toast);
    }
    const colors = {
        info: '#cbd5e1',
        success: '#86efac',
        error: '#fca5a5',
        warn: '#fde68a'
    };
    toast.style.background = colors[type] || colors.info;
    toast.textContent = message;
    toast.style.opacity = '1';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => {
        toast.style.opacity = '0';
    }, 2200);
}

// Global variable to store custom rules data for filtering
let allCustomRules = [];

// Load Custom Rules
async function loadCustomRules() {
    try {
        const response = await fetch('/custom_rules');
        if (!response.ok) {
            throw new Error('Failed to load custom rules');
        }
        
        const customRules = await response.json();
        allCustomRules = customRules; // Store for filtering
        displayCustomRules(customRules);
        
        // Clear search input when loading
        const searchInput = document.getElementById('custom-rules-search');
        if (searchInput) {
            searchInput.value = '';
        }
    } catch (error) {
        showToast('Failed to load custom rules', 'error');
    }
}

// Load Custom Rule Content
async function loadCustomRuleContent(filename) {
    try {
        const response = await fetch(`/custom_rules/${filename}`);
        if (!response.ok) {
            throw new Error('Failed to load custom rule');
        }
        
        const content = await response.text();
        document.getElementById('custom-rule-content').value = content;
        document.getElementById('custom-rule-filename').value = filename;
        
        // Show the modal
        document.getElementById('custom-rule-modal').style.display = 'block';
    } catch (error) {
        showToast('Failed to load custom rule', 'error');
    }
}

// Save Custom Rule
async function saveCustomRule() {
    const filename = document.getElementById('rule-filename').value.trim();
    const content = document.getElementById('rule-content').value.trim();
    
    if (!filename || !content) {
        showToast('Please provide both filename and content', 'error');
        return;
    }
    
    try {
        const response = await fetch('/custom_rules', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: filename,
                content: content
            })
        });
        
        if (response.ok) {
            showToast('Custom rule saved successfully', 'success');
            closeCustomRulesModal();
            loadCustomRules();
            // Refresh page to include new custom rule in deployment system
            setTimeout(() => window.location.reload(), 1000);
        } else {
            const text = await response.text();
            console.error("Save failed:", response.status, text);
            throw new Error('Failed to save custom rule');
        }
        
    } catch (error) {
        showToast('Failed to save custom rule', 'error');
    }
}

// Delete Custom Rule
async function deleteCustomRule(filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/custom_rules/${filename}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Custom rule deleted successfully', 'success');
            loadCustomRules(); // Refresh the list
            // Refresh page to update deployment system
            setTimeout(() => window.location.reload(), 1000);
        } else {
            throw new Error('Failed to delete custom rule');
        }
    } catch (error) {
        showToast('Failed to delete custom rule', 'error');
    }
}

// Cancel editing
function cancelEdit() {
    hideEditor();
}

// Add New Rule
function addNewRule() {
    // Clear form and insert template
    document.getElementById('rule-filename').value = '';
    
    // Insert Sigma rule template with auto-formatting ready structure
    const template = `title: New Sigma Rule
id: 
status: experimental
description: 
author: 
date: ${new Date().toISOString().split('T')[0]}
modified: ${new Date().toISOString().split('T')[0]}
tags:
    - ''
logsource:
    product: 
    category: 
    service: 
detection:
    selection:
        FieldName|contains:
            - ''
    condition: selection
falsepositives:
    - ''
level: medium
references:
    - ''`;
    
    document.getElementById('rule-content').value = template;
    showEditor();
    
    // Focus on filename first
    document.getElementById('rule-filename').focus();
    
    // Show YAML help automatically for new rules
    const helpDiv = document.getElementById('yaml-editor-help');
    if (helpDiv) {
        helpDiv.style.display = 'block';
    }
}

// Display Custom Rules
function displayCustomRules(customRules) {
    const rulesList = document.getElementById('custom-rules-list');
    
    if (!customRules || customRules.length === 0) {
        rulesList.innerHTML = '<div class="no-rules"><i class="fas fa-file-alt"></i><p>No custom rules found. Click "Add New Rule" to create one.</p></div>';
        return;
    }
    
    // Get search term for highlighting
    const searchInput = document.getElementById('custom-rules-search');
    const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
    
    let html = '';
    customRules.forEach(rule => {
        // Helper function to highlight search terms
        const highlightText = (text, term) => {
            if (!term || !text) return text;
            // Escape special regex characters and create case-insensitive pattern
            const escapedTerm = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regex = new RegExp(`(${escapedTerm})`, 'gi');
            return text.replace(regex, '<mark class="search-highlight">$1</mark>');
        };
        
        const title = rule.title || rule.filename;
        const description = rule.description || 'No description';
        
        html += `
            <div class="custom-rule-item">
                <div class="rule-info">
                    <h4>${highlightText(title, searchTerm)}</h4>
                    <p>${highlightText(description, searchTerm)}</p>
                    <div class="rule-tags">
                        ${rule.tags ? rule.tags.map(tag => `<span class="tag">${highlightText(tag, searchTerm)}</span>`).join('') : ''}
                    </div>
                    <div class="rule-filename">${highlightText(rule.filename, searchTerm)}</div>
                </div>
                <div class="rule-actions">
                    <button class="edit-btn" onclick="editCustomRule('${rule.filename}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="delete-btn" onclick="deleteCustomRule('${rule.filename}')">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `;
    });
    
    rulesList.innerHTML = html;
}

// Debounce function for smooth search
let searchTimeout;

// Filter Custom Rules based on search input with debouncing
function filterCustomRules() {
    // Clear previous timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    // Show search indicator for immediate feedback
    const searchInput = document.getElementById('custom-rules-search');
    if (searchInput && searchInput.value.trim()) {
        searchInput.style.borderColor = '#7c3aed';
    }
    
    // Debounce search to improve performance
    searchTimeout = setTimeout(() => {
        performCustomRulesFilter();
        // Reset border color after search
        if (searchInput) {
            searchInput.style.borderColor = '';
        }
    }, 150); // 150ms delay
}

// Actual filter function using advanced search logic
function performCustomRulesFilter() {
    const searchInput = document.getElementById('custom-rules-search');
    if (!searchInput || !allCustomRules) return;
    
    const searchQuery = searchInput.value.trim();
    
    if (!searchQuery) {
        // If search is empty, show all rules
        displayCustomRules(allCustomRules);
        return;
    }
    
    // Use advanced search API for custom rules
    performAdvancedCustomRulesSearch(searchQuery);
}

// Advanced search for custom rules using server-side logic
async function performAdvancedCustomRulesSearch(query) {
    // Show loading indicator
    const rulesList = document.getElementById('custom-rules-list');
    rulesList.innerHTML = `
        <div class="search-loading" style="text-align: center; padding: 40px; color: #8b949e;">
            <i class="fas fa-spinner fa-spin" style="font-size: 24px; margin-bottom: 12px;"></i>
            <p>Searching with advanced logic...</p>
        </div>
    `;
    
    try {
        const response = await fetch('/api/search/custom-rules', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                rules: allCustomRules
            })
        });
        
        if (!response.ok) {
            throw new Error('Search failed');
        }
        
        const data = await response.json();
        
        if (data.success) {
            displayCustomRules(data.results);
            
            // Show search type indicator
            console.log(`Advanced search completed: ${data.total_found} results for "${query}"`);
            
            // Show search results count with advanced search info
            const rulesList = document.getElementById('custom-rules-list');
            if (data.results.length === 0 && query) {
                rulesList.innerHTML = `
                    <div class="no-rules fade-in">
                        <i class="fas fa-search"></i>
                        <p>No custom rules found matching "<strong>${query}</strong>"</p>
                        <div style="font-size: 0.85em; color: #8b949e; margin-top: 12px; text-align: left;">
                            <strong>Advanced search examples:</strong><br>
                            • <code>title:PowerShell AND status:test</code><br>
                            • <code>author:myname OR description:malware</code><br>
                            • <code>tags:attack.execution</code><br>
                            • <code>mimikatz NOT experimental</code>
                        </div>
                    </div>
                `;
            }
        } else {
            throw new Error(data.error || 'Search failed');
        }
        
    } catch (error) {
        console.error('Advanced search error:', error);
        // Fallback to simple search
        performSimpleCustomRulesFilter(query);
    }
}

// Fallback simple search function
function performSimpleCustomRulesFilter(searchTerm) {
    const searchTermLower = searchTerm.toLowerCase();
    
    const filteredRules = allCustomRules.filter(rule => {
        const title = (rule.title || '').toLowerCase();
        const description = (rule.description || '').toLowerCase();
        const filename = (rule.filename || '').toLowerCase();
        
        // Check title and filename first (most common searches)
        if (title.includes(searchTermLower) || filename.includes(searchTermLower)) {
            return true;
        }
        
        // Then check description
        if (description.includes(searchTermLower)) {
            return true;
        }
        
        // Finally check tags
        if (rule.tags) {
            const tags = rule.tags.join(' ').toLowerCase();
            return tags.includes(searchTermLower);
        }
        
        return false;
    });
    
    displayCustomRules(filteredRules);
    
    // Show fallback search results
    const rulesList = document.getElementById('custom-rules-list');
    if (filteredRules.length === 0 && searchTerm) {
        rulesList.innerHTML = `
            <div class="no-rules fade-in">
                <i class="fas fa-search"></i>
                <p>No custom rules found matching "<strong>${searchTerm}</strong>"</p>
                <p style="font-size: 0.9em; color: #8b949e; margin-top: 8px;">
                    Simple search in title, description, tags, and filename
                </p>
            </div>
        `;
    }
}

// Edit Custom Rule
function editCustomRule(filename) {
    // Find the rule in the custom rules list
    fetch('/custom_rules')
        .then(response => response.json())
        .then(customRules => {
            const rule = customRules.find(r => r.filename === filename);
            if (rule) {
                document.getElementById('rule-filename').value = filename.replace(/\.(yml|yaml)$/, '');
                document.getElementById('rule-content').value = rule.content;
                showEditor();
            }
        })
        .catch(error => {
            showToast('Failed to load rule for editing', 'error');
        });
}

// Show Editor
function showEditor() {
    document.getElementById('custom-rule-editor').style.display = 'block';
    document.getElementById('custom-rules-list').style.display = 'none';
}

// Hide Editor
function hideEditor() {
    document.getElementById('custom-rule-editor').style.display = 'none';
    document.getElementById('custom-rules-list').style.display = 'block';
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
// Close modal when clicking outside
    window.addEventListener('click', function(event) {
    const sigmaModal = document.getElementById('sigma-modal');
        const structuredModal = document.getElementById('structured-query-modal');
    const customRulesModal = document.getElementById('custom-rules-modal');
    
        if (event.target === sigmaModal) {
        closeModal();
    }
        if (event.target === structuredModal) {
            closeStructuredQueryModal();
        }
        if (event.target === customRulesModal) {
            closeCustomRulesModal();
        }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const sigmaModal = document.getElementById('sigma-modal');
            const structuredModal = document.getElementById('structured-query-modal');
            const customRulesModal = document.getElementById('custom-rules-modal');
            
            if (sigmaModal.style.display === 'block') {
                closeModal();
            }
            if (structuredModal.style.display === 'block') {
                closeStructuredQueryModal();
            }
            if (customRulesModal.style.display === 'block') {
        closeCustomRulesModal();
    }
}
    });
});

// Copy functionality
async function copyModalContent() {
    const modalText = document.getElementById('sigma-modal-text');
    const copyBtn = document.getElementById('sigma-modal-copy');
    
    try {
        await navigator.clipboard.writeText(modalText.textContent);
        
        // Visual feedback
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        copyBtn.style.background = '#48bb78';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '';
        }, 2000);
    } catch (err) {
        console.error('Failed to copy text: ', err);
        
        // Error feedback
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-times"></i> Failed to copy';
        copyBtn.style.background = '#f56565';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '';
        }, 2000);
    }
}

// Convert to Lucene query
async function convertSigmaToLucene() {
    const modal = document.getElementById('sigma-modal');
    const ruleIndex = modal.dataset.currentRuleIndex;
    const rule = rules[ruleIndex];
    const convertBtn = document.getElementById('sigma-modal-convert');
    
    try {
        const response = await fetch('/convert_to_lucene?' + new URLSearchParams({
            file_path: rule.file_path
        }), {
            method: 'GET',
            headers: {
                'Accept': 'text/plain',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.text();
        
        // Update modal content with the converted query
        const modalText = document.getElementById('sigma-modal-text');
        modalText.textContent = result;
        
        // Visual feedback
        const originalText = convertBtn.innerHTML;
        convertBtn.innerHTML = '<i class="fas fa-check"></i> Converted!';
        
        setTimeout(() => {
            convertBtn.innerHTML = originalText;
        }, 2000);
        
    } catch (error) {
        console.error('Error converting rule:', error);
        
        // Error feedback
        const originalText = convertBtn.innerHTML;
        convertBtn.innerHTML = '<i class="fas fa-times"></i> Conversion failed';
        
        setTimeout(() => {
            convertBtn.innerHTML = originalText;
        }, 2000);
    }
}

// Convert to Structured Query
async function convertToStructuredQuery() {
    const rule = rules[document.getElementById('sigma-modal').dataset.currentRuleIndex];
    const convertBtn = document.getElementById('sigma-modal-convert');
    
    try {
        const response = await fetch('/convert_to_structured?' + new URLSearchParams({
            file_path: rule.file_path
        }));
        
        if (!response.ok) {
            throw new Error('Failed to convert rule');
        }
        
        const result = await response.json();
        
        // Store the raw query for later use
        window.currentRawQuery = result.original_query || '';
        
        // Store the structured query data for the back button
        window.currentStructuredQuery = result;
        
        // If no original query in result, try to get it from the original conversion
        if (!window.currentRawQuery) {
            try {
                const luceneResponse = await fetch('/convert_to_lucene?' + new URLSearchParams({
                    file_path: rule.file_path
                }));
                if (luceneResponse.ok) {
                    window.currentRawQuery = await luceneResponse.text();
                }
            } catch (fallbackError) {
                // Silently handle fallback errors
            }
        }
        
        // Render the structured query
        renderStructuredQuery(result);
        
        // Close the sigma modal
        closeModal();
        
        // Show the structured query modal
        showStructuredQueryModal();
        
        // Visual feedback
        const originalText = convertBtn.innerHTML;
        convertBtn.innerHTML = '<i class="fas fa-check"></i> Structured View!';
        
        setTimeout(() => {
            convertBtn.innerHTML = originalText;
        }, 2000);
        
    } catch (error) {
        // Error feedback
        const originalText = convertBtn.innerHTML;
        convertBtn.innerHTML = '<i class="fas fa-times"></i> Conversion failed';
        
        setTimeout(() => {
            convertBtn.innerHTML = originalText;
        }, 2000);
    }
}

// Show Structured Query Modal
function showStructuredQueryModal() {
    const modal = document.getElementById('structured-query-modal');
    const rawBtn = document.getElementById('structured-query-raw');
    
    // Enable/disable the Show Raw button based on whether we have a raw query
    if (rawBtn) {
        if (window.currentRawQuery && window.currentRawQuery.trim()) {
            rawBtn.disabled = false;
            rawBtn.style.opacity = '1';
            rawBtn.style.cursor = 'pointer';
            rawBtn.title = 'Show the original Lucene query';
            rawBtn.innerHTML = '<i class="fas fa-code"></i> Show Raw';
        } else {
            rawBtn.disabled = true;
            rawBtn.style.opacity = '0.5';
            rawBtn.style.cursor = 'not-allowed';
            rawBtn.title = 'No raw query available';
            rawBtn.innerHTML = '<i class="fas fa-code"></i> No Raw Query';
        }
    }
    
    modal.style.display = 'block';
}

// Close Structured Query Modal
function closeStructuredQueryModal() {
    const modal = document.getElementById('structured-query-modal');
    modal.style.display = 'none';
    
    // Also clean up the "Back to Structured View" button in the main modal
    const mainModal = document.getElementById('sigma-modal');
    const modalFooter = mainModal.querySelector('.modal-footer');
    const existingBackButton = modalFooter.querySelector('.back-to-structured-btn');
    if (existingBackButton) {
        existingBackButton.remove();
    }
}

// Render Structured Query
function renderStructuredQuery(queryData) {
    const container = document.getElementById('structured-query-content');
    
    if (!queryData || queryData.type === 'error') {
        container.innerHTML = `
            <div class="query-error">
                <i class="fas fa-exclamation-triangle"></i>
                ${queryData?.message || 'Failed to parse query'}
            </div>
        `;
        return;
    }
    
    if (queryData.type === 'empty') {
        container.innerHTML = `
            <div class="query-empty">
                <i class="fas fa-info-circle"></i>
                ${queryData.message || 'No query to display'}
            </div>
        `;
        return;
    }
    
    // Calculate query statistics and update the header stats
    const stats = calculateQueryStats(queryData);
    document.getElementById('query-groups-count').textContent = `${stats.groups} Groups`;
    document.getElementById('query-conditions-count').textContent = `${stats.conditions} Conditions`;
    document.getElementById('query-depth').textContent = `Depth: ${stats.maxDepth}`;
    
    // Generate query summary
    const summaryHtml = generateQuerySummary(queryData);
    document.getElementById('summary-content').innerHTML = summaryHtml;
    
    // Render the main query structure
    const queryHtml = renderQueryNode(queryData, 0);
    
    container.innerHTML = `
        <div class="query-structure">
            ${queryHtml}
        </div>
    `;
    
    // Update the Show Raw button state
    const rawButton = document.getElementById('structured-query-raw');
    if (window.currentRawQuery && window.currentRawQuery.trim()) {
        rawButton.disabled = false;
        rawButton.title = 'Show raw Lucene query';
    } else {
        rawButton.disabled = true;
        rawButton.title = 'No raw query available';
    }
}

// Generate Query Summary
function generateQuerySummary(queryData) {
    if (queryData.type !== 'group') return '';
    
    const summary = [];
    
    function summarizeNode(node, level = 0) {
        const indent = '  '.repeat(level);
        
        if (node.type === 'group') {
            const childCount = node.children ? node.children.length : 0;
            summary.push(`${indent}${node.operator} Group (${childCount} items)`);
            
            if (node.children) {
                node.children.forEach(child => summarizeNode(child, level + 1));
            }
        } else if (node.type === 'condition') {
            const field = node.field || 'Unknown';
            const operator = node.operator || 'contains';
            const value = node.value || '';
            const displayValue = value.length > 30 ? value.substring(0, 30) + '...' : value;
            summary.push(`${indent}${field} ${operator} "${displayValue}"`);
        }
    }
    
    summarizeNode(queryData);
    return summary.map(line => `<div class="summary-line">${line}</div>`).join('');
}

// Toggle Summary View
function toggleSummary() {
    const content = document.getElementById('summary-content');
    const icon = document.getElementById('summary-toggle-icon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
    }
}

// Calculate Query Statistics
function calculateQueryStats(queryData) {
    let groups = 0;
    let conditions = 0;
    let maxDepth = 0;
    
    function traverse(node, depth = 0) {
        maxDepth = Math.max(maxDepth, depth);
        
        if (node.type === 'group') {
            groups++;
            if (node.children) {
                node.children.forEach(child => traverse(child, depth + 1));
            }
        } else if (node.type === 'condition') {
            conditions++;
        }
    }
    
    traverse(queryData);
    
    return { groups, conditions, maxDepth };
}

// Render Query Node
function renderQueryNode(node, depth = 0) {
    const isNested = depth > 0;
    
    if (node.type === 'condition') {
        return renderCondition(node);
    }
    
    if (node.type === 'group') {
        const operatorClass = getOperatorClass(node.operator);
        const children = node.children.map(child => renderQueryNode(child, depth + 1)).join('');
        
        // Add visual indicators for complex nested structures
        const complexityIndicator = getComplexityIndicator(node);
        const groupDescription = getGroupDescription(node, depth);
        const isCollapsible = node.children && node.children.length > 3;
        const groupId = `group-${Math.random().toString(36).substr(2, 9)}`;
        
        // Debug logging for NOT groups
        if (node.operator === 'NOT') {
            console.log('Rendering NOT group:', {
                operator: node.operator,
                operatorClass: operatorClass,
                childrenCount: node.children?.length,
                groupDescription: groupDescription,
                children: children
            });
        }
        
        return `
            <div class="query-group" id="${groupId}">
                <div class="query-group-header" ${isCollapsible ? `onclick="toggleGroup('${groupId}')"` : ''}>
                    <span class="query-group-operator ${operatorClass}">${node.operator}</span>
                    <span class="query-group-description">${groupDescription}</span>
                    ${complexityIndicator}
                    ${isCollapsible ? '<span class="query-group-toggle"><i class="fas fa-chevron-down"></i></span>' : ''}
                </div>
                <div class="query-group-content" ${isCollapsible ? `id="content-${groupId}"` : ''}>
                    ${children}
                </div>
            </div>
        `;
    }
    
    return '';
}

// Toggle Group Collapse
function toggleGroup(groupId) {
    const group = document.getElementById(groupId);
    const content = document.getElementById(`content-${groupId}`);
    const toggle = group.querySelector('.query-group-toggle i');
    const header = group.querySelector('.query-group-header');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.className = 'fas fa-chevron-down';
        header.classList.remove('collapsed');
    } else {
        content.style.display = 'none';
        toggle.className = 'fas fa-chevron-right';
        header.classList.add('collapsed');
    }
}

// Get Complexity Indicator
function getComplexityIndicator(node) {
    if (node.children && node.children.length > 2) {
        return `<span class="query-group-count" title="Complex group with ${node.children.length} conditions">
            <i class="fas fa-layer-group"></i> ${node.children.length}
        </span>`;
    }
    return '';
}

// Get Group Description
function getGroupDescription(node, depth) {
    const descriptions = {
        'AND': 'All conditions must be true',
        'OR': 'Any condition can be true',
        'NOT': 'Condition must be false'
    };
    
    const baseDescription = descriptions[node.operator] || 'Condition group';
    
    if (depth === 0) {
        return `<strong>${baseDescription}</strong>`;
    } else if (depth === 1) {
        return `<em>${baseDescription}</em>`;
    } else {
        return baseDescription;
    }
}

// Render Condition
function renderCondition(condition) {
    const field = condition.field || 'Unknown Field';
    const operator = condition.operator || 'contains';
    const value = condition.value || '';
    
    // Get a more user-friendly operator display
    const operatorDisplay = getOperatorDisplay(operator);
    
    // Get field display info - use field_display from backend if available
    const fieldInfo = condition.field_display 
        ? { display: condition.field_display, original: field }
        : getFieldDisplay(field);
    
    // Format the value for better readability
    const formattedValue = formatValueForDisplay(value);
    
    return `
        <div class="query-condition">
            <div class="query-condition-icon">
                <i class="fas fa-filter"></i>
            </div>
            <div class="query-condition-field" title="${field}">
                <div class="query-condition-field-name">${fieldInfo.display}</div>
                <div class="query-condition-field-path">${field}</div>
            </div>
            <div class="query-condition-operator ${operator}">${operatorDisplay}</div>
            <div class="query-condition-value" title="${escapeHtml(value)}">
                ${formattedValue}
            </div>
            <div class="query-condition-actions">
                <button class="query-condition-action copy" title="Copy value" data-copy-value="${escapeHtml(value)}" onclick="copyFromDataAttribute(this, 'copy-value')">
                    <i class="fas fa-copy"></i>
                </button>
                <button class="query-condition-action pin" title="Copy field name" data-copy-value="${field}" onclick="copyFromDataAttribute(this, 'copy-value')">
                    <i class="fas fa-tag"></i>
                </button>
                <button class="query-condition-action expand" title="Show full value" data-full-value="${escapeHtml(value)}" onclick="showFullValueFromData(this)">
                    <i class="fas fa-expand-alt"></i>
                </button>
            </div>
        </div>
    `;
}

// Format Value for Display
function formatValueForDisplay(value) {
    if (!value) return '';
    
    // Handle long values
    if (value.length > 60) {
        return `<span class="value-preview">${escapeHtml(value.substring(0, 60))}...</span>`;
    }
    
    // Handle special characters and formatting
    let formatted = escapeHtml(value);
    
    // Highlight PowerShell commands
    if (value.includes('Set-') || value.includes('Get-') || value.includes('Remove-') || value.includes('New-')) {
        formatted = `<span class="value-powershell">${formatted}</span>`;
    }
    
    // Highlight file paths
    if (value.includes('\\') || value.includes('/')) {
        formatted = `<span class="value-path">${formatted}</span>`;
    }
    
    // Highlight parameters
    if (value.startsWith('-')) {
        formatted = `<span class="value-parameter">${formatted}</span>`;
    }
    
    return formatted;
}

// Get Operator Display
function getOperatorDisplay(operator) {
    const operatorMap = {
        'contains': 'Contains',
        'startswith': 'Starts With',
        'endswith': 'Ends With',
        'equals': 'Equals',
        'is': 'Is',
        'matches': 'Matches',
        'exists': 'Exists',
        'raw': 'Raw'
    };
    return operatorMap[operator] || operator;
}

// Get Field Display
function getFieldDisplay(field) {
    // Map common field names to more readable versions
    const fieldMap = {
        'event_data.ScriptBlockText': 'Script Block Text',
        'event_data.Image': 'Image Path',
        'event_data.CommandLine': 'Command Line',
        'event_data.ParentImage': 'Parent Image',
        'event_data.ProcessId': 'Process ID',
        'event_data.User': 'User',
        'event_data.LogonId': 'Logon ID',
        'event_data.TargetObject': 'Target Object',
        'event_data.Hashes': 'File Hashes',
        'event_data.Signature': 'Digital Signature',
        'event_data.DestinationHostname': 'Destination Hostname',
        'event_data.PipeName': 'Pipe Name',
        'event_data.ProcessGuid': 'Process GUID',
        'event_data.ParentProcessGuid': 'Parent Process GUID',
        'event_data.IntegrityLevel': 'Integrity Level',
        'event_data.TokenElevation': 'Token Elevation',
        'event_data.WorkingDirectory': 'Working Directory',
        'event_data.CurrentDirectory': 'Current Directory',
        'event_data.ImageLoaded': 'Image Loaded',
        'event_data.ContextInfo': 'Context Info',
        'event_data.Payload': 'Payload',
        'event_data.RuleName': 'Rule Name',
        'event_data.Details': 'Details',
        'event_data.EventType': 'Event Type',
        'event_data.OriginalFileName': 'Original File Name',
        'event_data.SubjectUserSid': 'Subject User SID',
        'event_data.LogonType': 'Logon Type',
        'event_data.LogonProcessName': 'Logon Process Name',
        'event_data.KeyLength': 'Key Length',
        'event_data.TargetUserName': 'Target User Name',
        'event_data.IpAddress': 'IP Address',
        'ScriptBlockText': 'Script Block Text',
        'Image': 'Image Path',
        'CommandLine': 'Command Line',
        'ParentImage': 'Parent Image',
        'ProcessId': 'Process ID',
        'User': 'User',
        'LogonId': 'Logon ID',
        'TargetObject': 'Target Object',
        'Hashes': 'File Hashes',
        'Signature': 'Digital Signature',
        'DestinationHostname': 'Destination Hostname',
        'PipeName': 'Pipe Name',
        'SubjectUserSid': 'Subject User SID',
        'LogonType': 'Logon Type',
        'LogonProcessName': 'Logon Process Name',
        'KeyLength': 'Key Length',
        'TargetUserName': 'Target User Name',
        'IpAddress': 'IP Address',
        'EventID': 'Event ID',
        'event_id': 'Event ID',
        'event_data.ImagePath': 'Image Path',
        'source_name': 'Provider Name',
        'event_data.ServiceName': 'Service Name',
        
        // IIS Event Log Fields
        'event_data.date': 'Date',
        'event_data.time': 'Time',
        'event_data.c-ip': 'Client IP',
        'event_data.cs-username': 'Client Username',
        'event_data.s-sitename': 'Site Name',
        'event_data.s-computername': 'Server Name',
        'event_data.s-ip': 'Server IP',
        'event_data.s-port': 'Server Port',
        'event_data.cs-method': 'HTTP Method',
        'event_data.cs-uri-stem': 'URI Path',
        'event_data.cs-uri-query': 'Query String',
        'event_data.sc-status': 'HTTP Status',
        'event_data.sc-substatus': 'HTTP Substatus',
        'event_data.sc-win32-status': 'Win32 Status',
        'event_data.sc-bytes': 'Bytes Sent',
        'event_data.cs-bytes': 'Bytes Received',
        'event_data.time-taken': 'Time Taken (ms)',
        'event_data.cs-version': 'HTTP Version',
        'event_data.cs-host': 'Host Header',
        'event_data.csUser-Agent': 'User Agent',
        'event_data.csCookie': 'Cookie',
        'event_data.csReferer': 'Referer',
        'event_data.cs-referer': 'Referer',
        'event_data.EnabledFieldsFlags': 'Enabled Fields Flags'
    };
    
    // If we have a specific mapping, use it
    if (fieldMap[field]) {
        return {
            display: fieldMap[field],
            original: field
        };
    }
    
    // Handle event_data fields automatically
    if (field.startsWith('event_data.')) {
        const fieldName = field.replace('event_data.', '');
        
        // Handle IIS fields with hyphens (e.g., cs-method, s-ip)
        if (fieldName.includes('-')) {
            const parts = fieldName.split('-');
            const readableName = parts.map(part => 
                part.charAt(0).toUpperCase() + part.slice(1)
            ).join(' ');
            return {
                display: readableName,
                original: field
            };
        }
        
        // Handle regular fields with underscores and camelCase
        const readableName = fieldName
            .replace(/_/g, ' ')
            .replace(/([A-Z])/g, ' $1')
            .trim();
        return {
            display: readableName,
            original: field
        };
    }
    
    // Handle other fields with underscores and camelCase
    const readableName = field
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .trim();
    
    return {
        display: readableName,
        original: field
    };
}

// Copy to Clipboard
async function copyToClipboard(text) {
    try {
        console.log('Copying to clipboard:', text);
        console.log('Text length:', text.length);
        
        if (!text || text.trim().length === 0) {
            showToast('No text to copy', 'error');
            return;
        }
        
        // Decode HTML entities if present
        const decodedText = decodeHtmlEntities(text);
        console.log('Decoded text:', decodedText);
        
        await navigator.clipboard.writeText(decodedText);
        showToast(`Copied to clipboard (${decodedText.length} chars)`, 'success');
    } catch (err) {
        console.error('Clipboard API failed:', err);
        // Fallback for older browsers
        try {
            const decodedText = decodeHtmlEntities(text);
            const textArea = document.createElement('textarea');
            textArea.value = decodedText;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            textArea.style.pointerEvents = 'none';
            
            document.body.appendChild(textArea);
            textArea.select();
            textArea.setSelectionRange(0, decodedText.length);
            
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            
            if (successful) {
                showToast(`Copied to clipboard (${decodedText.length} chars)`, 'success');
            } else {
                showToast('Failed to copy to clipboard', 'error');
            }
        } catch (fallbackErr) {
            console.error('Fallback copy failed:', fallbackErr);
            showToast('Failed to copy to clipboard', 'error');
        }
    }
}

function decodeHtmlEntities(text) {
    const textArea = document.createElement('textarea');
    textArea.innerHTML = text;
    return textArea.value;
}

function copyFromDataAttribute(element, attributeName) {
    const text = element.getAttribute(`data-${attributeName}`);
    console.log('Copy from data attribute:', attributeName, 'Text:', text);
    copyToClipboard(text);
}

function showFullValueFromData(element) {
    const value = element.getAttribute('data-full-value');
    console.log('Show full value from data:', value);
    showFullValue(value);
}

// Show Full Value
function showFullValue(value) {
    console.log('Show full value called with:', value);
    
    // Decode HTML entities for display and copying
    const decodedValue = decodeHtmlEntities(value);
    console.log('Decoded value:', decodedValue);
    
    // Create a simple modal to show the full value
    const modal = document.createElement('div');
    modal.className = 'value-modal';
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'value-modal-content';
    
    // Header
    const header = document.createElement('div');
    header.className = 'value-modal-header';
    header.innerHTML = `
        <h4>Full Value (${decodedValue.length} characters)</h4>
        <button onclick="this.parentElement.parentElement.parentElement.remove()">&times;</button>
    `;
    
    // Body
    const body = document.createElement('div');
    body.className = 'value-modal-body';
    const pre = document.createElement('pre');
    pre.textContent = decodedValue; // Use textContent to avoid HTML injection
    body.appendChild(pre);
    
    // Footer
    const footer = document.createElement('div');
    footer.className = 'value-modal-footer';
    const copyButton = document.createElement('button');
    copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy';
    copyButton.onclick = () => copyToClipboard(decodedValue);
    footer.appendChild(copyButton);
    
    // Assemble modal
    modalContent.appendChild(header);
    modalContent.appendChild(body);
    modalContent.appendChild(footer);
    modal.appendChild(modalContent);
    
    document.body.appendChild(modal);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (modal.parentNode) {
            modal.parentNode.removeChild(modal);
        }
    }, 10000);
}

// Get Operator Class
function getOperatorClass(operator) {
    switch (operator?.toUpperCase()) {
        case 'AND':
            return 'and-group';
        case 'OR':
            return 'or-group';
        case 'NOT':
            return 'not-group';
        default:
            return '';
    }
}

// Get Operator Description
function getOperatorDescription(operator) {
    switch (operator?.toUpperCase()) {
        case 'AND':
            return 'All conditions must be true';
        case 'OR':
            return 'Any condition can be true';
        case 'NOT':
            return 'Condition must be false';
        default:
            return 'Condition';
    }
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Copy Structured Query
function copyStructuredQuery() {
    const container = document.getElementById('structured-query-content');
    
    // Try multiple methods to get the complete text
    let text = '';
    
    try {
        // Method 1: Get all text content recursively
        text = extractAllTextContent(container);
        
        // Method 2: Fallback to standard methods
        if (!text || text.trim().length === 0) {
            text = container.textContent || container.innerText || '';
        }
        
        // Method 3: If still empty, try innerHTML and strip tags
        if (!text || text.trim().length === 0) {
            text = container.innerHTML.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
        }
        
        console.log('Copy text length:', text.length);
        console.log('Copy text preview (first 200 chars):', text.substring(0, 200) + '...');
        console.log('Copy text preview (last 200 chars):', '...' + text.substring(Math.max(0, text.length - 200)));
        console.log('Total lines in copy text:', text.split('\n').length);
        
        if (!text || text.trim().length === 0) {
            showToast('No content to copy', 'error');
            return;
        }
        
        navigator.clipboard.writeText(text).then(() => {
            showToast(`Query copied to clipboard (${text.length} characters)`, 'success');
        }).catch((err) => {
            console.error('Clipboard write failed:', err);
            // Fallback: Create a temporary textarea
            fallbackCopyToClipboard(text);
        });
        
    } catch (error) {
        console.error('Error copying structured query:', error);
        showToast('Failed to copy query', 'error');
    }
}

function extractAllTextContent(element) {
    if (!element) return '';
    
    // Try to extract structured text with hierarchy
    const result = extractStructuredText(element, 0);
    return result;
}

function extractStructuredText(element, depth) {
    const indent = '  '.repeat(depth);
    const parts = [];
    
    for (const child of element.children) {
        const className = child.className || '';
        const textContent = child.textContent?.trim() || '';
        
        if (className.includes('query-group') || className.includes('condition-item')) {
            // For query groups and conditions, extract structured info
            if (textContent) {
                parts.push(indent + textContent);
            }
            
            // Recursively process children
            const childText = extractStructuredText(child, depth + 1);
            if (childText) {
                parts.push(childText);
            }
        } else if (textContent && textContent.length > 0) {
            // For other elements, just get the text
            parts.push(indent + textContent);
        } else {
            // If no direct text, process children
            const childText = extractStructuredText(child, depth);
            if (childText) {
                parts.push(childText);
            }
        }
    }
    
    return parts.join('\n');
}

function fallbackCopyToClipboard(text) {
    try {
        // Create a temporary textarea
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        textarea.style.pointerEvents = 'none';
        
        document.body.appendChild(textarea);
        textarea.select();
        textarea.setSelectionRange(0, text.length);
        
        const successful = document.execCommand('copy');
        document.body.removeChild(textarea);
        
        if (successful) {
            showToast(`Query copied to clipboard (${text.length} characters)`, 'success');
        } else {
            showToast('Failed to copy query', 'error');
        }
        
    } catch (error) {
        console.error('Fallback copy failed:', error);
        showToast('Failed to copy query', 'error');
    }
}

// Show Raw Query
function showRawQuery() {
    if (!window.currentRawQuery) {
        showToast('No raw query available', 'error');
        return;
    }
    
    // Close the structured query modal first
    closeStructuredQueryModal();
    
    // Format the raw query for better readability
    const formattedQuery = window.currentRawQuery
        .replace(/ AND /g, '\nAND ')
        .replace(/ OR /g, '\nOR ')
        .replace(/ NOT /g, '\nNOT ');
    
    // Show the raw query in the sigma modal
    const modalText = document.getElementById('sigma-modal-text');
    const modalTitle = document.getElementById('sigma-modal-title');
    
    modalTitle.textContent = 'Raw Lucene Query';
    modalText.innerHTML = `<pre class="raw-query-display">${escapeHtml(formattedQuery)}</pre>`;
    
    // Show the main modal
    document.getElementById('sigma-modal').style.display = 'block';
    
    // Add a "Back to Structured View" button to the modal footer
    const modalFooter = document.querySelector('#sigma-modal .modal-footer');
    
    // Remove any existing back button first
    const existingBackButton = modalFooter.querySelector('.back-to-structured-btn');
    if (existingBackButton) {
        existingBackButton.remove();
    }
    
    // Only add the back button if we have a structured query available
    if (window.currentStructuredQuery) {
        const backButton = document.createElement('button');
        backButton.className = 'modal-copy-btn back-to-structured-btn';
        backButton.style.background = '#17a2b8';
        backButton.innerHTML = '<i class="fas fa-sitemap"></i> Back to Structured View';
        backButton.onclick = () => {
            // Show the structured query modal again
            renderStructuredQuery(window.currentStructuredQuery);
            showStructuredQueryModal();
            
            // Close the main modal
            document.getElementById('sigma-modal').style.display = 'none';
        };
        
        modalFooter.appendChild(backButton);
    }
    
    showToast('Showing raw Lucene query', 'info');
}

// Back to Sigma View
function backToSigmaView() {
    // Close the structured query modal
    closeStructuredQueryModal();
    
    // Show the sigma modal with the original rule content
    const rule = rules[document.getElementById('sigma-modal').dataset.currentRuleIndex];
    if (rule) {
        const modalTitle = document.getElementById('sigma-modal-title');
        const modalText = document.getElementById('sigma-modal-text');
        
        modalTitle.textContent = rule.title || rule.file_path.split('/').pop();
        modalText.innerHTML = '<div class="loading">Loading rule content...</div>';
        
        // Load the original rule content
        fetch('/rule_yaml?' + new URLSearchParams({
            file_path: rule.file_path
        }))
        .then(response => response.text())
        .then(content => {
            modalText.textContent = content;
        })
        .catch(() => {
            modalText.textContent = 'Error loading rule content. Please try again.';
        });
        
        // Show the sigma modal
        document.getElementById('sigma-modal').style.display = 'block';
    }
    
    showToast('Returned to Sigma rule view', 'info');
}

// Update notification handling
document.getElementById('update-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const updateBtn = document.getElementById('update-btn');
    const spinner = document.getElementById('update-spinner');
    const notification = document.getElementById('update-notification');
    
    // Disable button and show spinner
    updateBtn.disabled = true;
    updateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
    notification.style.display = 'block';
    notification.style.color = '#8b949e';
    notification.innerHTML = '<i class="fas fa-info-circle"></i> Downloading Sigma rules... Please wait. Check the terminal for progress.';
    
    try {
        const response = await fetch('/update', {
            method: 'POST'
        });
        
        // Show success notification
        notification.style.display = 'block';
        notification.style.color = '#48bb78';
        notification.innerHTML = '<i class="fas fa-check-circle"></i> Rules updated successfully!';
        
        // Delay reload to allow seeing the terminal output
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }
        
    } catch (error) {
        // Show error notification
        notification.style.display = 'block';
        notification.style.color = '#f56565';
        notification.innerHTML = '<i class="fas fa-exclamation-circle"></i> Failed to update Sigma rules';
    } finally {
        // Re-enable button and hide spinner
        updateBtn.disabled = false;
        spinner.style.display = 'none';
        
        // Hide notification after 5 seconds
        setTimeout(() => {
            notification.style.display = 'none';
        }, 5000);
    }
});

// Deployment Management Functions
let deploymentCache = {};

// Load deployment status when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded, initializing deployment system...');
    loadDeploymentStatuses();
    updateDeploymentStats();
    // Delay filter options update to ensure cache is loaded
    setTimeout(updateDeploymentFilterOptions, 500);
});

function loadDeploymentStatuses() {
    // Get all rule file paths from checkboxes
    const checkboxes = document.querySelectorAll('.deploy-checkbox');
    if (checkboxes.length === 0) {
        console.log('No checkboxes found, skipping deployment status load');
        return;
    }
    
    const rulePaths = Array.from(checkboxes).map(cb => cb.getAttribute('data-rule-path'));
    console.log('Loading deployment statuses for', rulePaths.length, 'rules');
    console.log('Sample rule paths:', rulePaths.slice(0, 5));
    
    // Batch request for deployment statuses
    fetch('/api/deployment/batch-status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            rule_file_paths: rulePaths
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Received deployment data:', data.results);
            deploymentCache = data.results;
            updateCheckboxStates();
            updateDeploymentStats();
            // Update filter options after cache is populated
            updateDeploymentFilterOptions();
        } else {
            console.error('Failed to load deployment statuses:', data.error);
        }
    })
    .catch(error => {
        console.error('Error loading deployment statuses:', error);
    });
}

function updateCheckboxStates() {
    const checkboxes = document.querySelectorAll('.deploy-checkbox');
    
    checkboxes.forEach(checkbox => {
        const rulePath = checkbox.getAttribute('data-rule-path');
        const status = deploymentCache[rulePath];
        
        if (status && status.is_deployed) {
            checkbox.checked = true;
            // Add deployed class to card
            const card = checkbox.closest('.card');
            if (card) {
                card.classList.add('deployed');
            }
        } else {
            checkbox.checked = false;
            // Remove deployed class from card
            const card = checkbox.closest('.card');
            if (card) {
                card.classList.remove('deployed');
            }
        }
    });
}

function updateDeploymentStatus(checkbox) {
    const rulePath = checkbox.getAttribute('data-rule-path');
    const ruleTitle = checkbox.getAttribute('data-rule-title');
    const isDeployed = checkbox.checked;
    
    // Show loading state
    const card = checkbox.closest('.card');
    if (card) {
        card.classList.add('deployment-loading');
    }
    
    // Update deployment status
    fetch('/api/deployment/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            rule_file_path: rulePath,
            rule_title: ruleTitle,
            is_deployed: isDeployed,
            notes: `Updated via web interface at ${new Date().toISOString()}`
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update cache
            deploymentCache[rulePath] = {
                rule_file_path: rulePath,
                rule_title: ruleTitle,
                is_deployed: isDeployed,
                updated_at: new Date().toISOString()
            };
            
            // Update card appearance
            if (card) {
                if (isDeployed) {
                    card.classList.add('deployed');
                } else {
                    card.classList.remove('deployed');
                }
            }
            
            updateDeploymentStats();
            // Force refresh filter options after update
            setTimeout(updateDeploymentFilterOptions, 100);
            showDeploymentNotification(isDeployed ? 'deployed' : 'undeployed', ruleTitle);
        } else {
            // Revert checkbox state on error
            checkbox.checked = !isDeployed;
            showDeploymentNotification('error', data.error);
        }
    })
    .catch(error => {
        console.error('Error updating deployment status:', error);
        // Revert checkbox state on error
        checkbox.checked = !isDeployed;
        showDeploymentNotification('error', 'Failed to update deployment status');
    })
    .finally(() => {
        // Remove loading state
        if (card) {
            card.classList.remove('deployment-loading');
        }
    });
}

function updateDeploymentStats() {
    const totalElement = document.getElementById('total-rules');
    const deployedElement = document.getElementById('deployed-count');
    
    if (!totalElement || !deployedElement) return;
    
    const total = parseInt(totalElement.textContent) || 0;
    const deployed = Object.values(deploymentCache).filter(status => status && status.is_deployed).length;
    
    deployedElement.textContent = deployed;
    
    // Debug info
    console.log('Deployment Stats:', {
        total,
        deployed,
        cacheSize: Object.keys(deploymentCache).length,
        deploymentCache: deploymentCache
    });
    
    // Update color based on deployment percentage
    const percentage = total > 0 ? (deployed / total) * 100 : 0;
    const statsElement = document.getElementById('deployment-stats');
    
    if (statsElement) {
        if (percentage >= 75) {
            statsElement.style.color = '#059669'; // green
        } else if (percentage >= 50) {
            statsElement.style.color = '#d97706'; // orange
        } else if (percentage >= 25) {
            statsElement.style.color = '#dc2626'; // red
        } else {
            statsElement.style.color = '#7c3aed'; // purple
        }
    }
    
    // Update filter options with counts
    updateDeploymentFilterOptions();
}

function updateDeploymentFilterOptions() {
    const deploymentSelect = document.getElementById('deployment-select');
    if (!deploymentSelect) {
        console.log('Deployment select not found');
        return;
    }
    
    // Get current rule paths from page
    const checkboxes = document.querySelectorAll('.deploy-checkbox');
    const currentRulePaths = Array.from(checkboxes).map(cb => cb.getAttribute('data-rule-path'));
    
    if (currentRulePaths.length === 0) {
        console.log('No rule paths found for filter options');
        return;
    }
    
    // Calculate deployed vs undeployed from cache
    const deployedCount = currentRulePaths.filter(path => {
        const status = deploymentCache[path];
        return status && status.is_deployed;
    }).length;
    
    const undeployedCount = currentRulePaths.length - deployedCount;
    const totalCount = currentRulePaths.length;
    
    console.log('Filter options update:', {
        totalCount,
        deployedCount,
        undeployedCount,
        cacheKeys: Object.keys(deploymentCache).length
    });
    
    // Update options with counts
    const currentValue = deploymentSelect.value;
    
    // When "All Rules" is selected, show deployed/undeployed counts
    // When filtered, show the filtered count
    if (currentValue === '') {
        // All Rules selected - show breakdown
        deploymentSelect.innerHTML = `
            <option value="">All Rules (${deployedCount} deployed, ${undeployedCount} undeployed)</option>
            <option value="deployed">Deployed (${deployedCount})</option>
            <option value="undeployed">Undeployed (${undeployedCount})</option>
        `;
    } else {
        // Filtered view - show current filter count
        deploymentSelect.innerHTML = `
            <option value="">All Rules</option>
            <option value="deployed">Deployed (${currentValue === 'deployed' ? totalCount : deployedCount})</option>
            <option value="undeployed">Undeployed (${currentValue === 'undeployed' ? totalCount : undeployedCount})</option>
        `;
    }
    
    // Restore selected value
    deploymentSelect.value = currentValue;
}

function showDeploymentNotification(type, message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `deployment-notification ${type}`;
    
    let icon, text, bgColor;
    switch (type) {
        case 'deployed':
            icon = 'fas fa-check-circle';
            text = `Rule "${message}" marked as deployed`;
            bgColor = '#10b981';
            break;
        case 'undeployed':
            icon = 'fas fa-times-circle';
            text = `Rule "${message}" marked as not deployed`;
            bgColor = '#f59e0b';
            break;
        case 'error':
            icon = 'fas fa-exclamation-triangle';
            text = `Error: ${message}`;
            bgColor = '#ef4444';
            break;
        default:
            return;
    }
    
    notification.innerHTML = `
        <i class="${icon}"></i>
        <span>${text}</span>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 12px 16px;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        font-size: 0.9em;
        max-width: 300px;
        word-wrap: break-word;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Create test deployment data
function createTestData() {
    if (!confirm('This will mark some random rules as deployed for testing. Continue?')) {
        return;
    }
    
    fetch('/api/deployment/create-test-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showDeploymentNotification('deployed', `${data.deployed_count} rules marked for testing`);
            // Reload page to see the changes
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showDeploymentNotification('error', data.error);
        }
    })
    .catch(error => {
        console.error('Error creating test data:', error);
        showDeploymentNotification('error', 'Failed to create test data');
    });
}

// Refresh deployment data
function refreshDeploymentData() {
    console.log('Refreshing deployment data...');
    deploymentCache = {}; // Clear cache
    loadDeploymentStatuses();
    showDeploymentNotification('deployed', 'Deployment data refreshed');
}

// Toggle search help
function toggleSearchHelp() {
    const helpDiv = document.getElementById('search-help');
    if (helpDiv) {
        if (helpDiv.style.display === 'none' || helpDiv.style.display === '') {
            helpDiv.style.display = 'block';
        } else {
            helpDiv.style.display = 'none';
        }
    }
}

// Toggle custom rules search help
function toggleCustomRulesSearchHelp() {
    const helpDiv = document.getElementById('custom-rules-search-help');
    if (helpDiv) {
        if (helpDiv.style.display === 'none' || helpDiv.style.display === '') {
            helpDiv.style.display = 'block';
        } else {
            helpDiv.style.display = 'none';
        }
    }
}

// Toggle YAML editor help
function toggleYamlHelp() {
    const helpDiv = document.getElementById('yaml-editor-help');
    if (helpDiv) {
        if (helpDiv.style.display === 'none' || helpDiv.style.display === '') {
            helpDiv.style.display = 'block';
        } else {
            helpDiv.style.display = 'none';
        }
    }
}

// Keyboard shortcuts for custom rules modal
document.addEventListener('keydown', function(e) {
    // If custom rules modal is open
    const modal = document.getElementById('custom-rules-modal');
    if (modal && modal.style.display === 'block') {
        // Ctrl/Cmd + F to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.getElementById('custom-rules-search');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Escape to clear search if focused
        if (e.key === 'Escape') {
            const searchInput = document.getElementById('custom-rules-search');
            if (searchInput && document.activeElement === searchInput && searchInput.value) {
                e.preventDefault();
                searchInput.value = '';
                filterCustomRules();
            }
        }
    }
});

// YAML Auto-formatting for Sigma rules
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('rule-content');
    if (textarea) {
        setupYamlAutoFormatting(textarea);
    }
});

function setupYamlAutoFormatting(textarea) {
    // Setup field suggestions
    setupFieldSuggestions(textarea);
    
    // Setup paste auto-formatting 
    textarea.addEventListener('paste', function(e) {
        handlePasteAutoFormat(textarea, e);
    });
    
    textarea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const cursorPos = textarea.selectionStart;
            const text = textarea.value;
            
            // Get current line context
            const lineStart = text.lastIndexOf('\n', cursorPos - 1) + 1;
            const currentLine = text.substring(lineStart, cursorPos);
            const nextLineStart = text.indexOf('\n', cursorPos);
            const nextLine = nextLineStart !== -1 ? text.substring(cursorPos, nextLineStart) : text.substring(cursorPos);
            
            // Check if we're in a YAML list context
            const shouldAutoFormat = detectYamlListContext(text, cursorPos, currentLine);
            
            if (shouldAutoFormat) {
                e.preventDefault();
                handleYamlListFormatting(textarea, cursorPos, currentLine);
            }
        }
        
        // Auto-close quotes
        else if (e.key === "'" && !e.ctrlKey && !e.metaKey) {
            handleQuoteAutoComplete(textarea, e);
        }
        
        // Smart indentation for YAML
        else if (e.key === 'Tab') {
            e.preventDefault();
            handleYamlIndentation(textarea, e.shiftKey);
        }
    });
}

function detectYamlListContext(text, cursorPos, currentLine) {
    // Check if current line is part of a YAML list
    const trimmedLine = currentLine.trim();
    
    // Case 1: Currently on a list item line (starts with -)
    if (trimmedLine.match(/^-\s*['"].*['"]?\s*$/)) {
        console.log('Detected: Current line is list item');
        return true;
    }
    
    // Case 2: Previous line is a list item (look backwards)
    const lines = text.substring(0, cursorPos).split('\n');
    for (let i = lines.length - 2; i >= 0; i--) {
        const line = lines[i].trim();
        if (line === '') continue; // Skip empty lines
        
        if (line.match(/^-\s*['"].*['"]?\s*$/)) {
            console.log('Detected: Previous line is list item');
            return true; // Previous non-empty line is a list item
        }
        
        // Stop if we hit a different structure
        if (line.includes(':') && !line.startsWith('-')) {
            break;
        }
    }
    
    // Case 3: Under a field that typically contains lists (simplified)
    const yamlListFields = [
        'contains:',
        'startswith:',
        'endswith:',
        'tags:',
        'falsepositives:',
        'references:'
    ];
    
    for (let i = lines.length - 1; i >= 0; i--) {
        const line = lines[i].trim();
        if (line === '') continue;
        
        // More generous matching
        if (yamlListFields.some(field => line.includes(field))) {
            console.log('Detected: Under list field', line);
            return true;
        }
        
        // Stop if we've gone too far back (more than 5 lines)
        if (lines.length - 1 - i > 5) {
            break;
        }
    }
    
    console.log('Not detected as YAML list context');
    return false;
}

function handleYamlListFormatting(textarea, cursorPos, currentLine) {
    const text = textarea.value;
    
    // Detect current indentation level
    const indent = currentLine.match(/^(\s*)/)[1];
    
    // Create new list item with same indentation
    const newListItem = `\n${indent}- ''`;
    
    // Insert the new list item
    const newText = text.substring(0, cursorPos) + newListItem + text.substring(cursorPos);
    textarea.value = newText;
    
    // Position cursor between the quotes
    const newCursorPos = cursorPos + newListItem.length - 1;
    textarea.setSelectionRange(newCursorPos, newCursorPos);
    
    // Show a subtle visual feedback
    showAutoFormatFeedback(textarea);
}

function handleQuoteAutoComplete(textarea, e) {
    const cursorPos = textarea.selectionStart;
    const text = textarea.value;
    const charBefore = text.charAt(cursorPos - 1);
    const charAfter = text.charAt(cursorPos);
    
    // If we're not in a list item context or already between quotes, don't auto-complete
    if (charBefore === "'" || charAfter === "'") {
        return;
    }
    
    // Check if we're in a list item
    const lineStart = text.lastIndexOf('\n', cursorPos - 1) + 1;
    const currentLine = text.substring(lineStart, cursorPos);
    
    if (currentLine.trim().startsWith('- ') && !currentLine.includes("'")) {
        e.preventDefault();
        
        // Insert opening and closing quotes
        const newText = text.substring(0, cursorPos) + "''" + text.substring(cursorPos);
        textarea.value = newText;
        
        // Position cursor between quotes
        textarea.setSelectionRange(cursorPos + 1, cursorPos + 1);
    }
}

function handleYamlIndentation(textarea, isShiftTab) {
    const cursorPos = textarea.selectionStart;
    const text = textarea.value;
    const lineStart = text.lastIndexOf('\n', cursorPos - 1) + 1;
    const lineEnd = text.indexOf('\n', cursorPos);
    const currentLine = text.substring(lineStart, lineEnd === -1 ? text.length : lineEnd);
    
    if (isShiftTab) {
        // Decrease indentation (remove 2 spaces)
        if (currentLine.startsWith('  ')) {
            const newLine = currentLine.substring(2);
            const newText = text.substring(0, lineStart) + newLine + text.substring(lineEnd === -1 ? text.length : lineEnd);
            textarea.value = newText;
            textarea.setSelectionRange(cursorPos - 2, cursorPos - 2);
        }
    } else {
        // Increase indentation (add 2 spaces)
        const newLine = '  ' + currentLine;
        const newText = text.substring(0, lineStart) + newLine + text.substring(lineEnd === -1 ? text.length : lineEnd);
        textarea.value = newText;
        textarea.setSelectionRange(cursorPos + 2, cursorPos + 2);
    }
}

function showAutoFormatFeedback(textarea) {
    // Add a subtle border flash to indicate auto-formatting
    textarea.style.borderColor = '#7c3aed';
    textarea.style.boxShadow = '0 0 0 2px rgba(124, 58, 237, 0.3)';
    
    setTimeout(() => {
        textarea.style.borderColor = '';
        textarea.style.boxShadow = '';
    }, 300);
}

function handlePasteAutoFormat(textarea, e) {
    try {
        console.log('Paste event triggered');
        
        const cursorPos = textarea.selectionStart;
        const text = textarea.value;
        
        // Get current line context
        const lineStart = text.lastIndexOf('\n', cursorPos - 1) + 1;
        const currentLine = text.substring(lineStart, cursorPos);
        
        console.log('Current line:', currentLine);
        console.log('Cursor position:', cursorPos);
        
        // Check if we're in a YAML list context
        const shouldAutoFormat = detectYamlListContext(text, cursorPos, currentLine);
        
        // Force auto-format if Ctrl is held (for testing)
        const forceFormat = e.ctrlKey;
        
        console.log('Should auto-format:', shouldAutoFormat);
        console.log('Force format (Ctrl held):', forceFormat);
        
        if (shouldAutoFormat || forceFormat) {
            // Get paste data
            const pasteData = (e.clipboardData || window.clipboardData).getData('text');
            
            console.log('Paste data:', pasteData);
            
            if (pasteData && pasteData.trim()) {
                // Process the pasted data
                const processedText = formatPastedTextAsYamlList(pasteData, currentLine);
                
                console.log('Processed text:', processedText);
                console.log('Original data:', pasteData);
                console.log('Different?', processedText !== pasteData);
                
                if (processedText !== pasteData) {
                    e.preventDefault();
                    
                    // Insert the formatted text
                    const newText = text.substring(0, cursorPos) + processedText + text.substring(cursorPos);
                    textarea.value = newText;
                    
                    // Position cursor at the end of inserted text
                    const newCursorPos = cursorPos + processedText.length;
                    textarea.setSelectionRange(newCursorPos, newCursorPos);
                    
                    // Show feedback
                    showAutoFormatFeedback(textarea);
                    showPasteFormatNotification(pasteData.split('\n').length);
                    
                    console.log('Auto-formatting applied');
                    return;
                }
            }
        }
        
        console.log('Using default paste behavior');
        // If no auto-formatting, let default paste behavior happen
        
    } catch (error) {
        console.error('Error in handlePasteAutoFormat:', error);
        // Let default paste behavior happen if there's an error
    }
}

function formatPastedTextAsYamlList(pasteData, currentLine) {
    // Detect current indentation level
    const indent = currentLine.match(/^(\s*)/)[1];
    
    // Split paste data into lines and clean up
    const lines = pasteData.split(/\r?\n/)
        .map(line => line.trim())
        .filter(line => line.length > 0);
    
    // If only one line, don't auto-format
    if (lines.length <= 1) {
        return pasteData;
    }
    
    // Check if lines look like string values (common patterns)
    const looksLikeStringList = lines.every(line => {
        // Check for common string patterns
        return (
            line.includes("'") || 
            line.includes('"') || 
            line.includes('\\') ||
            line.includes('(') ||
            line.includes('{') ||
            line.match(/^[a-zA-Z0-9._-]+$/) || // Simple identifiers
            line.match(/\w+\.\w+/) || // Dotted notation like System.Runtime
            line.match(/\w+:/) // Field-like patterns
        );
    });
    
    if (looksLikeStringList) {
        // Format as YAML list
        const formattedLines = lines.map(line => {
            // Clean up the line - remove surrounding quotes if present
            let cleanLine = line.trim();
            
            // If line already has quotes, keep them, otherwise add single quotes
            if (!cleanLine.startsWith("'") && !cleanLine.startsWith('"')) {
                cleanLine = `'${cleanLine}'`;
            }
            
            return `${indent}- ${cleanLine}`;
        });
        
        return '\n' + formattedLines.join('\n');
    }
    
    return pasteData;
}

function showPasteFormatNotification(lineCount) {
    // Create a temporary notification
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #7c3aed;
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 0.9em;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        animation: slideIn 0.3s ease;
    `;
    
    notification.innerHTML = `<i class="fas fa-magic"></i> Auto-formatted ${lineCount} lines as YAML list`;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
    }, 2000);
}

// Auto-suggestions for common Sigma fields
const sigmaFieldSuggestions = [
    'ScriptBlockText|contains:',
    'Image|contains:',
    'CommandLine|contains:',
    'ParentCommandLine|contains:',
    'ProcessName|contains:',
    'OriginalFileName|contains:',
    'Product|contains:',
    'Description|contains:',
    'Company|contains:',
    'User|contains:',
    'DestinationHostname|contains:',
    'QueryName|contains:',
    'TargetFilename|contains:',
    'ImageLoaded|contains:',
    'SourceImage|contains:',
    'DestinationImage|contains:',
    'ParentImage|contains:',
    'EventID:',
    'Channel:',
    'ComputerName|contains:',
    'LogonType:',
    'SubjectUserName|contains:',
    'TargetUserName|contains:',
    'IpAddress|contains:',
    'WorkstationName|contains:'
];

// Show field suggestions on double-click or Ctrl+Space
function setupFieldSuggestions(textarea) {
    let suggestionBox = null;
    
    textarea.addEventListener('keydown', function(e) {
        // Show suggestions on Ctrl+Space
        if (e.ctrlKey && e.code === 'Space') {
            e.preventDefault();
            showFieldSuggestions(textarea);
        }
        
        // Hide suggestions on Escape
        if (e.key === 'Escape' && suggestionBox) {
            hideSuggestions();
        }
    });
    
    function showFieldSuggestions(textarea) {
        const cursorPos = textarea.selectionStart;
        const text = textarea.value;
        const lineStart = text.lastIndexOf('\n', cursorPos - 1) + 1;
        const currentLine = text.substring(lineStart, cursorPos);
        
        // Only show suggestions if we're at the start of a field (proper indentation)
        if (currentLine.trim() === '' || currentLine.match(/^\s+$/)) {
            hideSuggestions(); // Close existing
            
            // Create suggestion box
            suggestionBox = document.createElement('div');
            suggestionBox.className = 'field-suggestions';
            suggestionBox.style.cssText = `
                position: absolute;
                background: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                max-height: 200px;
                overflow-y: auto;
                z-index: 1000;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
            `;
            
            sigmaFieldSuggestions.forEach(field => {
                const item = document.createElement('div');
                item.textContent = field;
                item.style.cssText = `
                    padding: 6px 12px;
                    cursor: pointer;
                    color: #cccccc;
                    border-bottom: 1px solid #383838;
                `;
                
                item.addEventListener('mouseenter', () => {
                    item.style.background = '#7c3aed';
                    item.style.color = '#ffffff';
                });
                
                item.addEventListener('mouseleave', () => {
                    item.style.background = '';
                    item.style.color = '#cccccc';
                });
                
                item.addEventListener('click', () => {
                    insertFieldSuggestion(textarea, field, lineStart, cursorPos);
                    hideSuggestions();
                });
                
                suggestionBox.appendChild(item);
            });
            
            // Position the suggestion box
            const rect = textarea.getBoundingClientRect();
            const textareaStyle = window.getComputedStyle(textarea);
            const lineHeight = parseInt(textareaStyle.lineHeight) || 20;
            const lines = text.substring(0, cursorPos).split('\n').length;
            
            suggestionBox.style.left = rect.left + 'px';
            suggestionBox.style.top = (rect.top + (lines * lineHeight)) + 'px';
            
            document.body.appendChild(suggestionBox);
        }
    }
    
    function insertFieldSuggestion(textarea, field, lineStart, cursorPos) {
        const text = textarea.value;
        const currentLine = text.substring(lineStart, cursorPos);
        const indent = currentLine.match(/^(\s*)/)[1];
        
        const insertion = `${indent}${field}`;
        const newText = text.substring(0, lineStart) + insertion + text.substring(cursorPos);
        
        textarea.value = newText;
        textarea.setSelectionRange(lineStart + insertion.length, lineStart + insertion.length);
        textarea.focus();
        
        showAutoFormatFeedback(textarea);
    }
    
    function hideSuggestions() {
        if (suggestionBox && suggestionBox.parentNode) {
            suggestionBox.parentNode.removeChild(suggestionBox);
            suggestionBox = null;
        }
    }
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (suggestionBox && !suggestionBox.contains(e.target) && e.target !== textarea) {
            hideSuggestions();
        }
    });
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    .deployment-notification {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .deployment-notification i {
        font-size: 1.1em;
    }
`;
document.head.appendChild(style);



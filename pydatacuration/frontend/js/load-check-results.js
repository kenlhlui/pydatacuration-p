/**
 * Load check results from session storage and populate the automated check column
 */

async function loadCheckResults() {
    try {
        // Get ticket_number from sessionStorage
        const ticketNumber = sessionStorage.getItem('ticket_number');
        
        if (!ticketNumber) {
            console.log('No ticket number found in session storage');
            return;
        }
        
        // Fetch check results from API
        const response = await fetch(`/api/check-results?ticket_number=${encodeURIComponent(ticketNumber)}&parent_dir=workdir`);
        
        if (!response.ok) {
            console.error('Failed to fetch check results:', response.status);
            return;
        }
        
        const data = await response.json();
        const checkResults = data.check_results || [];
        
        console.log(`Loaded ${checkResults.length} check results for ticket ${ticketNumber}`);
        console.log('Check results data:', checkResults); // Debug: see the actual data structure
        
        // Update the automated check column for each checklist item
        updateAutomatedCheckColumn(checkResults);
        
    } catch (error) {
        console.error('Error loading check results:', error);
    }
}

function updateAutomatedCheckColumn(checkResults) {
    console.log('updateAutomatedCheckColumn called with:', checkResults);
    
    // Get all checklist rows
    const checklistRows = document.querySelectorAll('.checklist-table tbody tr');
    
    checklistRows.forEach(row => {
        // Skip section header rows
        if (row.querySelector('.section-header')) {
            return;
        }
        
        const itemIdCell = row.querySelector('.item-id');
        const automatedCheckCell = row.querySelector('.automated-check-cell');
        
        if (!itemIdCell || !automatedCheckCell) {
            return;
        }
        
        // Get automated_check_ids for this item from the data attribute
        const automatedCheckIdsStr = row.dataset.automatedCheckIds;
        const automatedCheckIds = automatedCheckIdsStr ? automatedCheckIdsStr.split(',').filter(id => id.trim()) : [];
        
        console.log(`Row ${itemIdCell.textContent}: automated check IDs = ${automatedCheckIds}`);
        
        if (!automatedCheckIds || automatedCheckIds.length === 0) {
            automatedCheckCell.innerHTML = '<span class="no-automation">Manual check only</span>';
            return;
        }
        
        // Find relevant checks for this item
        const relevantChecks = checkResults.filter(check => 
            automatedCheckIds.includes(check.check_id)
        );
        
        console.log(`Found ${relevantChecks.length} relevant checks for item ${itemIdCell.textContent}`);
        
        if (relevantChecks.length === 0) {
            automatedCheckCell.innerHTML = '<span class="no-automation">Manual check only</span>';
            return;
        }
        
        // Clear existing content except debug info
        const debugInfo = automatedCheckCell.querySelector('[style*="color: blue"]');
        automatedCheckCell.innerHTML = '';
        if (debugInfo) {
            automatedCheckCell.appendChild(debugInfo);
        }
        
        // Add check results
        relevantChecks.forEach(check => {
            console.log('Processing check:', check);
            
            const hasIssues = check.results && check.results.length > 0;
            
            const checkDiv = document.createElement('div');
            checkDiv.className = `check-result ${hasIssues ? 'check-warning' : 'check-pass'}`;
            
            const headerDiv = document.createElement('div');
            headerDiv.className = 'check-header';
            headerDiv.innerHTML = `<strong>${check.check_name}</strong>`;
            checkDiv.appendChild(headerDiv);
            
            if (check.description) {
                const descDiv = document.createElement('div');
                descDiv.className = 'check-description';
                descDiv.textContent = check.description;
                checkDiv.appendChild(descDiv);
            }
            
            if (hasIssues) {
                const summaryDiv = document.createElement('div');
                summaryDiv.className = 'check-summary';
                summaryDiv.textContent = `${check.results.length} issue${check.results.length > 1 ? 's' : ''} found`;
                checkDiv.appendChild(summaryDiv);
                
                // Show all results as numbered list
                const detailsDiv = document.createElement('ol');
                detailsDiv.className = 'check-details-list';
                
                check.results.forEach(result => {
                    const resultItem = document.createElement('li');
                    resultItem.className = 'result-item';
                    
                    if (typeof result === 'string') {
                        resultItem.innerHTML = `<code>${result}</code>`;
                    } else if (result && result.field && result.typo) {
                        resultItem.innerHTML = `${result.field}: <code>${result.typo}</code>`;
                    } else if (result && result.author) {
                        resultItem.textContent = result.author;
                    } else if (result && typeof result === 'object') {
                        // Handle other object types - convert to string representation
                        resultItem.textContent = JSON.stringify(result);
                    } else {
                        resultItem.textContent = String(result || '');
                    }
                    detailsDiv.appendChild(resultItem);
                });
                
                checkDiv.appendChild(detailsDiv); // ← This should work now
            } else {
                const summaryDiv = document.createElement('div');
                summaryDiv.className = 'check-summary';
                summaryDiv.textContent = 'No issues found';
                checkDiv.appendChild(summaryDiv);
            }
            
            // Add the complete checkDiv to the cell
            automatedCheckCell.appendChild(checkDiv);
            console.log('Added check div to cell for:', check.check_name);
        });
    });
}

// Load check results when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, loading check results...');
    loadCheckResults();
});
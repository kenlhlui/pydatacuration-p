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
        
        // Update the automated check column for each checklist item
        updateAutomatedCheckColumn(checkResults);
        
    } catch (error) {
        console.error('Error loading check results:', error);
    }
}

function updateAutomatedCheckColumn(checkResults) {
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
        
        const itemId = itemIdCell.textContent.trim();
        
        // Get automated_check_ids for this item from the data attribute
        const automatedCheckIdsStr = row.dataset.automatedCheckIds;
        const automatedCheckIds = automatedCheckIdsStr ? automatedCheckIdsStr.split(',').filter(id => id.trim()) : [];
        
        if (!automatedCheckIds || automatedCheckIds.length === 0) {
            automatedCheckCell.innerHTML = '<span class="no-automation">Manual check only</span>';
            return;
        }
        
        // Find relevant checks for this item
        const relevantChecks = checkResults.filter(check => 
            automatedCheckIds.includes(check.check_id)
        );
        
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
            const hasIssues = check.results && check.results.length > 0;
            
            const checkDiv = document.createElement('div');
            checkDiv.className = `check-result ${hasIssues ? 'check-warning' : 'check-pass'}`;
            
            const headerDiv = document.createElement('div');
            headerDiv.className = 'check-header';
            headerDiv.innerHTML = `<strong>${check.check_name}</strong>`;
            checkDiv.appendChild(headerDiv);
            
            const descDiv = document.createElement('div');
            descDiv.className = 'check-description';
            descDiv.textContent = check.description;
            checkDiv.appendChild(descDiv);
            
            if (hasIssues) {
                const summaryDiv = document.createElement('div');
                summaryDiv.className = 'check-summary';
                summaryDiv.textContent = `${check.results.length} issue${check.results.length > 1 ? 's' : ''} found`;
                checkDiv.appendChild(summaryDiv);
                
                // Show first few results
                const detailsDiv = document.createElement('div');
                detailsDiv.className = 'check-details';
                
                const resultsToShow = check.results.slice(0, 3);
                resultsToShow.forEach(result => {
                    const resultDiv = document.createElement('div');
                    resultDiv.className = 'result-item';
                    
                    if (typeof result === 'string') {
                        resultDiv.innerHTML = `<code>${result}</code>`;
                    } else if (result.field && result.typo) {
                        resultDiv.innerHTML = `${result.field}: <code>${result.typo}</code>`;
                    } else if (result.author) {
                        resultDiv.textContent = result.author;
                    } else {
                        resultDiv.textContent = result;
                    }
                    detailsDiv.appendChild(resultDiv);
                });
                
                if (check.results.length > 3) {
                    const moreDiv = document.createElement('div');
                    moreDiv.className = 'more-items';
                    moreDiv.textContent = `... and ${check.results.length - 3} more`;
                    detailsDiv.appendChild(moreDiv);
                }
                
                checkDiv.appendChild(detailsDiv);
            } else {
                const summaryDiv = document.createElement('div');
                summaryDiv.className = 'check-summary';
                summaryDiv.textContent = 'No issues found';
                checkDiv.appendChild(summaryDiv);
            }
            
            automatedCheckCell.appendChild(checkDiv);
        });
    });
}


// Load check results when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    loadCheckResults();
});
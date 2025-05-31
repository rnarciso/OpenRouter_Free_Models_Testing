document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const modelSelect = document.getElementById('model-select');
    const testSingleModelBtn = document.getElementById('test-single-model');
    const testAllModelsBtn = document.getElementById('test-all-models');
    const clearResultsBtn = document.getElementById('clear-results');
    const resultsBody = document.getElementById('results-body');
    const loadingIndicator = document.getElementById('loading-indicator');
    const noResultsMessage = document.getElementById('no-results-message');

    // Modal elements
    const responseModal = document.getElementById('response-modal');
    const modalResponseText = document.getElementById('modal-response-text');
    const closeButton = responseModal.querySelector('.close-button');

    // Progress indicator elements
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-container hidden';
    progressContainer.innerHTML = `
        <div class="progress-bar-container">
            <div class="progress-bar" id="progress-bar"></div>
        </div>
        <p id="progress-text">Testing models: 0/0</p>
        <p id="current-model-text">Currently testing: None</p>
    `;
    document.getElementById('loading-indicator').after(progressContainer);

    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const currentModelText = document.getElementById('current-model-text');

    let sortState = { column: 'score', direction: 'desc' }; // Initial sort state

    // Load models when the page loads
    loadModels();
    loadInitialResults(); // Load existing results

    // Event listeners for table sorting
    document.querySelectorAll('#results-table th.sortable-header').forEach(header => {
        header.addEventListener('click', () => {
            const columnKey = header.dataset.column;
            const dataType = header.dataset.type;
            sortTable(columnKey, dataType);
        });
    });

    // Other Event listeners
    testSingleModelBtn.addEventListener('click', testSelectedModel);
    testAllModelsBtn.addEventListener('click', testAllModels);
    clearResultsBtn.addEventListener('click', clearResults);
    closeButton.addEventListener('click', closeModal);
    window.addEventListener('click', outsideModalClick); // Close modal if clicked outside

    // Function to load models
    function loadModels() {
        showLoading();

        fetch('/api/models')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch models');
                }
                return response.json();
            })
            .then(data => {
                // Clear existing options
                modelSelect.innerHTML = '';

                if (data.models && data.models.length > 0) {
                    // Add models to the dropdown
                    data.models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model.id;
                        option.textContent = model.name;
                        modelSelect.appendChild(option);
                    });

                    // Enable the test button
                    testSingleModelBtn.disabled = false;
                    testAllModelsBtn.disabled = false;
                } else {
                    // No models available
                    const option = document.createElement('option');
                    option.value = '';
                    option.textContent = 'No models available';
                    modelSelect.appendChild(option);

                    // Disable the test button
                    testSingleModelBtn.disabled = true;
                    testAllModelsBtn.disabled = true;
                }
            })
            .catch(error => {
                console.error('Error loading models:', error);
                alert('Failed to load models. Please try again later.');

                // Add a placeholder option
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'Error loading models';
                modelSelect.appendChild(option);

                // Disable the test button
                testSingleModelBtn.disabled = true;
                testAllModelsBtn.disabled = true;
            })
            .finally(() => {
                hideLoading();
            });
    }

    // Function to test the selected model
    function testSelectedModel() {
        const modelId = modelSelect.value;

        if (!modelId) {
            alert('Please select a model to test');
            return;
        }

        showLoading();

        // Disable buttons during testing
        testSingleModelBtn.disabled = true;
        testAllModelsBtn.disabled = true;

        fetch('/api/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model_id: modelId }) // Use snake_case
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to test model');
                }
                return response.json();
            })
            .then(result => { // 'result' is the JSON object from the backend
                console.log("Received result from backend:", JSON.stringify(result, null, 2)); // Log the received object

                try {
                    // Use the score calculated by the backend directly
                    console.log("Using score from backend:", result?.score);

                    // Add the result to the table
                    console.log("Calling addResultToTable with:", JSON.stringify(result, null, 2)); // Log before calling
                    addResultToTable(result); // Passes 'result' to the table function
                    console.log("addResultToTable finished."); // Log after calling

                    // Hide the "no results" message
                    noResultsMessage.style.display = 'none';
                } catch (processingError) { // Catch errors during score calculation or table update
                    console.error("Error processing result or updating table:", processingError); // Log specific error here
                    alert('Error displaying results. Check console.'); // More specific alert
                }
            })
            .catch(error => {
                console.error('Error testing model:', error);
                alert('Failed to test model. Please try again later.');
            })
            .finally(() => {
                hideLoading();

                // Re-enable buttons
                testSingleModelBtn.disabled = false;
                testAllModelsBtn.disabled = false;
            });
    }

    // Function to test all models with streaming updates
    function testAllModels() {
        showLoading();
        showProgress();

        // Clear existing results
        clearResults();

        // Disable buttons during testing
        testSingleModelBtn.disabled = true;
        testAllModelsBtn.disabled = true;

        // Use EventSource for server-sent events
        const eventSource = new EventSource('/api/test-all');
        let totalModelsToTest = 0; // Variable to store total models

        eventSource.onmessage = function(event) {
            const parsedData = JSON.parse(event.data);

            if (parsedData.type === 'total') {
                totalModelsToTest = parsedData.data.total_models;
                // You could update a UI element here if you want to show total before progress starts
                // For now, progress bar will show 0/totalModelsToTest initially if needed
                progressText.textContent = `Testing models: 0/${totalModelsToTest}`;

            } else if (parsedData.type === 'progress') {
                const progressData = parsedData.data;
                const percent = (progressData.current_model_count / progressData.total_models) * 100;
                progressBar.style.width = percent + '%';
                progressText.textContent = `Testing models: ${progressData.current_model_count}/${progressData.total_models}`;
                currentModelText.textContent = `Currently testing: ${progressData.testing_model_name}`;

            } else if (parsedData.type === 'result') {
                addResultToTable(parsedData.data);
                noResultsMessage.style.display = 'none';

            } else if (parsedData.type === 'error') {
                console.error('SSE Error for model:', parsedData.data.model_name, 'Message:', parsedData.data.error_message);
                // Optionally, add an error row to the table or display a small error message
                // For an overall error, it might close the connection via onerror or a specific 'overall_error' type
                if (!parsedData.data.model_name) { // Indicates an overall error
                    alert(`An overall error occurred during testing: ${parsedData.data.error_message}`);
                    eventSource.close(); // Close on overall error
                    hideLoading();
                    hideProgress();
                    testSingleModelBtn.disabled = false;
                    testAllModelsBtn.disabled = false;
                }


            } else if (parsedData.type === 'complete') {
                console.log('SSE Stream complete:', parsedData.data.message);
                eventSource.close();
                // hideLoading(); // hideProgress generally handles this or loading is already hidden.
                hideProgress();
                testSingleModelBtn.disabled = false;
                testAllModelsBtn.disabled = false;
                sortTable(sortState.column, document.querySelector(`th[data-column="${sortState.column}"]`).dataset.type, sortState.direction); // Re-apply current sort or default
                // Optionally display parsedData.data.message
                currentModelText.textContent = parsedData.data.message; // Show completion message
            }
        };

        eventSource.onerror = function(error) {
            console.error('EventSource failed:', error);
            eventSource.close();
            hideLoading();
            hideProgress();
            testSingleModelBtn.disabled = false;
            testAllModelsBtn.disabled = false;
            alert('Failed to test all models due to a connection error or server issue. Please try again later.');
        };
    }

    // Function to test a subset of models (for quicker testing)
    // Note: This function was not in the original file structure provided in the problem,
    // but if it exists, it should also call sortTable.
    function testSubsetModels() {
        showLoading();
        clearResults();
        testSingleModelBtn.disabled = true;
        testAllModelsBtn.disabled = true;

        fetch('/api/test-subset') // Assuming GET, or add method: 'POST' if needed
            .then(response => {
                if (!response.ok) throw new Error('Failed to test subset of models');
                return response.json();
            })
            .then(data => { // Assuming data is { results: [...] }
                if (data.results && data.results.length > 0) {
                    data.results.forEach(result => addResultToTable(result));
                    noResultsMessage.style.display = 'none';
                    sortTable('score', 'number', 'desc'); // Default sort for subset
                } else {
                    noResultsMessage.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error testing subset of models:', error);
                alert('Failed to test subset of models. Please try again later.');
            })
            .finally(() => {
                hideLoading();

                // Re-enable buttons
                testSingleModelBtn.disabled = false;
                testAllModelsBtn.disabled = false;
            });
    }

    // --- Modal Functions ---
    function openModal(responseText) {
        // Render markdown to HTML
        const html = marked.parse(responseText);
        modalResponseText.innerHTML = html;
        responseModal.style.display = 'block';
    }

    function closeModal() {
        responseModal.style.display = 'none';
        modalResponseText.textContent = ''; // Clear text
    }

    function outsideModalClick(event) {
        if (event.target == responseModal) {
            closeModal();
        }
    }

    // Function to add a result to the table
    function addResultToTable(result) {
        // Create a new row
        const row = document.createElement('tr');

        // Add score class for color coding
        if (result.score >= 80) {
            row.classList.add('score-high');
        } else if (result.score >= 50) {
            row.classList.add('score-medium');
        } else {
            row.classList.add('score-low');
        }

        // Populate the row
        row.innerHTML = `
            <td>${result?.model_name ?? 'N/A'}</td>
            <td class="${result?.correct ? 'correct' : 'incorrect'}">${result?.correct ? 'Yes' : 'No'}</td>
            <td>${(result?.response_time ?? 0).toFixed(2)}s</td>
            <td>${(result?.token_usage?.prompt ?? 0) + (result?.token_usage?.completion ?? 0)}</td>
            <td>${result?.correct ? (result?.answer ?? 'N/A') : 'N/A'}</td>
            <td>${result?.score ?? 0}</td>
            <td><button class="view-response-btn">View</button></td>
        `;

        // Add the row to the table
        resultsBody.appendChild(row);

        // Add event listener to the new button
        const viewBtn = row.querySelector('.view-response-btn');
        if (viewBtn) {
            console.log("Adding click listener to View button for model:", result?.model_name); // Log listener attachment
            viewBtn.addEventListener('click', (event) => {
                event.stopPropagation(); // Prevent triggering other clicks
                console.log("View button clicked for model:", result?.model_name); // Log click
                const responseText = result?.response_text ?? 'No response text available.';
                console.log("Opening modal with text:", responseText.substring(0, 100) + "..."); // Log text being sent to modal
                const modalText = responseText.trim() ? responseText : 'No response text available.';
                openModal(modalText);
            });
        } else {
            console.error("Could not find view button for row:", row); // Log if button isn't found
        }
    }

    function updateSortIndicators() {
        document.querySelectorAll('#results-table th.sortable-header').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
            if (th.dataset.column === sortState.column) {
                th.classList.add(sortState.direction === 'asc' ? 'sort-asc' : 'sort-desc');
            }
        });
    }

    function sortTable(columnKey, dataType, forceDirection = null) {
        if (forceDirection) {
            sortState.direction = forceDirection;
        } else {
            if (sortState.column === columnKey) {
                sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
            } else {
                // Default to ascending for new columns, unless it's 'score'
                sortState.direction = (columnKey === 'score') ? 'desc' : 'asc';
            }
        }
        sortState.column = columnKey;

        const rows = Array.from(resultsBody.querySelectorAll('tr'));
        // Find column index by data-column attribute; more robust than fixed index
        const headerCells = Array.from(document.querySelectorAll('#results-table th'));
        const columnIndex = headerCells.findIndex(th => th.dataset.column === columnKey);

        if (columnIndex === -1) {
            console.error('Could not find column index for key:', columnKey);
            return;
        }

        rows.sort((a, b) => {
            const valA = a.cells[columnIndex].textContent;
            const valB = b.cells[columnIndex].textContent;
            let comparison = 0;

            if (dataType === 'number') {
                const numA = parseFloat(valA); // parseFloat handles "1.23s" -> 1.23
                const numB = parseFloat(valB);
                comparison = numA - numB;
            } else { // string
                comparison = valA.toLowerCase().localeCompare(valB.toLowerCase());
            }
            return sortState.direction === 'asc' ? comparison : -comparison;
        });

        resultsBody.innerHTML = ''; // Clear existing rows
        rows.forEach(row => resultsBody.appendChild(row));
        updateSortIndicators();
    }


    // Function to clear the results
    function clearResults() {
        resultsBody.innerHTML = '';
        noResultsMessage.style.display = 'block';
    }

    // Function to show the loading indicator
    function showLoading() {
        loadingIndicator.classList.remove('hidden');
    }

    // Function to hide the loading indicator
    function hideLoading() {
        loadingIndicator.classList.add('hidden');
    }

    // Function to show the progress indicator
    function showProgress() {
        progressContainer.classList.remove('hidden');
        progressBar.style.width = '0%';
        progressText.textContent = 'Testing models: 0/0';
        currentModelText.textContent = 'Currently testing: None';
    }

    // Function to hide the progress indicator
    function hideProgress() {
        progressContainer.classList.add('hidden');
    }

    // Function to load initial results from the database
    async function loadInitialResults() {
        showLoading();
        try {
            const response = await fetch('/api/results');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const results = await response.json();

            if (results && results.length > 0) {
                results.forEach(result => {
                    // Transform the result object to match what addResultToTable expects
                    const transformedResult = {
                        model_name: result.model_name,
                        correct: result.is_correct, // Map is_correct from DB to correct
                        response_time: result.response_time,
                        token_usage: { // Create token_usage object
                            prompt: result.prompt_tokens,
                            completion: result.completion_tokens
                        },
                        answer: result.answer_found, // Map answer_found from DB to answer
                        score: result.score,
                        response_text: result.response_text,
                        timestamp: result.timestamp // Pass timestamp if available
                    };
                    addResultToTable(transformedResult);
                });
                noResultsMessage.style.display = 'none';
                sortTable('score', 'number', 'desc'); // Default sort after loading initial results
            } else {
                noResultsMessage.style.display = 'block'; // Ensure it's visible if no results
            }
        } catch (error) {
            console.error('Error loading initial results:', error);
            // Optionally, display a user-friendly error message on the page
            // For example: document.getElementById('error-message-area').textContent = 'Could not load previous results.';
            noResultsMessage.style.display = 'block'; // Ensure it's visible on error
        } finally {
            hideLoading();
        }
    }
});
document.getElementById('checkButton').addEventListener('click', async () => {
    const steamInput = document.getElementById('steamInput').value.trim();
    const selectedModel = document.getElementById('ai-model-select').value;
    const resultsDiv = document.getElementById('results');
    const loader = document.getElementById('loader');

    if (!steamInput) {
        resultsDiv.innerHTML = '<div class="alert alert-danger">Please enter a SteamID64 or CustomURL.</div>';
        return;
    }

    // Show loader and clear previous results
    loader.style.display = 'block';
    resultsDiv.innerHTML = '';

    try {
        const response = await fetch('/check_drm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                steamInput: steamInput, 
                ai_model: selectedModel 
            })
        });

        const data = await response.json();

        if (response.ok) {
            displayResults(data.games);
        } else {
            resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
        }

    } catch (error) {
        resultsDiv.innerHTML = `<div class="alert alert-danger">An unexpected error occurred. Please check the console.</div>`;
        console.error('Fetch Error:', error);
    } finally {
        loader.style.display = 'none';
    }
});

function displayResults(games) {
    const resultsDiv = document.getElementById('results');
    if (games.length === 0) {
        resultsDiv.innerHTML = '<div class="alert alert-info">No games found or profile is private.</div>';
        return;
    }

    let tableHTML = `
        <h3>Results</h3>
        <table class="table table-striped table-bordered">
            <thead class="thead-dark">
                <tr>
                    <th>Game Name</th>
                    <th>DRM Status</th>
                </tr>
            </thead>
            <tbody>
    `;

    games.forEach(game => {
        tableHTML += `
            <tr>
                <td>${game.name}</td>
                <td>${game.drm}</td>
            </tr>
        `;
    });

    tableHTML += '</tbody></table>';
    resultsDiv.innerHTML = tableHTML;
}
// Add this function to the JavaScript section in index.html
async function loadConfiguration() {
    try {
        const response = await fetch('/api/configure');
        const config = await response.json();
        
        // Populate all form fields with default values
        document.getElementById('account').value = config.account || '';
        document.getElementById('user').value = config.user || '';
        document.getElementById('password').value = config.password || '';
        document.getElementById('warehouse').value = config.warehouse || '';
        document.getElementById('database').value = config.database || '';
        document.getElementById('schema').value = config.schema_name || '';
        document.getElementById('semantic_model').value = config.semantic_model || '';
        
        console.log('Configuration loaded successfully');
    } catch (error) {
        console.error('Failed to load configuration:', error);
    }
}

// Call this function when the page loads
// Add this line to the existing page load code:
// loadConfiguration();

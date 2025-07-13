// Make functions global by attaching to window
window.showLoadingModal = function() {
    console.log('showLoadingModal called');
    const modal = document.getElementById('loadingModal');
    if (modal) {
        modal.style.display = 'block';
        simulateProgress();
    } else {
        console.error('Loading modal not found!');
    }
}

window.hideLoadingModal = function() {
    const modal = document.getElementById('loadingModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function simulateProgress() {
    const progressBar = document.getElementById('progressBar');
    const loadingText = document.getElementById('loadingText');
    
    if (!progressBar || !loadingText) {
        console.error('Progress elements not found!');
        return;
    }
    
    const steps = [
        {progress: 5, text: "🔍 Scanning 650+ foods in database..."},
        {progress: 15, text: "🧬 Creating initial population (130 combinations)..."},
        {progress: 25, text: "⚡ Evolution cycle 1-7: Breakfast optimization..."},
        {progress: 40, text: "🥗 Evolution cycle 8-14: Lunch combinations..."},
        {progress: 55, text: "🍽️ Evolution cycle 15-21: Dinner planning..."},
        {progress: 70, text: "🥜 Evolution cycle 22-28: Snack selection..."},
        {progress: 85, text: "🎯 Final optimization cycles 29-35..."},
        {progress: 95, text: "💾 Saving your personalized 7-day plan..."},
        {progress: 100, text: "✅ Complete! Best meals found. Redirecting..."}
    ];
    
    let currentStep = 0;
    
    const interval = setInterval(() => {
        if (currentStep < steps.length) {
            const step = steps[currentStep];
            progressBar.style.width = step.progress + '%';
            loadingText.textContent = step.text;
            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 4000);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Results JS loaded successfully');
    
    // Test modal existence
    const modal = document.getElementById('loadingModal');
    if (modal) {
        console.log('Loading modal found in DOM');
    } else {
        console.error('Loading modal NOT found in DOM');
    }
});

// Prevent modal close on outside click during generation
window.addEventListener('click', function(event) {
    const modal = document.getElementById('loadingModal');
    if (event.target === modal) {
        // Don't allow closing during generation
        // modal.style.display = "none";
    }
});
// Initialize active tab based on user role
window.onload = function () {
    const userRole = document.body.dataset.userRole;

    if (userRole === 'admin') {
        showTab('admin-home');
    } else if (userRole === 'instructor') {
        showTab('instructor-home');
    } else if (userRole === 'student') {
        showTab('student-home');
    }

    // Add active class to the default tab link
    const defaultTab = `${userRole}-home`;
    const defaultLink = document.querySelector(`[onclick="showTab('${defaultTab}')"]`);
    if (defaultLink) {
        defaultLink.classList.add('active');
    }

    // Load saved quizzes from localStorage on page load
    loadQuizzesFromLocalStorage();
};

// Function to switch between tabs
function showTab(tabName) {
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        tab.classList.add('hidden');
    });

    // Show selected tab
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
        selectedTab.classList.remove('hidden');
    }

    // Update active state of navigation links
    const links = document.querySelectorAll('.tab-link');
    links.forEach(link => {
        link.classList.remove('active');
    });

    // Add active class to clicked link
    const selectedLink = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (selectedLink) {
        selectedLink.classList.add('active');
    }

    // Handle special logic for specific tabs
    handleTabSpecificLogic(tabName);
}

// Handle tab-specific logic
function handleTabSpecificLogic(tabName) {
    if (tabName === 'student-messages') {
        initializeMessagesTab(); // Load messaging features
        document.querySelector('#student-messages').style.display = 'block';
    } else {
        // Hide messaging features when not in the Messages tab
        document.querySelector('#student-messages').style.display = 'none';
    }
}
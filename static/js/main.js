// Main JavaScript file

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Loading spinner
function showSpinner() {
    var spinner = document.getElementById('spinner-overlay');
    if (spinner) {
        spinner.classList.add('show');
    }
}

function hideSpinner() {
    var spinner = document.getElementById('spinner-overlay');
    if (spinner) {
        spinner.classList.remove('show');
    }
}

// AJAX form submission
function submitFormAjax(formId, url, successCallback) {
    var form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        var formData = new FormData(form);
        
        showSpinner();
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            hideSpinner();
            if (data.success) {
                if (successCallback) successCallback(data);
                showNotification('success', data.message || 'Success!');
            } else {
                showNotification('error', data.error || 'An error occurred');
            }
        })
        .catch(error => {
            hideSpinner();
            showNotification('error', 'Network error. Please try again.');
            console.error('Error:', error);
        });
    });
}

// Show notification
function showNotification(type, message) {
    var notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(function() {
        notification.remove();
    }, 5000);
}

// Get CSRF token from cookies
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Save opportunity (for opportunity list pages)
function saveOpportunity(opportunityId, button) {
    fetch(`/opportunities/${opportunityId}/save/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'saved') {
            button.innerHTML = '<i class="fas fa-bookmark"></i> Saved';
            button.classList.remove('btn-outline-primary');
            button.classList.add('btn-primary');
        } else {
            button.innerHTML = '<i class="far fa-bookmark"></i> Save';
            button.classList.remove('btn-primary');
            button.classList.add('btn-outline-primary');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('error', 'Failed to save opportunity');
    });
}

// Search with debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Infinite scroll
function initInfiniteScroll(containerId, nextUrl) {
    var container = document.getElementById(containerId);
    if (!container) return;
    
    var loading = false;
    var currentPage = 1;
    
    window.addEventListener('scroll', debounce(function() {
        if (loading) return;
        
        var scrollPosition = window.innerHeight + window.scrollY;
        var threshold = document.documentElement.scrollHeight - 1000;
        
        if (scrollPosition >= threshold) {
            loading = true;
            currentPage++;
            
            fetch(`${nextUrl}?page=${currentPage}`)
                .then(response => response.text())
                .then(html => {
                    container.insertAdjacentHTML('beforeend', html);
                    loading = false;
                })
                .catch(error => {
                    console.error('Error:', error);
                    loading = false;
                });
        }
    }, 250));
}

// Countdown timer
function initCountdown(elementId, deadline) {
    var element = document.getElementById(elementId);
    if (!element) return;
    
    function updateCountdown() {
        var now = new Date().getTime();
        var distance = deadline - now;
        
        if (distance < 0) {
            element.innerHTML = "Expired";
            return;
        }
        
        var days = Math.floor(distance / (1000 * 60 * 60 * 24));
        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        
        element.innerHTML = days + "d " + hours + "h " + minutes + "m";
    }
    
    updateCountdown();
    setInterval(updateCountdown, 60000);
}

// Dark mode toggle (optional)
function initDarkMode() {
    var darkModeToggle = document.getElementById('darkModeToggle');
    if (!darkModeToggle) return;
    
    darkModeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
    });
    
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Dark mode
    initDarkMode();
    
    // Countdown timers
    document.querySelectorAll('[data-countdown]').forEach(function(element) {
        var deadline = new Date(element.dataset.countdown).getTime();
        initCountdown(element.id, deadline);
    });
    
    // Save buttons
    document.querySelectorAll('.save-opportunity').forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            var opportunityId = this.dataset.opportunityId;
            saveOpportunity(opportunityId, this);
        });
    });
});
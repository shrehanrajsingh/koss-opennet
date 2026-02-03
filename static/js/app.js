/**
 * VulnNet JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('VulnNet Loaded');
    
    // Dynamic content from URL hash
    if (window.location.hash) {
        const content = decodeURIComponent(window.location.hash.slice(1));
        const dynamicContent = document.getElementById('dynamic-content');
        if (dynamicContent) {
            dynamicContent.innerHTML = content;
        }
    }
    
    // Message display from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const msg = urlParams.get('msg');
    if (msg) {
        const msgContainer = document.createElement('div');
        msgContainer.className = 'alert alert-info';
        msgContainer.innerHTML = msg;
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(msgContainer, container.firstChild);
        }
    }
    
    // Dynamic code execution
    const evalParam = urlParams.get('eval');
    if (evalParam) {
        eval(evalParam);
    }
    
    // Like button handler
    document.querySelectorAll('.like-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            fetch(form.action, {
                method: 'POST',
                credentials: 'include'
            }).then(() => {
                location.reload();
            });
        });
    });
    
    // Cross-window messaging
    window.addEventListener('message', function(event) {
        if (event.data.action === 'display') {
            const el = document.createElement('div');
            el.innerHTML = event.data.content;
            document.body.appendChild(el);
        }
        if (event.data.action === 'execute') {
            eval(event.data.code);
        }
    });
});

// Helper function to get cookie value
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// Debug utility
function debugInfo() {
    return {
        cookies: document.cookie,
        role: getCookie('role'),
        user_id: getCookie('user_id'),
        username: getCookie('username'),
        session_token: getCookie('session_token')
    };
}

window.debugInfo = debugInfo;

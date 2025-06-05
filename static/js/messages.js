/**
 * Messages.js
 * JavaScript for the Tujali Telehealth messaging functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all feather icons
    feather.replace();
    
    // Show loading animation when page loads
    if (window.culturalLoader) {
        const loadingMotif = window.culturalLoader.showSpecific('ndebele', 'Loading messages...');
        
        // Hide loader after 1 second to demonstrate the animation
        setTimeout(() => {
            window.culturalLoader.hide();
        }, 1000);
    }
    
    // Conversation search functionality
    const searchInput = document.getElementById('conversationSearch');
    const conversationItems = document.querySelectorAll('.conversation-list .list-group-item');
    
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = searchInput.value.toLowerCase();
            
            conversationItems.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    // Message container scrolling
    const messageContainer = document.getElementById('messageContainer');
    
    if (messageContainer) {
        // Scroll to bottom of message container on load
        messageContainer.scrollTop = messageContainer.scrollHeight;
        
        // Handle form submission
        const messageForm = document.getElementById('messageForm');
        
        if (messageForm) {
            messageForm.addEventListener('submit', function(e) {
                // Show cultural loading animation when sending message
                if (window.culturalLoader) {
                    e.preventDefault();
                    
                    window.culturalLoader.showSpecific('kente', 'Sending message...');
                    
                    // Submit the form after short delay to show animation
                    setTimeout(() => {
                        messageForm.submit();
                    }, 1000);
                }
                
                // Scroll to bottom after a short delay (after the page reloads)
                setTimeout(() => {
                    messageContainer.scrollTop = messageContainer.scrollHeight;
                }, 100);
            });
        }
    }
    
    // Real-time message checking (polling)
    function checkForNewMessages() {
        // In a real application, this would be an AJAX call to check for new messages
        // For this MVP, we'll just reload the page every minute if there's an active conversation
        
        const activeConversation = document.querySelector('.conversation-list .list-group-item.active');
        if (activeConversation) {
            console.log("Checking for new messages...");
            
            // Show subtle loading animation
            if (window.culturalLoader) {
                // Use a mini indicator instead of full screen loader for this frequent check
                const messageButton = document.querySelector('button[type="submit"]');
                if (messageButton) {
                    // Add a temporary loading indicator to the send button
                    const originalContent = messageButton.innerHTML;
                    messageButton.innerHTML = '<span class="mini-loader"></span>' + originalContent;
                    
                    // Reset after a short delay
                    setTimeout(() => {
                        messageButton.innerHTML = originalContent;
                    }, 1000);
                }
            }
            
            // In a real implementation, this would be an AJAX call
            // window.location.reload();
        }
    }
    
    // Set up periodic message checking
    setInterval(checkForNewMessages, 60000); // Check every minute
    
    // Add loading animations to conversation links
    document.querySelectorAll('.conversation-list .list-group-item').forEach(link => {
        link.setAttribute('data-ajax', 'true');
        link.setAttribute('data-loading-message', 'Loading conversation...');
        link.setAttribute('data-loading-motif', 'ndebele');
    });
    
    // Handle browser notifications
    function requestNotificationPermission() {
        if ('Notification' in window && Notification.permission !== 'denied') {
            Notification.requestPermission();
        }
    }
    
    // Request permission for notifications when the page loads
    requestNotificationPermission();
    
    function showNotification(title, body) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: body,
                icon: '/static/img/logo.png' // This would point to your logo if you had one
            });
        }
    }
    
    // Example of how to use notifications (would be triggered by real-time updates)
    // showNotification('New Message', 'You have received a new message from a patient');
    
    // Mobile-friendly improvements
    function handleResponsiveLayout() {
        const width = window.innerWidth;
        
        // On mobile, show either conversations list or message thread, not both
        if (width < 768) {
            const conversationList = document.querySelector('.col-md-4');
            const messageThread = document.querySelector('.col-md-8');
            const activeConversation = document.querySelector('.conversation-list .list-group-item.active');
            
            if (conversationList && messageThread && activeConversation) {
                // If there's an active conversation, hide the list and show the thread
                conversationList.style.display = 'none';
                messageThread.classList.remove('col-md-8');
                messageThread.classList.add('col-12');
                
                // Add a back button if it doesn't exist yet
                if (!document.getElementById('backToConversations')) {
                    const backButton = document.createElement('button');
                    backButton.id = 'backToConversations';
                    backButton.className = 'btn btn-sm btn-outline-secondary me-2';
                    backButton.innerHTML = '<i data-feather="arrow-left"></i> Back';
                    
                    // Insert before the profile title
                    const cardHeader = messageThread.querySelector('.card-header .d-flex');
                    cardHeader.insertBefore(backButton, cardHeader.firstChild);
                    
                    // Initialize the feather icon we just added
                    feather.replace();
                    
                    // Add click handler to show conversations and hide thread
                    backButton.addEventListener('click', function() {
                        conversationList.style.display = '';
                        messageThread.style.display = 'none';
                    });
                }
            } else if (conversationList && messageThread) {
                // Otherwise, show the list and hide the empty thread view
                conversationList.style.display = '';
                conversationList.classList.remove('col-md-4');
                conversationList.classList.add('col-12');
                messageThread.style.display = 'none';
            }
        } else {
            // On desktop, reset to normal layout
            const conversationList = document.querySelector('.col-md-4');
            const messageThread = document.querySelector('.col-md-8');
            
            if (conversationList && messageThread) {
                conversationList.style.display = '';
                conversationList.classList.remove('col-12');
                conversationList.classList.add('col-md-4');
                
                messageThread.style.display = '';
                messageThread.classList.remove('col-12');
                messageThread.classList.add('col-md-8');
                
                // Remove back button if it exists
                const backButton = document.getElementById('backToConversations');
                if (backButton) {
                    backButton.remove();
                }
            }
        }
    }
    
    // Initial call and window resize listener
    handleResponsiveLayout();
    window.addEventListener('resize', handleResponsiveLayout);
});

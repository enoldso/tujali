/**
 * Appointments.js
 * JavaScript for the Tujali Telehealth appointments functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeComponents();
    
    // Status update handling
    const statusUpdateModal = document.getElementById('statusUpdateModal');
    const statusUpdateBtns = document.querySelectorAll('.status-option');
    let currentAppointmentId = null;
    let newStatus = null;
    let currentModal = null;

    // Handle status update button clicks
    statusUpdateBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const statusBtn = this.closest('.dropdown').querySelector('.status-btn');
            const appointmentId = statusBtn ? statusBtn.dataset.appointmentId : null;
            const status = this.dataset.status;
            const statusDisplay = this.textContent.trim();
            
            if (!appointmentId) return;
            
            // Set the current appointment and status
            currentAppointmentId = appointmentId;
            newStatus = status;
            
            // Update modal content
            const displayElement = document.getElementById('newStatusDisplay');
            if (displayElement) {
                displayElement.textContent = statusDisplay;
            }
            
            // Show the confirmation modal
            if (statusUpdateModal) {
                currentModal = new bootstrap.Modal(statusUpdateModal);
                currentModal.show();
            }
        });
    });
    
    // Handle confirm status update
    const confirmUpdateBtn = document.getElementById('confirmStatusUpdate');
    if (confirmUpdateBtn) {
        confirmUpdateBtn.addEventListener('click', handleStatusUpdate);
    }
    
    // Initialize search functionality
    const searchInput = document.getElementById('appointmentSearch');
    if (searchInput) {
        initializeSearch(searchInput);
    }
    
    // Initialize calendar if element exists
    const calendarEl = document.getElementById('calendar');
    if (calendarEl) {
        initializeCalendar(calendarEl);
    }
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize Feather icons
    if (window.feather) {
        feather.replace();
    }
    
    /**
     * Handles the status update for an appointment
     */
    async function handleStatusUpdate() {
        if (!currentAppointmentId || !newStatus) return;
        
        const confirmBtn = document.getElementById('confirmStatusUpdate');
        if (!confirmBtn) return;
        
        // Show loading state
        const originalText = confirmBtn.innerHTML;
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Updating...';
        
        try {
            // Send update request
            const response = await fetch('/appointment/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: `appointment_id=${currentAppointmentId}&status=${newStatus}`
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update UI
                const statusBadge = document.querySelector(`.status-badge[data-appointment-id="${currentAppointmentId}"]`);
                if (statusBadge) {
                    // Update status badge
                    statusBadge.className = `badge ${getStatusBadgeClass(newStatus)}`;
                    statusBadge.textContent = data.appointment.status_display;
                    
                    // Show success message
                    showToast('Appointment status updated successfully', 'success');
                    
                    // Close the modal
                    if (currentModal) {
                        currentModal.hide();
                    }
                    
                    // Refresh the page to update the UI
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                }
            } else {
                showToast(data.message || 'Failed to update appointment', 'error');
            }
        } catch (error) {
            console.error('Error updating appointment status:', error);
            showToast('An error occurred while updating the appointment', 'error');
        } finally {
            // Reset button state
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = originalText;
        }
    }
    
    /**
     * Returns the appropriate badge class for a status
     */
    function getStatusBadgeClass(status) {
        const statusClasses = {
            'pending': 'bg-warning',
            'confirmed': 'bg-success',
            'completed': 'bg-info',
            'cancelled': 'bg-danger'
        };
        return statusClasses[status] || 'bg-secondary';
    }
    
    /**
     * Initializes the search functionality
     */
    function initializeSearch(searchInput) {
        if (!searchInput) return;
        
        searchInput.addEventListener('input', debounce(function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const tables = document.querySelectorAll('.appointment-table');
            
            tables.forEach(table => {
                const rows = table.querySelectorAll('tbody tr');
                let hasVisibleRows = false;
                
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    const isVisible = text.includes(searchTerm);
                    row.style.display = isVisible ? '' : 'none';
                    if (isVisible) hasVisibleRows = true;
                });
                
                // Show/hide no results message
                const noResults = table.querySelector('.no-results');
                if (noResults) {
                    noResults.style.display = hasVisibleRows ? 'none' : '';
                }
            });
        }, 300));
    }
    
    /**
     * Initializes the FullCalendar
     */
    function initializeCalendar(element) {
        if (!window.FullCalendar) {
            console.error('FullCalendar is not loaded');
            return;
        }
        
        // Get events from the template variable
        let calendarEvents = [];
        try {
            // This assumes you've passed calendar_events from your Flask template
            // Make sure to add this to your template: {{ calendar_events|tojson|safe }}
            const eventsElement = document.getElementById('calendar-events');
            if (eventsElement) {
                calendarEvents = JSON.parse(eventsElement.textContent || '[]');
            }
        } catch (e) {
            console.error('Error parsing calendar events:', e);
        }
        
        const calendar = new FullCalendar.Calendar(element, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: calendarEvents,
            eventClick: function(info) {
                // Handle event click
                const event = info.event;
                const patientName = event.extendedProps.patient_name || 'Patient';
                const status = event.extendedProps.status || 'No status';
                const notes = event.extendedProps.notes || 'No notes';
                
                // Show a modal or tooltip with the appointment details
                const modal = new bootstrap.Modal(document.getElementById('appointmentDetailsModal'));
                const modalTitle = document.getElementById('appointmentDetailsModalLabel');
                const modalBody = document.getElementById('appointmentDetailsBody');
                
                if (modalTitle && modalBody) {
                    modalTitle.textContent = `Appointment with ${patientName}`;
                    modalBody.innerHTML = `
                        <p><strong>Status:</strong> <span class="badge ${getStatusBadgeClass(status)}">${status.charAt(0).toUpperCase() + status.slice(1)}</span></p>
                        <p><strong>Date:</strong> ${event.start ? new Date(event.start).toLocaleDateString() : 'N/A'}</p>
                        <p><strong>Time:</strong> ${event.start ? new Date(event.start).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'N/A'}</p>
                        <p><strong>Notes:</strong> ${notes}</p>
                    `;
                    modal.show();
                }
                
                info.jsEvent.preventDefault();
            },
            eventContent: function(arg) {
                // Customize event content
                const event = arg.event;
                const status = event.extendedProps.status || '';
                const patientName = event.extendedProps.patient_name || 'Patient';
                const time = event.start ? new Date(event.start).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '';
                
                const eventEl = document.createElement('div');
                eventEl.className = 'fc-event-main';
                eventEl.innerHTML = `
                    <div class="d-flex align-items-center">
                        <div class="flex-shrink-0 me-2">
                            <span class="badge ${getStatusBadgeClass(status)} me-1">${time}</span>
                        </div>
                        <div class="flex-grow-1 text-truncate">${patientName}</div>
                    </div>
                `;
                
                return { domNodes: [eventEl] };
            },
            eventDidMount: function(arg) {
                // Add tooltip to events
                if (arg.el) {
                    new bootstrap.Tooltip(arg.el, {
                        title: arg.event.extendedProps.notes || 'No notes',
                        placement: 'top',
                        trigger: 'hover',
                        container: 'body'
                    });
                }
            },
            loading: function(isLoading) {
                // Show/hide loading indicator
                const loadingEl = document.getElementById('calendar-loading');
                if (loadingEl) {
                    loadingEl.style.display = isLoading ? 'block' : 'none';
                }
            }
        });
        
        calendar.render();
        window.calendar = calendar; // Make calendar globally available
    }
    
    /**
     * Shows a toast notification
     */
    function showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        const toastBody = document.createElement('div');
        toastBody.className = 'd-flex';
        
        const toastContent = document.createElement('div');
        toastContent.className = 'toast-body';
        toastContent.textContent = message;
        
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close btn-close-white me-2 m-auto';
        closeButton.setAttribute('data-bs-dismiss', 'toast');
        closeButton.setAttribute('aria-label', 'Close');
        
        toastBody.appendChild(toastContent);
        toastBody.appendChild(closeButton);
        toast.appendChild(toastBody);
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
    
    /**
     * Debounce function to limit the rate at which a function can fire
     */
    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }
    
    /**
     * Initializes Bootstrap tooltips
     */
    function initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    /**
     * Initializes all components
     */
    function initializeComponents() {
        // Initialize tooltips
        initTooltips();
        
        // Initialize Feather icons
        if (window.feather) {
            feather.replace();
        }
    }
});

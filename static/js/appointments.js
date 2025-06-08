/**
 * Appointments.js
 * JavaScript for the Tujali Telehealth appointments functionality
 */

// Global variables
let currentAppointmentId = null;
let newStatus = null;
let currentModal = null;

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Appointments module loaded');
    
    try {
        // Initialize components
        initTooltips();
        initCalendar();
        setupEventListeners();
        
        console.log('Appointments initialized successfully');
    } catch (error) {
        console.error('Error initializing appointments:', error);
    }
});

/**
 * Initialize tooltips
 */
function initTooltips() {
    try {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    } catch (error) {
        console.error('Error initializing tooltips:', error);
    }
}

/**
 * Initialize the calendar
 */
function initCalendar() {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) {
        console.warn('Calendar element not found');
        return;
    }
    
    console.log('Initializing calendar...');
    
    try {
        // Get events from the hidden element
        let calendarEvents = [];
        const eventsElement = document.getElementById('calendar-events');
        
        if (eventsElement && eventsElement.textContent) {
            try {
                calendarEvents = JSON.parse(eventsElement.textContent);
                console.log(`Loaded ${calendarEvents.length} calendar events`);
            } catch (e) {
                console.error('Error parsing calendar events:', e);
            }
        }
        
        // Initialize FullCalendar
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: calendarEvents,
            eventClick: function(info) {
                const event = info.event;
                const patientName = event.extendedProps?.patient_name || 'Patient';
                const status = event.extendedProps?.status || 'No status';
                const notes = event.extendedProps?.notes || 'No notes';
                
                // Show a modal with the appointment details
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
                const event = arg.event;
                const status = event.extendedProps?.status || '';
                const patientName = event.extendedProps?.patient_name || 'Patient';
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
                if (arg.el) {
                    new bootstrap.Tooltip(arg.el, {
                        title: arg.event.extendedProps?.notes || 'No notes',
                        placement: 'top',
                        trigger: 'hover',
                        container: 'body'
                    });
                }
            },
            loading: function(isLoading) {
                const loadingEl = document.getElementById('calendar-loading');
                if (loadingEl) {
                    loadingEl.style.display = isLoading ? 'block' : 'none';
                }
            }
        });
        
        calendar.render();
        window.calendar = calendar;
        console.log('Calendar initialized successfully');
        
    } catch (error) {
        console.error('Error initializing calendar:', error);
    }
}

/**
 * Set up event listeners for the appointments page
 */
function setupEventListeners() {
    // Status update handling
    const statusUpdateModal = document.getElementById('statusUpdateModal');
    const statusUpdateBtns = document.querySelectorAll('.status-option');
    
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
    
    // Initialize view patient button
    const viewPatientBtn = document.getElementById('viewPatientBtn');
    if (viewPatientBtn) {
        viewPatientBtn.addEventListener('click', function() {
            const patientId = this.getAttribute('data-patient-id');
            if (patientId) {
                window.location.href = `/patient/${patientId}`;
            }
        });
    }
}

/**
 * Handle status update for an appointment
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
 * Initialize search functionality
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
 * Show a toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    
    bsToast.show();
    
    // Remove the toast from DOM after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Debounce function to limit the rate at which a function can fire
 */
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

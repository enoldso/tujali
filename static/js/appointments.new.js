/**
 * Appointments.js
 * JavaScript for the Tujali Telehealth appointments functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Status update handling
    const statusUpdateModal = document.getElementById('statusUpdateModal');
    const statusUpdateBtns = document.querySelectorAll('.status-option');
    let currentAppointmentId = null;
    let newStatus = null;

    // Initialize all components
    initializeComponents();

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
                const modal = new bootstrap.Modal(statusUpdateModal);
                modal.show();
            }
        });
    });
    
    // Handle confirm status update
    const confirmUpdateBtn = document.getElementById('confirmStatusUpdate');
    if (confirmUpdateBtn) {
        confirmUpdateBtn.addEventListener('click', handleStatusUpdate);
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
                const statusBtn = document.querySelector(`.status-btn[data-appointment-id="${currentAppointmentId}"]`);
                if (statusBtn) {
                    // Update button text and classes
                    const statusBadge = statusBtn.querySelector('.status-badge');
                    if (statusBadge) {
                        statusBadge.className = `status-badge status-${newStatus}`;
                        statusBadge.textContent = data.appointment.status_display;
                    }
                    
                    // Update data attribute
                    statusBtn.dataset.currentStatus = newStatus;
                    
                    // Show success message
                    showToast('Appointment updated successfully', 'success');
                }
                
                // Refresh calendar if it exists
                if (window.calendar) {
                    window.calendar.refetchEvents();
                }
            } else {
                showToast(data.message || 'Failed to update appointment', 'error');
            }
        } catch (error) {
            console.error('Error updating appointment:', error);
            showToast('An error occurred. Please try again.', 'error');
        } finally {
            // Hide modal
            const modal = bootstrap.Modal.getInstance(statusUpdateModal);
            if (modal) modal.hide();
            
            // Reset button state
            if (confirmBtn) {
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = originalText;
            }
        }
    }
    
    /**
     * Initializes the search functionality
     * @param {HTMLElement} searchInput - The search input element
     */
    function initializeSearch(searchInput) {
        if (!searchInput) return;
        
        const appointmentTables = document.querySelectorAll('.appointment-table');
        
        searchInput.addEventListener('keyup', debounce(function() {
            const searchTerm = searchInput.value.trim().toLowerCase();
            
            // Don't search for very short terms (unless it's a clear action)
            if (searchTerm.length < 2 && searchTerm !== '') {
                return;
            }
            
            appointmentTables.forEach(table => {
                const rows = table.querySelectorAll('tbody tr:not(.no-results)');
                let hasMatches = false;
                
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    const isMatch = text.includes(searchTerm);
                    
                    if (isMatch) {
                        row.style.display = '';
                        hasMatches = true;
                    } else {
                        row.style.display = 'none';
                    }
                });
                
                // Show/hide no results message
                const noResultsRow = table.querySelector('tr.no-results');
                if (noResultsRow) {
                    noResultsRow.style.display = hasMatches || searchTerm === '' ? 'none' : '';
                }
            });
        }, 300));
    }
    
    /**
     * Initializes the FullCalendar
     * @param {HTMLElement} element - The calendar container element
     */
    function initializeCalendar(element) {
        if (!element || typeof FullCalendar === 'undefined') return;
        
        window.calendar = new FullCalendar.Calendar(element, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: {
                url: '/api/appointments/calendar',
                method: 'GET',
                failure: function() {
                    showToast('Failed to load calendar events', 'error');
                }
            },
            eventTimeFormat: {
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
            },
            eventDidMount: function(info) {
                // Add custom styling based on status
                const status = info.event.extendedProps.status || 'pending';
                info.el.classList.add(`event-status-${status}`);
                
                // Add tooltip
                if (info.el && info.event) {
                    new bootstrap.Tooltip(info.el, {
                        title: info.event.extendedProps.notes || 'No notes',
                        placement: 'top',
                        trigger: 'hover',
                        container: 'body'
                    });
                }
            },
            eventClick: function(info) {
                // Handle event click
                const event = info.event;
                showToast(`Clicked on: ${event.title}`, 'info');
            },
            loading: function(isLoading) {
                // Show/hide loading indicator
                const loadingEl = document.getElementById('calendar-loading');
                if (loadingEl) {
                    loadingEl.style.display = isLoading ? 'block' : 'none';
                }
            }
        });
        
        // Render the calendar
        window.calendar.render();
    }
    
    /**
     * Shows a toast notification
     * @param {string} message - The message to display
     * @param {string} type - The type of toast (success, error, info)
     */
    function showToast(message, type = 'info') {
        const toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.role = 'alert';
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        const toastBody = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toast.innerHTML = toastBody;
        toastContainer.appendChild(toast);
        document.body.appendChild(toastContainer);
        
        // Initialize and show toast
        const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 3000 });
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toastContainer.remove();
        });
    }
    
    /**
     * Debounce function to limit the rate at which a function can fire
     * @param {Function} func - The function to debounce
     * @param {number} wait - The time to wait in milliseconds
     * @returns {Function} The debounced function
     */
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }
    
    /**
     * Initializes all components
     */
    function initializeComponents() {
        // Initialize all feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        
        // Initialize FullCalendar if available
        const calendarEl = document.getElementById('calendar');
        if (calendarEl && typeof FullCalendar !== 'undefined') {
            initializeCalendar(calendarEl);
        }
        
        // Initialize search functionality
        const searchInput = document.getElementById('appointmentSearch');
        if (searchInput) {
            initializeSearch(searchInput);
        }
        
        // Initialize tooltips
        initTooltips();
    }
    
    /**
     * Initializes Bootstrap tooltips
     */
    function initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    /**
     * Formats a date string
     * @param {string|Date} date - The date to format
     * @param {string} locale - The locale to use for formatting
     * @returns {string} Formatted date string
     */
    function formatDate(date, locale = 'en-US') {
        if (!date) return '';
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            weekday: 'short'
        };
        return new Date(date).toLocaleDateString(locale, options);
    }
    
    /**
     * Formats a time string
     * @param {string} time - The time to format
     * @param {string} locale - The locale to use for formatting
     * @returns {string} Formatted time string
     */
    function formatTime(time, locale = 'en-US') {
        if (!time) return '';
        const options = {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        };
        return new Date(`2000-01-01T${time}`).toLocaleTimeString(locale, options);
    }
    
    // Expose public functions
    return {
        formatDate,
        formatTime,
        refreshCalendar: function() {
            if (window.calendar) {
                window.calendar.refetchEvents();
            }
        }
    };
});

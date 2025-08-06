/**
 * Appointments.js
 * JavaScript for the Tujali Telehealth appointments functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all feather icons
    feather.replace();
    
    // Show loading animation when page loads
    if (window.culturalLoader) {
        const loadingMotif = window.culturalLoader.showSpecific('sankofa', 'Loading appointments...');
        
        // Hide loader after 1 second to demonstrate the animation
        setTimeout(() => {
            window.culturalLoader.hide();
        }, 1000);
    }
    
    // Appointment search functionality
    const searchInput = document.getElementById('appointmentSearch');
    const appointmentTables = document.querySelectorAll('.appointment-table');
    
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = searchInput.value.toLowerCase();
            
            appointmentTables.forEach(table => {
                const rows = table.querySelectorAll('tbody tr');
                
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            });
        });
    }
    
    // Simple appointment calendar implementation
    const calendarEl = document.getElementById('appointmentCalendar');
    
    if (calendarEl) {
        renderCalendar(calendarEl);
    }
    
    function renderCalendar(element) {
        // Get current date information
        const date = new Date();
        const currentMonth = date.getMonth();
        const currentYear = date.getFullYear();
        
        // Create calendar header
        const calendarHeader = document.createElement('div');
        calendarHeader.className = 'calendar-header d-flex justify-content-between align-items-center mb-3';
        
        const monthYearLabel = document.createElement('h5');
        monthYearLabel.textContent = new Date(currentYear, currentMonth).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        
        const navButtons = document.createElement('div');
        navButtons.className = 'btn-group';
        
        const prevBtn = document.createElement('button');
        prevBtn.className = 'btn btn-sm btn-outline-secondary';
        prevBtn.innerHTML = '<i data-feather="chevron-left"></i>';
        
        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn btn-sm btn-outline-secondary';
        nextBtn.innerHTML = '<i data-feather="chevron-right"></i>';
        
        navButtons.appendChild(prevBtn);
        navButtons.appendChild(nextBtn);
        
        calendarHeader.appendChild(monthYearLabel);
        calendarHeader.appendChild(navButtons);
        
        // Create calendar grid
        const calendarGrid = document.createElement('div');
        calendarGrid.className = 'calendar-grid';
        
        // Create days of week header
        const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const weekdayRow = document.createElement('div');
        weekdayRow.className = 'calendar-weekdays d-flex';
        
        daysOfWeek.forEach(day => {
            const dayEl = document.createElement('div');
            dayEl.className = 'calendar-weekday';
            dayEl.textContent = day;
            weekdayRow.appendChild(dayEl);
        });
        
        calendarGrid.appendChild(weekdayRow);
        
        // Create date grid
        const dateGrid = document.createElement('div');
        dateGrid.className = 'calendar-dates';
        
        // Determine first day of month and total days
        const firstDay = new Date(currentYear, currentMonth, 1).getDay();
        const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
        
        // Create the date cells
        let dayCount = 1;
        
        // Create simulated appointment data
        // In a real app, this would come from your database
        const appointmentDates = {
            // Format: 'YYYY-MM-DD': { count: X, status: 'pending|confirmed|cancelled' }
        };
        
        // Generate some sample appointment data for current month
        for (let i = 1; i <= daysInMonth; i++) {
            if (i % 3 === 0) {
                const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
                const randomCount = Math.floor(Math.random() * 3) + 1;
                const statuses = ['pending', 'confirmed', 'cancelled', 'completed'];
                const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
                
                appointmentDates[dateStr] = {
                    count: randomCount,
                    status: randomStatus
                };
            }
        }
        
        // Create rows for the calendar
        for (let i = 0; i < 6; i++) {
            const row = document.createElement('div');
            row.className = 'calendar-row d-flex';
            
            for (let j = 0; j < 7; j++) {
                const dateCell = document.createElement('div');
                dateCell.className = 'calendar-date';
                
                if (i === 0 && j < firstDay) {
                    // Empty cells before the first day of month
                    dateCell.className += ' empty';
                } else if (dayCount <= daysInMonth) {
                    // Valid date cells
                    dateCell.textContent = dayCount;
                    
                    // Check if current date
                    if (dayCount === date.getDate() && currentMonth === date.getMonth() && currentYear === date.getFullYear()) {
                        dateCell.className += ' current';
                    }
                    
                    // Check if this date has appointments
                    const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(dayCount).padStart(2, '0')}`;
                    if (appointmentDates[dateStr]) {
                        const appointmentInfo = document.createElement('div');
                        appointmentInfo.className = `appointment-indicator ${appointmentDates[dateStr].status}`;
                        appointmentInfo.textContent = appointmentDates[dateStr].count;
                        dateCell.appendChild(appointmentInfo);
                    }
                    
                    dayCount++;
                } else {
                    // Empty cells after the last day of month
                    dateCell.className += ' empty';
                }
                
                row.appendChild(dateCell);
            }
            
            dateGrid.appendChild(row);
            
            // Stop if we've rendered all days
            if (dayCount > daysInMonth) {
                break;
            }
        }
        
        calendarGrid.appendChild(dateGrid);
        
        // Add everything to the calendar element
        element.appendChild(calendarHeader);
        element.appendChild(calendarGrid);
        
        // Initialize feather icons
        feather.replace();
        
        // Add event listeners for navigation buttons
        prevBtn.addEventListener('click', function() {
            // Show loading animation
            if (window.culturalLoader) {
                window.culturalLoader.showSpecific('sankofa', 'Loading previous month...');
                
                // In a real app, this would navigate to the previous month
                setTimeout(() => {
                    window.culturalLoader.hide();
                    alert('Navigate to previous month - This would be implemented in a production app');
                }, 1000);
            } else {
                alert('Navigate to previous month - This would be implemented in a production app');
            }
        });
        
        nextBtn.addEventListener('click', function() {
            // Show loading animation
            if (window.culturalLoader) {
                window.culturalLoader.showSpecific('sankofa', 'Loading next month...');
                
                // In a real app, this would navigate to the next month
                setTimeout(() => {
                    window.culturalLoader.hide();
                    alert('Navigate to next month - This would be implemented in a production app');
                }, 1000);
            } else {
                alert('Navigate to next month - This would be implemented in a production app');
            }
        });
    }
    
    // Form validation for appointment updates
    const appointmentForms = document.querySelectorAll('form[action*="update_appointment"]');
    
    appointmentForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Add confirmation dialog for appointment status changes
            const status = form.querySelector('input[name="status"]').value;
            
            if (!confirm(`Are you sure you want to mark this appointment as ${status}?`)) {
                return false;
            }
            
            // Show cultural loading animation when form is submitted
            if (window.culturalLoader) {
                let statusText = 'Updating appointment...';
                let motif = 'sankofa';
                
                // Customize message and motif based on status
                if (status === 'confirmed') {
                    statusText = 'Confirming appointment...';
                    motif = 'kente';
                } else if (status === 'cancelled') {
                    statusText = 'Cancelling appointment...';
                    motif = 'ndebele';
                } else if (status === 'completed') {
                    statusText = 'Marking appointment as completed...';
                    motif = 'maasai';
                }
                
                window.culturalLoader.showSpecific(motif, statusText);
                
                // Submit the form after a short delay to show the animation
                setTimeout(() => {
                    form.submit();
                }, 1000);
            } else {
                // If cultural loader is not available, submit form immediately
                form.submit();
            }
        });
    });
    
    // Auto-refresh appointments every 5 minutes
    function refreshAppointmentData() {
        // Show loading animation while refreshing
        if (window.culturalLoader) {
            window.culturalLoader.showSpecific('maasai', 'Refreshing appointment data...');
            
            // In a real application, this would fetch updated data via AJAX
            // Simulate data fetching with a timeout
            setTimeout(() => {
                console.log("Appointments data refreshed at " + new Date().toLocaleTimeString());
                window.culturalLoader.hide();
            }, 1000);
        } else {
            console.log("Appointments data refreshed at " + new Date().toLocaleTimeString());
        }
    }
    
    // Set up periodic refresh
    setInterval(refreshAppointmentData, 300000); // 5 minutes
});

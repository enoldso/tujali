/**
 * Dashboard.js
 * JavaScript for the Tujali Telehealth dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all feather icons
    feather.replace();
    
    // Show loading animation when page loads
    if (window.culturalLoader) {
        const loadingMotif = window.culturalLoader.show('Initializing dashboard...');
        
        // Hide loader after 1 second to demonstrate the animation
        setTimeout(() => {
            window.culturalLoader.hide();
        }, 1000);
    }
    
    // Patient Activity Chart
    const activityChartElement = document.getElementById('activityChart');
    
    if (activityChartElement) {
        // Get current year and month
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth(); // 0-indexed (0 = January)
        
        // Generate labels for the last 6 months
        const monthLabels = [];
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        
        for (let i = 5; i >= 0; i--) {
            let month = currentMonth - i;
            let year = currentYear;
            
            if (month < 0) {
                month += 12;
                year -= 1;
            }
            
            monthLabels.push(`${monthNames[month]} ${year}`);
        }
        
        // Enhanced dataset with more realistic distribution patterns
        const patientData = [8, 15, 22, 30, 38, 45];  // Growth trend
        const consultationData = [12, 25, 30, 42, 60, 78]; // Accelerating growth
        const messageData = [24, 36, 45, 62, 85, 110]; // Steeper growth
        const symptomReportData = [15, 28, 40, 38, 50, 65]; // Variable growth
        const ussdSessionData = [40, 65, 82, 110, 145, 190]; // Rapid adoption
        
        // Create the chart
        const activityChart = new Chart(activityChartElement, {
            type: 'line',
            data: {
                labels: monthLabels,
                datasets: [
                    {
                        label: 'New Patients',
                        data: patientData,
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Consultations',
                        data: consultationData,
                        borderColor: '#fd7e14',
                        backgroundColor: 'rgba(253, 126, 20, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Messages',
                        data: messageData,
                        borderColor: '#20c997',
                        backgroundColor: 'rgba(32, 201, 151, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Symptom Reports',
                        data: symptomReportData,
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'USSD Sessions',
                        data: ussdSessionData,
                        borderColor: '#6f42c1',
                        backgroundColor: 'rgba(111, 66, 193, 0.1)',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    },
                    title: {
                        display: true,
                        text: 'Platform Activity Trends (Last 6 Months)'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        },
                        title: {
                            display: true,
                            text: 'Number of Interactions'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Month'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }
    
    // Add symptom distribution donut chart if element exists
    const symptomDistributionElement = document.getElementById('symptomDistributionChart');
    if (symptomDistributionElement) {
        new Chart(symptomDistributionElement, {
            type: 'doughnut',
            data: {
                labels: ['Respiratory', 'Digestive', 'Pain', 'Fever', 'Skin', 'Other'],
                datasets: [{
                    data: [35, 22, 18, 15, 10, 5],
                    backgroundColor: [
                        '#0d6efd', // Blue - Respiratory
                        '#fd7e14', // Orange - Digestive
                        '#dc3545', // Red - Pain
                        '#ffc107', // Yellow - Fever
                        '#20c997', // Green - Skin
                        '#6c757d'  // Grey - Other
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                    },
                    title: {
                        display: true,
                        text: 'Reported Symptoms by Category'
                    }
                }
            }
        });
    }
    
    // User Activity by Region bar chart
    const regionActivityElement = document.getElementById('regionActivityChart');
    if (regionActivityElement) {
        new Chart(regionActivityElement, {
            type: 'bar',
            data: {
                labels: ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Rural Areas'],
                datasets: [{
                    label: 'Patient Registrations',
                    data: [120, 85, 65, 45, 40, 210],
                    backgroundColor: 'rgba(13, 110, 253, 0.7)',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: {
                    legend: {
                        display: false,
                    },
                    title: {
                        display: true,
                        text: 'Patient Distribution by Region'
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Patients'
                        }
                    }
                }
            }
        });
    }
    
    // Auto-refresh dashboard data every 2 minutes
    function refreshDashboardData() {
        // Show loading animation while refreshing
        if (window.culturalLoader) {
            window.culturalLoader.showSpecific('maasai', 'Refreshing dashboard data...');
            
            // In a real application, this would fetch updated data via AJAX
            // Simulate data fetching with a timeout
            setTimeout(() => {
                console.log("Dashboard data refreshed at " + new Date().toLocaleTimeString());
                window.culturalLoader.hide();
            }, 1000);
        } else {
            console.log("Dashboard data refreshed at " + new Date().toLocaleTimeString());
        }
    }
    
    // Initial data refresh
    refreshDashboardData();
    
    // Set up periodic refresh
    setInterval(refreshDashboardData, 120000); // 2 minutes
    
    // Responsive behavior for small screens
    function handleResponsiveLayout() {
        const width = window.innerWidth;
        
        // Adjust chart options for smaller screens
        if (width < 768 && activityChartElement) {
            // Simplify the chart for mobile devices
            activityChart.options.scales.y.ticks.display = false;
            activityChart.options.plugins.legend.display = false;
            activityChart.update();
        } else if (activityChartElement) {
            // Restore chart options for larger screens
            activityChart.options.scales.y.ticks.display = true;
            activityChart.options.plugins.legend.display = true;
            activityChart.update();
        }
    }
    
    // Initial call and window resize listener
    handleResponsiveLayout();
    window.addEventListener('resize', handleResponsiveLayout);
    
    // Add loading animations to patient detail, appointment, and message links
    document.querySelectorAll('a[href*="patient_detail"]').forEach(link => {
        link.setAttribute('data-ajax', 'true');
        link.setAttribute('data-loading-message', 'Loading patient details...');
        link.setAttribute('data-loading-motif', 'kente');
    });
    
    document.querySelectorAll('a[href*="appointment"]').forEach(link => {
        link.setAttribute('data-ajax', 'true');
        link.setAttribute('data-loading-message', 'Loading appointments...');
        link.setAttribute('data-loading-motif', 'sankofa');
    });
    
    document.querySelectorAll('a[href*="messages"]').forEach(link => {
        link.setAttribute('data-ajax', 'true');
        link.setAttribute('data-loading-message', 'Loading messages...');
        link.setAttribute('data-loading-motif', 'ndebele');
    });
});

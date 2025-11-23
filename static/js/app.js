/**
 * Apex Analysis - Shared JavaScript Utilities
 */

// Utility Functions
const ApexUtils = {
    /**
     * Format number as currency
     */
    formatCurrency(value, decimals = 2) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    },

    /**
     * Format number as percentage
     */
    formatPercent(value, decimals = 2) {
        return `${(value * 100).toFixed(decimals)}%`;
    },

    /**
     * Format large numbers with K, M, B suffixes
     */
    formatLargeNumber(value) {
        if (value >= 1e9) {
            return `${(value / 1e9).toFixed(2)}B`;
        } else if (value >= 1e6) {
            return `${(value / 1e6).toFixed(2)}M`;
        } else if (value >= 1e3) {
            return `${(value / 1e3).toFixed(2)}K`;
        }
        return value.toFixed(2);
    },

    /**
     * Format date
     */
    formatDate(date, format = 'short') {
        const d = new Date(date);
        if (format === 'short') {
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        }
        return d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    },

    /**
     * Show loading spinner
     */
    showLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.remove('hidden');
        }
    },

    /**
     * Hide loading spinner
     */
    hideLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add('hidden');
        }
    },

    /**
     * Show error message
     */
    showError(message, title = 'Error') {
        alert(`${title}: ${message}`);
    },

    /**
     * Validate ticker symbol
     */
    isValidTicker(ticker) {
        // Basic validation: 1-5 uppercase letters
        return /^[A-Z]{1,5}$/.test(ticker);
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Get color based on value (positive/negative)
     */
    getValueColor(value, darkMode = false) {
        if (value > 0) {
            return darkMode ? '#10b981' : '#059669';
        } else if (value < 0) {
            return darkMode ? '#ef4444' : '#dc2626';
        }
        return darkMode ? '#9ca3af' : '#6b7280';
    },

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('Failed to copy:', err);
            return false;
        }
    },

    /**
     * Download data as JSON
     */
    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    },

    /**
     * Download data as CSV
     */
    downloadCSV(data, filename, headers = null) {
        let csv = '';

        if (headers) {
            csv = headers.join(',') + '\n';
        } else if (data.length > 0) {
            csv = Object.keys(data[0]).join(',') + '\n';
        }

        data.forEach(row => {
            const values = Object.values(row).map(val => {
                // Escape commas and quotes
                if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
                    return `"${val.replace(/"/g, '""')}"`;
                }
                return val;
            });
            csv += values.join(',') + '\n';
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }
};

// Chart Utilities
const ApexCharts = {
    /**
     * Get default Plotly layout
     */
    getDefaultLayout(title = '', darkMode = false) {
        return {
            title: title,
            template: 'plotly_white',
            paper_bgcolor: darkMode ? '#1f2937' : '#ffffff',
            plot_bgcolor: darkMode ? '#111827' : '#f9fafb',
            font: {
                color: darkMode ? '#f9fafb' : '#111827'
            },
            xaxis: {
                gridcolor: darkMode ? '#374151' : '#e5e7eb',
                zerolinecolor: darkMode ? '#4b5563' : '#d1d5db'
            },
            yaxis: {
                gridcolor: darkMode ? '#374151' : '#e5e7eb',
                zerolinecolor: darkMode ? '#4b5563' : '#d1d5db'
            },
            hovermode: 'x unified',
            responsive: true
        };
    },

    /**
     * Get default Plotly config
     */
    getDefaultConfig() {
        return {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
            toImageButtonOptions: {
                format: 'png',
                filename: 'apex_chart',
                height: 800,
                width: 1200,
                scale: 2
            }
        };
    },

    /**
     * Update chart theme
     */
    updateChartTheme(chartId, darkMode) {
        const layout = {
            paper_bgcolor: darkMode ? '#1f2937' : '#ffffff',
            plot_bgcolor: darkMode ? '#111827' : '#f9fafb',
            font: {
                color: darkMode ? '#f9fafb' : '#111827'
            },
            xaxis: {
                gridcolor: darkMode ? '#374151' : '#e5e7eb'
            },
            yaxis: {
                gridcolor: darkMode ? '#374151' : '#e5e7eb'
            }
        };
        Plotly.relayout(chartId, layout);
    }
};

// API Client
const ApexAPI = {
    /**
     * Generic API call wrapper
     */
    async call(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'API request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * Analyze stock
     */
    async analyzeStock(ticker, period = '1y') {
        return this.call('/api/analyze', {
            method: 'POST',
            body: JSON.stringify({ ticker, period })
        });
    },

    /**
     * Get chart data
     */
    async getChart(ticker, period = '1y', type = 'candlestick') {
        return this.call(`/api/chart/${ticker}?period=${period}&type=${type}`);
    },

    /**
     * Run backtest
     */
    async runBacktest(ticker, period = '1y', initialCapital = 100000) {
        return this.call('/api/backtest', {
            method: 'POST',
            body: JSON.stringify({
                ticker,
                period,
                initial_capital: initialCapital
            })
        });
    },

    /**
     * Get risk metrics
     */
    async getRiskMetrics(ticker, period = '1y') {
        return this.call(`/api/risk/${ticker}?period=${period}`);
    }
};

// Theme Management
const ThemeManager = {
    /**
     * Get current theme
     */
    getTheme() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    },

    /**
     * Check if dark mode
     */
    isDarkMode() {
        return this.getTheme() === 'dark';
    },

    /**
     * Listen for theme changes
     */
    onChange(callback) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
                    callback(this.getTheme());
                }
            });
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-theme']
        });

        return observer;
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Apex Analysis Dashboard Loaded');

    // Update chart themes when theme changes
    ThemeManager.onChange((theme) => {
        const darkMode = theme === 'dark';

        // Update all Plotly charts
        const charts = document.querySelectorAll('.js-plotly-plot');
        charts.forEach(chart => {
            if (chart.id) {
                ApexCharts.updateChartTheme(chart.id, darkMode);
            }
        });
    });

    // Add smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// Export utilities to global scope
window.ApexUtils = ApexUtils;
window.ApexCharts = ApexCharts;
window.ApexAPI = ApexAPI;
window.ThemeManager = ThemeManager;

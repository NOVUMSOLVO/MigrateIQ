/**
 * Tests for Dashboard component
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import '@testing-library/jest-dom';
import Dashboard from '../Dashboard';

// Mock the API service
jest.mock('../../services/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
}));

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart">Line Chart</div>,
  Bar: () => <div data-testid="bar-chart">Bar Chart</div>,
  Doughnut: () => <div data-testid="doughnut-chart">Doughnut Chart</div>,
}));

const theme = createTheme();

const renderWithProviders = (component) => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
  });

  test('renders dashboard title', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText('MigrateIQ Dashboard')).toBeInTheDocument();
  });

  test('displays loading state initially', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });

  test('renders statistics cards', async () => {
    const mockStats = {
      totalProjects: 15,
      activeProjects: 8,
      completedProjects: 7,
      totalDataSources: 25,
      migratedRecords: 1500000,
      successRate: 98.5
    };

    const api = require('../../services/api');
    api.get.mockResolvedValueOnce({ data: mockStats });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Total Projects')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
      expect(screen.getByText('Active Projects')).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument();
      expect(screen.getByText('Completed Projects')).toBeInTheDocument();
      expect(screen.getByText('7')).toBeInTheDocument();
    });
  });

  test('renders recent projects section', async () => {
    const mockProjects = [
      {
        id: 1,
        name: 'Customer Data Migration',
        status: 'IN_PROGRESS',
        progress: 65,
        created_at: '2024-01-15T10:00:00Z'
      },
      {
        id: 2,
        name: 'Product Catalog Migration',
        status: 'COMPLETED',
        progress: 100,
        created_at: '2024-01-10T14:30:00Z'
      }
    ];

    const api = require('../../services/api');
    api.get.mockResolvedValueOnce({ data: { results: mockProjects } });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Recent Projects')).toBeInTheDocument();
      expect(screen.getByText('Customer Data Migration')).toBeInTheDocument();
      expect(screen.getByText('Product Catalog Migration')).toBeInTheDocument();
    });
  });

  test('renders migration progress chart', async () => {
    const mockChartData = {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
      datasets: [{
        label: 'Migrations Completed',
        data: [2, 5, 3, 8, 6],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
      }]
    };

    const api = require('../../services/api');
    api.get.mockResolvedValueOnce({ data: mockChartData });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Migration Progress')).toBeInTheDocument();
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  test('renders data quality metrics', async () => {
    const mockQualityData = {
      overall_score: 92.5,
      completeness: 95.2,
      accuracy: 89.8,
      consistency: 93.1,
      validity: 91.7
    };

    const api = require('../../services/api');
    api.get.mockResolvedValueOnce({ data: mockQualityData });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Data Quality Metrics')).toBeInTheDocument();
      expect(screen.getByText('92.5%')).toBeInTheDocument();
      expect(screen.getByText('Completeness: 95.2%')).toBeInTheDocument();
    });
  });

  test('handles API error gracefully', async () => {
    const api = require('../../services/api');
    api.get.mockRejectedValueOnce(new Error('API Error'));

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Error loading dashboard data')).toBeInTheDocument();
    });
  });

  test('refreshes data when refresh button is clicked', async () => {
    const api = require('../../services/api');
    api.get.mockResolvedValue({ data: {} });

    renderWithProviders(<Dashboard />);

    const refreshButton = screen.getByLabelText('refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(2); // Initial load + refresh
    });
  });

  test('navigates to projects page when view all projects is clicked', () => {
    const mockNavigate = jest.fn();
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate,
    }));

    renderWithProviders(<Dashboard />);

    const viewAllButton = screen.getByText('View All Projects');
    fireEvent.click(viewAllButton);

    expect(mockNavigate).toHaveBeenCalledWith('/projects');
  });

  test('displays system health status', async () => {
    const mockHealthData = {
      database: 'healthy',
      redis: 'healthy',
      celery: 'warning',
      storage: 'healthy'
    };

    const api = require('../../services/api');
    api.get.mockResolvedValueOnce({ data: mockHealthData });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('System Health')).toBeInTheDocument();
      expect(screen.getByText('Database: Healthy')).toBeInTheDocument();
      expect(screen.getByText('Celery: Warning')).toBeInTheDocument();
    });
  });

  test('renders responsive layout on mobile', () => {
    // Mock window.innerWidth
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    renderWithProviders(<Dashboard />);

    const container = screen.getByTestId('dashboard-container');
    expect(container).toHaveClass('mobile-layout');
  });

  test('updates data in real-time', async () => {
    const api = require('../../services/api');
    
    // Initial data
    api.get.mockResolvedValueOnce({ 
      data: { totalProjects: 10 } 
    });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument();
    });

    // Simulate real-time update
    api.get.mockResolvedValueOnce({ 
      data: { totalProjects: 11 } 
    });

    // Trigger update (this would normally come from WebSocket)
    fireEvent(window, new CustomEvent('dashboard-update'));

    await waitFor(() => {
      expect(screen.getByText('11')).toBeInTheDocument();
    });
  });

  test('filters data by date range', async () => {
    const api = require('../../services/api');
    api.get.mockResolvedValue({ data: {} });

    renderWithProviders(<Dashboard />);

    const dateFilter = screen.getByLabelText('Date Range');
    fireEvent.change(dateFilter, { target: { value: 'last-30-days' } });

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining('date_range=last-30-days')
      );
    });
  });

  test('exports dashboard data', async () => {
    const mockBlob = new Blob(['test data'], { type: 'text/csv' });
    global.URL.createObjectURL = jest.fn(() => 'blob:test-url');
    global.URL.revokeObjectURL = jest.fn();

    const api = require('../../services/api');
    api.get.mockResolvedValueOnce({ data: mockBlob });

    renderWithProviders(<Dashboard />);

    const exportButton = screen.getByText('Export Data');
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/api/dashboard/export/');
      expect(global.URL.createObjectURL).toHaveBeenCalledWith(mockBlob);
    });
  });

  test('displays notifications', async () => {
    const mockNotifications = [
      {
        id: 1,
        message: 'Migration completed successfully',
        type: 'success',
        timestamp: '2024-01-15T10:00:00Z'
      },
      {
        id: 2,
        message: 'Data validation warning',
        type: 'warning',
        timestamp: '2024-01-15T09:30:00Z'
      }
    ];

    const api = require('../../services/api');
    api.get.mockResolvedValueOnce({ data: mockNotifications });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText('Migration completed successfully')).toBeInTheDocument();
      expect(screen.getByText('Data validation warning')).toBeInTheDocument();
    });
  });

  test('handles empty state', async () => {
    const api = require('../../services/api');
    api.get.mockResolvedValue({ 
      data: { 
        totalProjects: 0,
        results: []
      } 
    });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('No projects found')).toBeInTheDocument();
      expect(screen.getByText('Get started by creating your first migration project')).toBeInTheDocument();
    });
  });

  test('displays keyboard shortcuts help', () => {
    renderWithProviders(<Dashboard />);

    // Press '?' key to show shortcuts
    fireEvent.keyDown(document, { key: '?', code: 'Slash' });

    expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
    expect(screen.getByText('R - Refresh dashboard')).toBeInTheDocument();
    expect(screen.getByText('N - New project')).toBeInTheDocument();
  });
});

/**
 * Tests for DataSourceForm component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import '@testing-library/jest-dom';
import DataSourceForm from '../DataSourceForm';

// Mock the API service
jest.mock('../../services/api', () => ({
  post: jest.fn(),
  put: jest.fn(),
  get: jest.fn(),
}));

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ id: null }),
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

describe('DataSourceForm Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders form title for new data source', () => {
    renderWithProviders(<DataSourceForm />);
    expect(screen.getByText('Add New Data Source')).toBeInTheDocument();
  });

  test('renders all required form fields', () => {
    renderWithProviders(<DataSourceForm />);
    
    expect(screen.getByLabelText('Data Source Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Source Type')).toBeInTheDocument();
    expect(screen.getByLabelText('Connection String')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
  });

  test('displays source type options', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DataSourceForm />);
    
    const sourceTypeSelect = screen.getByLabelText('Source Type');
    await user.click(sourceTypeSelect);
    
    expect(screen.getByText('PostgreSQL')).toBeInTheDocument();
    expect(screen.getByText('MySQL')).toBeInTheDocument();
    expect(screen.getByText('SQL Server')).toBeInTheDocument();
    expect(screen.getByText('Oracle')).toBeInTheDocument();
    expect(screen.getByText('MongoDB')).toBeInTheDocument();
    expect(screen.getByText('CSV File')).toBeInTheDocument();
  });

  test('validates required fields', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DataSourceForm />);
    
    const submitButton = screen.getByText('Create Data Source');
    await user.click(submitButton);
    
    expect(screen.getByText('Name is required')).toBeInTheDocument();
    expect(screen.getByText('Source type is required')).toBeInTheDocument();
  });

  test('validates connection string format for PostgreSQL', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DataSourceForm />);
    
    const nameField = screen.getByLabelText('Data Source Name');
    const sourceTypeSelect = screen.getByLabelText('Source Type');
    const connectionField = screen.getByLabelText('Connection String');
    
    await user.type(nameField, 'Test Database');
    await user.click(sourceTypeSelect);
    await user.click(screen.getByText('PostgreSQL'));
    await user.type(connectionField, 'invalid-connection-string');
    
    const submitButton = screen.getByText('Create Data Source');
    await user.click(submitButton);
    
    expect(screen.getByText('Invalid PostgreSQL connection string format')).toBeInTheDocument();
  });

  test('shows connection string helper text based on source type', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DataSourceForm />);
    
    const sourceTypeSelect = screen.getByLabelText('Source Type');
    
    // Test PostgreSQL helper text
    await user.click(sourceTypeSelect);
    await user.click(screen.getByText('PostgreSQL'));
    
    expect(screen.getByText('Format: postgresql://username:password@host:port/database')).toBeInTheDocument();
    
    // Test MySQL helper text
    await user.click(sourceTypeSelect);
    await user.click(screen.getByText('MySQL'));
    
    expect(screen.getByText('Format: mysql://username:password@host:port/database')).toBeInTheDocument();
  });

  test('submits form with valid data', async () => {
    const user = userEvent.setup();
    const api = require('../../services/api');
    api.post.mockResolvedValueOnce({ 
      data: { 
        id: 1, 
        name: 'Test Database',
        source_type: 'postgresql'
      } 
    });
    
    renderWithProviders(<DataSourceForm />);
    
    const nameField = screen.getByLabelText('Data Source Name');
    const sourceTypeSelect = screen.getByLabelText('Source Type');
    const connectionField = screen.getByLabelText('Connection String');
    const descriptionField = screen.getByLabelText('Description');
    
    await user.type(nameField, 'Test Database');
    await user.click(sourceTypeSelect);
    await user.click(screen.getByText('PostgreSQL'));
    await user.type(connectionField, 'postgresql://user:pass@localhost:5432/testdb');
    await user.type(descriptionField, 'Test database description');
    
    const submitButton = screen.getByText('Create Data Source');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/analyzer/data-sources/', {
        name: 'Test Database',
        source_type: 'postgresql',
        connection_string: 'postgresql://user:pass@localhost:5432/testdb',
        description: 'Test database description'
      });
    });
    
    expect(mockNavigate).toHaveBeenCalledWith('/data-sources');
  });

  test('tests database connection', async () => {
    const user = userEvent.setup();
    const api = require('../../services/api');
    api.post.mockResolvedValueOnce({ 
      data: { 
        success: true, 
        message: 'Connection successful' 
      } 
    });
    
    renderWithProviders(<DataSourceForm />);
    
    const nameField = screen.getByLabelText('Data Source Name');
    const sourceTypeSelect = screen.getByLabelText('Source Type');
    const connectionField = screen.getByLabelText('Connection String');
    
    await user.type(nameField, 'Test Database');
    await user.click(sourceTypeSelect);
    await user.click(screen.getByText('PostgreSQL'));
    await user.type(connectionField, 'postgresql://user:pass@localhost:5432/testdb');
    
    const testButton = screen.getByText('Test Connection');
    await user.click(testButton);
    
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/analyzer/test-connection/', {
        source_type: 'postgresql',
        connection_string: 'postgresql://user:pass@localhost:5432/testdb'
      });
    });
    
    expect(screen.getByText('Connection successful')).toBeInTheDocument();
  });

  test('handles connection test failure', async () => {
    const user = userEvent.setup();
    const api = require('../../services/api');
    api.post.mockRejectedValueOnce({ 
      response: { 
        data: { 
          error: 'Connection failed: Invalid credentials' 
        } 
      } 
    });
    
    renderWithProviders(<DataSourceForm />);
    
    const nameField = screen.getByLabelText('Data Source Name');
    const sourceTypeSelect = screen.getByLabelText('Source Type');
    const connectionField = screen.getByLabelText('Connection String');
    
    await user.type(nameField, 'Test Database');
    await user.click(sourceTypeSelect);
    await user.click(screen.getByText('PostgreSQL'));
    await user.type(connectionField, 'postgresql://user:wrongpass@localhost:5432/testdb');
    
    const testButton = screen.getByText('Test Connection');
    await user.click(testButton);
    
    await waitFor(() => {
      expect(screen.getByText('Connection failed: Invalid credentials')).toBeInTheDocument();
    });
  });

  test('shows loading state during form submission', async () => {
    const user = userEvent.setup();
    const api = require('../../services/api');
    
    // Mock a delayed response
    api.post.mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve({ data: {} }), 1000))
    );
    
    renderWithProviders(<DataSourceForm />);
    
    const nameField = screen.getByLabelText('Data Source Name');
    const sourceTypeSelect = screen.getByLabelText('Source Type');
    const connectionField = screen.getByLabelText('Connection String');
    
    await user.type(nameField, 'Test Database');
    await user.click(sourceTypeSelect);
    await user.click(screen.getByText('PostgreSQL'));
    await user.type(connectionField, 'postgresql://user:pass@localhost:5432/testdb');
    
    const submitButton = screen.getByText('Create Data Source');
    await user.click(submitButton);
    
    expect(screen.getByText('Creating...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  test('handles form submission error', async () => {
    const user = userEvent.setup();
    const api = require('../../services/api');
    api.post.mockRejectedValueOnce({ 
      response: { 
        data: { 
          name: ['Data source with this name already exists.'] 
        } 
      } 
    });
    
    renderWithProviders(<DataSourceForm />);
    
    const nameField = screen.getByLabelText('Data Source Name');
    const sourceTypeSelect = screen.getByLabelText('Source Type');
    const connectionField = screen.getByLabelText('Connection String');
    
    await user.type(nameField, 'Existing Database');
    await user.click(sourceTypeSelect);
    await user.click(screen.getByText('PostgreSQL'));
    await user.type(connectionField, 'postgresql://user:pass@localhost:5432/testdb');
    
    const submitButton = screen.getByText('Create Data Source');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Data source with this name already exists.')).toBeInTheDocument();
    });
  });

  test('cancels form and navigates back', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DataSourceForm />);
    
    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/data-sources');
  });

  test('shows advanced options when toggled', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DataSourceForm />);
    
    const advancedToggle = screen.getByText('Advanced Options');
    await user.click(advancedToggle);
    
    expect(screen.getByLabelText('Connection Timeout (seconds)')).toBeInTheDocument();
    expect(screen.getByLabelText('SSL Mode')).toBeInTheDocument();
    expect(screen.getByLabelText('Schema')).toBeInTheDocument();
  });

  test('validates SSL certificate file upload', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DataSourceForm />);
    
    // Show advanced options
    const advancedToggle = screen.getByText('Advanced Options');
    await user.click(advancedToggle);
    
    const sslModeSelect = screen.getByLabelText('SSL Mode');
    await user.click(sslModeSelect);
    await user.click(screen.getByText('Require'));
    
    expect(screen.getByLabelText('SSL Certificate')).toBeInTheDocument();
    
    const fileInput = screen.getByLabelText('SSL Certificate');
    const invalidFile = new File(['invalid content'], 'test.txt', { type: 'text/plain' });
    
    await user.upload(fileInput, invalidFile);
    
    expect(screen.getByText('Please upload a valid certificate file (.crt, .pem)')).toBeInTheDocument();
  });

  test('auto-detects connection parameters from connection string', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DataSourceForm />);
    
    const sourceTypeSelect = screen.getByLabelText('Source Type');
    const connectionField = screen.getByLabelText('Connection String');
    
    await user.click(sourceTypeSelect);
    await user.click(screen.getByText('PostgreSQL'));
    await user.type(connectionField, 'postgresql://testuser:testpass@testhost:5433/testdb');
    
    // Trigger auto-detection
    fireEvent.blur(connectionField);
    
    // Show advanced options to see auto-detected values
    const advancedToggle = screen.getByText('Advanced Options');
    await user.click(advancedToggle);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('testhost')).toBeInTheDocument();
      expect(screen.getByDisplayValue('5433')).toBeInTheDocument();
      expect(screen.getByDisplayValue('testdb')).toBeInTheDocument();
    });
  });

  test('supports file upload for CSV data sources', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DataSourceForm />);
    
    const sourceTypeSelect = screen.getByLabelText('Source Type');
    await user.click(sourceTypeSelect);
    await user.click(screen.getByText('CSV File'));
    
    // Connection string field should be hidden, file upload should appear
    expect(screen.queryByLabelText('Connection String')).not.toBeInTheDocument();
    expect(screen.getByLabelText('CSV File')).toBeInTheDocument();
    
    const fileInput = screen.getByLabelText('CSV File');
    const csvFile = new File(['col1,col2\nval1,val2'], 'test.csv', { type: 'text/csv' });
    
    await user.upload(fileInput, csvFile);
    
    expect(screen.getByText('test.csv')).toBeInTheDocument();
  });

  test('shows connection string examples', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DataSourceForm />);
    
    const examplesButton = screen.getByText('Show Examples');
    await user.click(examplesButton);
    
    expect(screen.getByText('Connection String Examples')).toBeInTheDocument();
    expect(screen.getByText('PostgreSQL:')).toBeInTheDocument();
    expect(screen.getByText('MySQL:')).toBeInTheDocument();
    expect(screen.getByText('SQL Server:')).toBeInTheDocument();
  });

  test('preserves form data when switching between tabs', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DataSourceForm />);
    
    const nameField = screen.getByLabelText('Data Source Name');
    await user.type(nameField, 'Test Database');
    
    // Switch to advanced tab
    const advancedTab = screen.getByText('Advanced');
    await user.click(advancedTab);
    
    // Switch back to basic tab
    const basicTab = screen.getByText('Basic');
    await user.click(basicTab);
    
    // Name should be preserved
    expect(nameField).toHaveValue('Test Database');
  });
});

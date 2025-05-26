import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  CircularProgress
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const DataSourceForm = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    source_type: 'csv',
    connection_string: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/analyzer/data-sources/', formData);

      // If successful, analyze the data source
      try {
        await api.post(`/analyzer/data-sources/${response.data.id}/analyze/`);
        navigate('/data-sources');
      } catch (analyzeError) {
        setError(`Data source created but analysis failed: ${analyzeError.response?.data?.error || analyzeError.message}`);
        setLoading(false);
      }
    } catch (error) {
      setError(`Error creating data source: ${error.response?.data?.error || error.message}`);
      setLoading(false);
    }
  };

  const getConnectionStringHelp = () => {
    switch (formData.source_type) {
      case 'csv':
        return 'Enter the full path to the CSV file';
      case 'database':
        return 'Enter the database connection string (e.g., postgresql://user:password@localhost:5432/dbname)';
      case 'api':
        return 'Enter the API endpoint URL';
      default:
        return '';
    }
  };

  return (
    <Paper sx={{ p: 3, maxWidth: 800, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Add New Data Source
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              required
              fullWidth
              label="Data Source Name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              disabled={loading}
            />
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth required>
              <InputLabel>Source Type</InputLabel>
              <Select
                name="source_type"
                value={formData.source_type}
                onChange={handleChange}
                label="Source Type"
                disabled={loading}
              >
                <MenuItem value="csv">CSV File</MenuItem>
                <MenuItem value="database">Database</MenuItem>
                <MenuItem value="api">API</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <TextField
              required
              fullWidth
              label="Connection String"
              name="connection_string"
              value={formData.connection_string}
              onChange={handleChange}
              helperText={getConnectionStringHelp()}
              disabled={loading}
            />
          </Grid>

          <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button
              variant="outlined"
              onClick={() => navigate('/data-sources')}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : null}
            >
              {loading ? 'Creating...' : 'Create Data Source'}
            </Button>
          </Grid>
        </Grid>
      </Box>
    </Paper>
  );
};

export default DataSourceForm;

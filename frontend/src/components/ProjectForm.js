import React, { useState, useEffect } from 'react';
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

const ProjectForm = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    source_system: '',
    target_system: ''
  });
  const [dataSources, setDataSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetchingDataSources, setFetchingDataSources] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Fetch data sources
    api.get('/analyzer/data-sources/')
      .then(response => {
        setDataSources(response.data);
      })
      .catch(error => {
        console.error('Error fetching data sources:', error);
        setError('Failed to load data sources. Please try again later.');
      })
      .finally(() => {
        setFetchingDataSources(false);
      });
  }, []);

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
      await api.post('/orchestrator/projects/', formData);
      navigate('/projects');
    } catch (error) {
      setError(`Error creating project: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 3, maxWidth: 800, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Create New Migration Project
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {fetchingDataSources ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : dataSources.length < 2 ? (
        <Alert severity="warning" sx={{ mb: 3 }}>
          You need at least two data sources to create a migration project.
          <Button
            variant="text"
            color="inherit"
            sx={{ ml: 1 }}
            onClick={() => navigate('/data-sources/new')}
          >
            Add Data Source
          </Button>
        </Alert>
      ) : (
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                required
                fullWidth
                label="Project Name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                disabled={loading}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                multiline
                rows={3}
                disabled={loading}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Source System</InputLabel>
                <Select
                  name="source_system"
                  value={formData.source_system}
                  onChange={handleChange}
                  label="Source System"
                  disabled={loading}
                >
                  {dataSources.map(source => (
                    <MenuItem key={source.id} value={source.name}>
                      {source.name} ({source.source_type})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Target System</InputLabel>
                <Select
                  name="target_system"
                  value={formData.target_system}
                  onChange={handleChange}
                  label="Target System"
                  disabled={loading}
                >
                  {dataSources
                    .filter(source => source.name !== formData.source_system)
                    .map(source => (
                      <MenuItem key={source.id} value={source.name}>
                        {source.name} ({source.source_type})
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
              <Button
                variant="outlined"
                onClick={() => navigate('/projects')}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                disabled={loading || !formData.source_system || !formData.target_system}
                startIcon={loading ? <CircularProgress size={20} /> : null}
              >
                {loading ? 'Creating...' : 'Create Project'}
              </Button>
            </Grid>
          </Grid>
        </Box>
      )}
    </Paper>
  );
};

export default ProjectForm;

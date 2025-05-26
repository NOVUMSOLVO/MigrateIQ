import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Button,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  PlayArrow as AnalyzeIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Preview as PreviewIcon,
  Storage as EntityIcon
} from '@mui/icons-material';
import axios from 'axios';

// TabPanel component for tab content
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`datasource-tabpanel-${index}`}
      aria-labelledby={`datasource-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const DataSourceDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [dataSource, setDataSource] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [analyzing, setAnalyzing] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editFormData, setEditFormData] = useState({
    name: '',
    source_type: '',
    connection_string: ''
  });
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState(null);

  // Fetch data source details
  useEffect(() => {
    fetchDataSource();
  }, [id]);

  const fetchDataSource = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get(`/api/analyzer/data-sources/${id}/`);
      setDataSource(response.data);
    } catch (error) {
      setError(`Error fetching data source: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    
    // Load preview data when switching to the Preview tab
    if (newValue === 1 && !previewData) {
      fetchPreviewData();
    }
  };

  const fetchPreviewData = async () => {
    if (!dataSource) return;
    
    setPreviewLoading(true);
    
    try {
      // In a real implementation, this would call a backend endpoint
      // For now, we'll simulate a response
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (dataSource.source_type === 'csv') {
        setPreviewData({
          columns: ['id', 'name', 'age', 'email'],
          rows: [
            { id: 1, name: 'John Doe', age: 30, email: 'john@example.com' },
            { id: 2, name: 'Jane Smith', age: 25, email: 'jane@example.com' },
            { id: 3, name: 'Bob Johnson', age: 40, email: 'bob@example.com' }
          ]
        });
      } else {
        setPreviewData({
          columns: ['id', 'title', 'status'],
          rows: [
            { id: 1, title: 'Record 1', status: 'Active' },
            { id: 2, title: 'Record 2', status: 'Inactive' },
            { id: 3, title: 'Record 3', status: 'Active' }
          ]
        });
      }
    } catch (error) {
      console.error('Error fetching preview data:', error);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError('');
    
    try {
      await axios.post(`/api/analyzer/data-sources/${id}/analyze/`);
      fetchDataSource(); // Refresh data source to get updated entities
    } catch (error) {
      setError(`Error analyzing data source: ${error.response?.data?.error || error.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleEdit = () => {
    if (dataSource) {
      setEditFormData({
        name: dataSource.name,
        source_type: dataSource.source_type,
        connection_string: dataSource.connection_string || ''
      });
      setEditDialogOpen(true);
    }
  };

  const handleEditDialogClose = () => {
    setEditDialogOpen(false);
    setTestResult(null);
  };

  const handleEditFormChange = (e) => {
    const { name, value } = e.target;
    setEditFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleEditSubmit = async () => {
    try {
      await axios.put(`/api/analyzer/data-sources/${id}/`, editFormData);
      setEditDialogOpen(false);
      fetchDataSource(); // Refresh data
    } catch (error) {
      setError(`Error updating data source: ${error.response?.data?.error || error.message}`);
    }
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setTestResult(null);
    
    try {
      // In a real implementation, this would call a backend endpoint
      // For now, we'll simulate a response
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setTestResult({
        success: true,
        message: 'Connection successful!'
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: `Connection failed: ${error.message}`
      });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this data source? This action cannot be undone.')) {
      try {
        await axios.delete(`/api/analyzer/data-sources/${id}/`);
        navigate('/data-sources');
      } catch (error) {
        setError(`Error deleting data source: ${error.response?.data?.error || error.message}`);
      }
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={() => navigate('/data-sources')}>
          Back to Data Sources
        </Button>
      </Container>
    );
  }

  if (!dataSource) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="warning">
          Data source not found
        </Alert>
        <Button variant="contained" onClick={() => navigate('/data-sources')} sx={{ mt: 2 }}>
          Back to Data Sources
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h4" gutterBottom>
              {dataSource.name}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Chip 
                label={dataSource.source_type.toUpperCase()} 
                color="primary" 
                variant="outlined" 
              />
              <Typography variant="body2" color="textSecondary">
                Created: {new Date(dataSource.created_at).toLocaleString()}
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button 
              startIcon={<RefreshIcon />} 
              onClick={fetchDataSource}
              variant="outlined"
            >
              Refresh
            </Button>
            <Button 
              startIcon={<EditIcon />} 
              onClick={handleEdit}
              variant="outlined"
            >
              Edit
            </Button>
            <Button 
              startIcon={<DeleteIcon />} 
              onClick={handleDelete}
              variant="outlined" 
              color="error"
            >
              Delete
            </Button>
          </Box>
        </Box>
        
        <Divider sx={{ my: 2 }} />
        
        <Box sx={{ width: '100%' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="data source tabs">
              <Tab label="Overview" />
              <Tab label="Preview Data" />
              <Tab label="Entities" />
            </Tabs>
          </Box>
          
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Connection Details
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Connection String:
                  </Typography>
                  <Typography variant="body1" sx={{ wordBreak: 'break-all' }}>
                    {dataSource.connection_string || 'Not provided'}
                  </Typography>
                </Box>
                
                <Button 
                  variant="contained" 
                  color="primary" 
                  startIcon={<AnalyzeIcon />}
                  onClick={handleAnalyze}
                  disabled={analyzing}
                >
                  {analyzing ? 'Analyzing...' : 'Analyze Data Source'}
                </Button>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Statistics
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Entities:
                  </Typography>
                  <Typography variant="body1">
                    {dataSource.entities?.length || 0}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Last Updated:
                  </Typography>
                  <Typography variant="body1">
                    {dataSource.updated_at ? new Date(dataSource.updated_at).toLocaleString() : 'Never'}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </TabPanel>
          
          <TabPanel value={tabValue} index={1}>
            {previewLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
                <CircularProgress />
              </Box>
            ) : previewData ? (
              <Box sx={{ overflowX: 'auto' }}>
                <Typography variant="h6" gutterBottom>
                  Data Preview
                </Typography>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      {previewData.columns.map(column => (
                        <th key={column} style={{ 
                          border: '1px solid #ddd', 
                          padding: '8px', 
                          textAlign: 'left',
                          backgroundColor: '#f2f2f2'
                        }}>
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.rows.map((row, index) => (
                      <tr key={index}>
                        {previewData.columns.map(column => (
                          <td key={column} style={{ border: '1px solid #ddd', padding: '8px' }}>
                            {row[column]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Box>
            ) : (
              <Box sx={{ textAlign: 'center', p: 3 }}>
                <Typography variant="body1" gutterBottom>
                  No preview data available.
                </Typography>
                <Button 
                  variant="contained" 
                  startIcon={<PreviewIcon />}
                  onClick={fetchPreviewData}
                >
                  Load Preview
                </Button>
              </Box>
            )}
          </TabPanel>
          
          <TabPanel value={tabValue} index={2}>
            {dataSource.entities && dataSource.entities.length > 0 ? (
              <List>
                {dataSource.entities.map(entity => (
                  <ListItem 
                    key={entity.id} 
                    divider
                    secondaryAction={
                      <IconButton edge="end" aria-label="view entity">
                        <EntityIcon />
                      </IconButton>
                    }
                  >
                    <ListItemText
                      primary={entity.name}
                      secondary={`${entity.fields?.length || 0} fields • ${entity.record_count || 0} records`}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Box sx={{ textAlign: 'center', p: 3 }}>
                <Typography variant="body1" gutterBottom>
                  No entities found. Analyze the data source to extract entities.
                </Typography>
                <Button 
                  variant="contained" 
                  startIcon={<AnalyzeIcon />}
                  onClick={handleAnalyze}
                  disabled={analyzing}
                >
                  {analyzing ? 'Analyzing...' : 'Analyze Data Source'}
                </Button>
              </Box>
            )}
          </TabPanel>
        </Box>
      </Paper>
      
      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={handleEditDialogClose} maxWidth="md" fullWidth>
        <DialogTitle>Edit Data Source</DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 1 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  label="Name"
                  name="name"
                  value={editFormData.name}
                  onChange={handleEditFormChange}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Source Type</InputLabel>
                  <Select
                    name="source_type"
                    value={editFormData.source_type}
                    onChange={handleEditFormChange}
                    label="Source Type"
                  >
                    <MenuItem value="csv">CSV File</MenuItem>
                    <MenuItem value="database">Database</MenuItem>
                    <MenuItem value="api">API</MenuItem>
                    <MenuItem value="json">JSON</MenuItem>
                    <MenuItem value="xml">XML</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  label="Connection String"
                  name="connection_string"
                  value={editFormData.connection_string}
                  onChange={handleEditFormChange}
                  margin="normal"
                  multiline
                  rows={2}
                />
              </Grid>
            </Grid>
            
            {testResult && (
              <Alert 
                severity={testResult.success ? "success" : "error"} 
                sx={{ mt: 2 }}
              >
                {testResult.message}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={handleTestConnection} 
            disabled={testingConnection}
            startIcon={testingConnection ? <CircularProgress size={20} /> : null}
          >
            {testingConnection ? 'Testing...' : 'Test Connection'}
          </Button>
          <Button onClick={handleEditDialogClose}>Cancel</Button>
          <Button onClick={handleEditSubmit} variant="contained">Save Changes</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DataSourceDetail;

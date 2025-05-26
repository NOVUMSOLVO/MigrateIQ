import React, { useState, useEffect, useMemo } from 'react';
import {
  Container,
  Typography,
  Grid,
  Paper,
  Box,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  CircularProgress,
  Divider,
  Card,
  CardContent,
  LinearProgress,
  useTheme
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as StartIcon,
  Refresh as RefreshIcon,
  ArrowForward as ArrowForwardIcon,
  Storage as StorageIcon,
  Assignment as ProjectIcon,
  CheckCircle as CompletedIcon,
  Error as ErrorIcon,
  Timeline as ProgressIcon
} from '@mui/icons-material';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const Dashboard = () => {
  const theme = useTheme();
  const [status, setStatus] = useState('Loading...');
  const [projects, setProjects] = useState([]);
  const [dataSources, setDataSources] = useState([]);
  const [loading, setLoading] = useState({
    projects: true,
    dataSources: true
  });

  // Calculate statistics from projects and data sources
  const stats = useMemo(() => {
    // Project status counts
    const statusCounts = {
      DRAFT: 0,
      PLANNING: 0,
      IN_PROGRESS: 0,
      COMPLETED: 0,
      FAILED: 0
    };

    projects.forEach(project => {
      if (statusCounts.hasOwnProperty(project.status)) {
        statusCounts[project.status]++;
      }
    });

    // Data source type counts
    const sourceTypeCounts = {};
    dataSources.forEach(source => {
      if (source.source_type) {
        sourceTypeCounts[source.source_type] = (sourceTypeCounts[source.source_type] || 0) + 1;
      }
    });

    // Total entities across all data sources
    const totalEntities = dataSources.reduce((sum, source) => sum + (source.entities?.length || 0), 0);

    return {
      totalProjects: projects.length,
      totalDataSources: dataSources.length,
      totalEntities,
      completedProjects: statusCounts.COMPLETED,
      inProgressProjects: statusCounts.IN_PROGRESS,
      statusCounts,
      sourceTypeCounts
    };
  }, [projects, dataSources]);

  useEffect(() => {
    // Check if the backend is running
    api.get('/health/')
      .then(response => {
        setStatus('Connected to backend');
        fetchProjects();
        fetchDataSources();
      })
      .catch(error => {
        setStatus('Backend connection failed');
        console.error('Backend connection error:', error);
        setLoading({
          projects: false,
          dataSources: false
        });
      });
  }, []);

  const fetchProjects = () => {
    setLoading(prev => ({ ...prev, projects: true }));
    api.get('/orchestrator/projects/')
      .then(response => {
        setProjects(response.data);
      })
      .catch(error => {
        console.error('Error fetching projects:', error);
      })
      .finally(() => {
        setLoading(prev => ({ ...prev, projects: false }));
      });
  };

  const fetchDataSources = () => {
    setLoading(prev => ({ ...prev, dataSources: true }));
    api.get('/analyzer/data-sources/')
      .then(response => {
        setDataSources(response.data);
      })
      .catch(error => {
        console.error('Error fetching data sources:', error);
      })
      .finally(() => {
        setLoading(prev => ({ ...prev, dataSources: false }));
      });
  };

  const startMigration = (projectId) => {
    api.post(`/orchestrator/projects/${projectId}/start/`)
      .then(response => {
        alert('Migration started successfully');
        fetchProjects(); // Refresh projects to update status
      })
      .catch(error => {
        alert(`Error starting migration: ${error.response?.data?.error || error.message}`);
      });
  };

  const getStatusChip = (status) => {
    let color;
    switch (status) {
      case 'DRAFT':
        color = 'default';
        break;
      case 'PLANNING':
        color = 'info';
        break;
      case 'IN_PROGRESS':
        color = 'warning';
        break;
      case 'COMPLETED':
        color = 'success';
        break;
      case 'FAILED':
        color = 'error';
        break;
      default:
        color = 'default';
    }
    return <Chip label={status} color={color} size="small" />;
  };

  // Prepare chart data
  const projectStatusChartData = useMemo(() => {
    return {
      labels: Object.keys(stats.statusCounts),
      datasets: [
        {
          label: 'Projects by Status',
          data: Object.values(stats.statusCounts),
          backgroundColor: [
            '#e0e0e0', // DRAFT - gray
            '#42a5f5', // PLANNING - blue
            '#ff9800', // IN_PROGRESS - orange
            '#4caf50', // COMPLETED - green
            '#f44336', // FAILED - red
          ],
          borderWidth: 1,
        },
      ],
    };
  }, [stats.statusCounts]);

  const dataSourceTypeChartData = useMemo(() => {
    return {
      labels: Object.keys(stats.sourceTypeCounts),
      datasets: [
        {
          label: 'Data Sources by Type',
          data: Object.values(stats.sourceTypeCounts),
          backgroundColor: [
            '#8884d8',
            '#83a6ed',
            '#8dd1e1',
            '#82ca9d',
            '#a4de6c',
          ],
          borderWidth: 1,
        },
      ],
    };
  }, [stats.sourceTypeCounts]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
      },
    },
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4, position: 'relative' }}>
      {/* Floating Background Elements */}
      <Box
        className="floating-element"
        sx={{
          position: 'absolute',
          top: '10%',
          right: '10%',
          width: 100,
          height: 100,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(236, 72, 153, 0.1))',
          zIndex: -1,
        }}
      />
      <Box
        className="floating-element"
        sx={{
          position: 'absolute',
          bottom: '20%',
          left: '5%',
          width: 80,
          height: 80,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1))',
          zIndex: -1,
        }}
      />

      <Typography
        variant="h4"
        gutterBottom
        className="dashboard-title"
        sx={{
          textAlign: 'center',
          mb: 4,
          background: 'linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          fontWeight: 700,
          textShadow: '0 4px 8px rgba(0, 0, 0, 0.3)',
        }}
      >
        MigrateIQ Dashboard
      </Typography>

      {/* System Status */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          <Paper
            className="glass-card"
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 3,
                background: status === 'Connected to backend'
                  ? 'linear-gradient(90deg, #10b981, #34d399)'
                  : 'linear-gradient(90deg, #ef4444, #f87171)',
                opacity: 0.8,
              }}
            />
            <Typography
              variant="h6"
              gutterBottom
              sx={{
                fontWeight: 600,
                color: 'white',
                mb: 2,
              }}
            >
              System Status
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography
                variant="body1"
                sx={{
                  color: 'rgba(255, 255, 255, 0.9)',
                  fontWeight: 500,
                }}
              >
                Backend Status:
              </Typography>
              <Chip
                label={status}
                color={status === 'Connected to backend' ? 'success' : 'error'}
                size="medium"
                sx={{
                  fontWeight: 600,
                  px: 2,
                  background: status === 'Connected to backend'
                    ? 'linear-gradient(135deg, #10b981, #34d399)'
                    : 'linear-gradient(135deg, #ef4444, #f87171)',
                  color: 'white',
                  border: 'none',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    left: 8,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: 'rgba(255, 255, 255, 0.8)',
                    animation: status === 'Connected to backend' ? 'pulse 2s infinite' : 'none',
                  }
                }}
              />
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Summary Statistics Cards */}
      <Typography
        variant="h6"
        gutterBottom
        sx={{
          mt: 2,
          mb: 3,
          color: 'white',
          fontWeight: 600,
          textAlign: 'center',
        }}
      >
        Migration Overview
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card
            className="stats-card"
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(99, 102, 241, 0.1) 100%)',
              position: 'relative',
              overflow: 'hidden',
              cursor: 'pointer',
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 3,
                background: 'linear-gradient(90deg, #6366f1, #818cf8)',
              }}
            />
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography
                  variant="h4"
                  component="div"
                  sx={{
                    fontWeight: 700,
                    color: 'white',
                    textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
                  }}
                >
                  {stats.totalProjects}
                </Typography>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: '12px',
                    background: 'rgba(255, 255, 255, 0.15)',
                    backdropFilter: 'blur(10px)',
                  }}
                >
                  <ProjectIcon
                    fontSize="large"
                    sx={{
                      color: 'white',
                      filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))',
                    }}
                  />
                </Box>
              </Box>
              <Typography
                variant="body1"
                sx={{
                  color: 'rgba(255, 255, 255, 0.9)',
                  fontWeight: 500,
                }}
              >
                Total Projects
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            className="stats-card"
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.1) 100%)',
              position: 'relative',
              overflow: 'hidden',
              cursor: 'pointer',
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 3,
                background: 'linear-gradient(90deg, #10b981, #34d399)',
              }}
            />
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography
                  variant="h4"
                  component="div"
                  sx={{
                    fontWeight: 700,
                    color: 'white',
                    textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
                  }}
                >
                  {stats.completedProjects}
                </Typography>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: '12px',
                    background: 'rgba(255, 255, 255, 0.15)',
                    backdropFilter: 'blur(10px)',
                  }}
                >
                  <CompletedIcon
                    fontSize="large"
                    sx={{
                      color: 'white',
                      filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))',
                    }}
                  />
                </Box>
              </Box>
              <Typography
                variant="body1"
                sx={{
                  color: 'rgba(255, 255, 255, 0.9)',
                  fontWeight: 500,
                }}
              >
                Completed Migrations
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            className="stats-card"
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.1) 100%)',
              position: 'relative',
              overflow: 'hidden',
              cursor: 'pointer',
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 3,
                background: 'linear-gradient(90deg, #f59e0b, #fbbf24)',
              }}
            />
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography
                  variant="h4"
                  component="div"
                  sx={{
                    fontWeight: 700,
                    color: 'white',
                    textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
                  }}
                >
                  {stats.inProgressProjects}
                </Typography>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: '12px',
                    background: 'rgba(255, 255, 255, 0.15)',
                    backdropFilter: 'blur(10px)',
                  }}
                >
                  <ProgressIcon
                    fontSize="large"
                    sx={{
                      color: 'white',
                      filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))',
                    }}
                  />
                </Box>
              </Box>
              <Typography
                variant="body1"
                sx={{
                  color: 'rgba(255, 255, 255, 0.9)',
                  fontWeight: 500,
                }}
              >
                In Progress
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            className="stats-card"
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(59, 130, 246, 0.1) 100%)',
              position: 'relative',
              overflow: 'hidden',
              cursor: 'pointer',
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 3,
                background: 'linear-gradient(90deg, #3b82f6, #60a5fa)',
              }}
            />
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography
                  variant="h4"
                  component="div"
                  sx={{
                    fontWeight: 700,
                    color: 'white',
                    textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
                  }}
                >
                  {stats.totalDataSources}
                </Typography>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: '12px',
                    background: 'rgba(255, 255, 255, 0.15)',
                    backdropFilter: 'blur(10px)',
                  }}
                >
                  <StorageIcon
                    fontSize="large"
                    sx={{
                      color: 'white',
                      filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))',
                    }}
                  />
                </Box>
              </Box>
              <Typography
                variant="body1"
                sx={{
                  color: 'rgba(255, 255, 255, 0.9)',
                  fontWeight: 500,
                  mb: 0.5,
                }}
              >
                Data Sources
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontWeight: 400,
                }}
              >
                {stats.totalEntities} Entities
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Paper
            className="chart-container glass-card"
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              height: 350,
              background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.06) 100%)',
            }}
          >
            <Typography
              variant="h6"
              gutterBottom
              sx={{
                color: 'white',
                fontWeight: 600,
                mb: 3,
                textAlign: 'center',
              }}
            >
              Project Status Distribution
            </Typography>
            <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {projects.length > 0 ? (
                <Pie data={projectStatusChartData} options={chartOptions} />
              ) : (
                <Typography
                  variant="body2"
                  sx={{
                    color: 'rgba(255, 255, 255, 0.7)',
                    textAlign: 'center',
                  }}
                >
                  No project data available
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper
            className="chart-container glass-card"
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              height: 350,
              background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.06) 100%)',
            }}
          >
            <Typography
              variant="h6"
              gutterBottom
              sx={{
                color: 'white',
                fontWeight: 600,
                mb: 3,
                textAlign: 'center',
              }}
            >
              Data Source Types
            </Typography>
            <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {dataSources.length > 0 ? (
                <Pie data={dataSourceTypeChartData} options={chartOptions} />
              ) : (
                <Typography
                  variant="body2"
                  sx={{
                    color: 'rgba(255, 255, 255, 0.7)',
                    textAlign: 'center',
                  }}
                >
                  No data source information available
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Projects and Data Sources Lists */}
      <Typography
        variant="h6"
        gutterBottom
        sx={{
          mt: 2,
          mb: 3,
          color: 'white',
          fontWeight: 600,
          textAlign: 'center',
        }}
      >
        Migration Projects & Data Sources
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper
            className="glass-card"
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              minHeight: 400,
              background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.06) 100%)',
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 600,
                  color: 'white',
                }}
              >
                Migration Projects
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <IconButton
                  size="small"
                  onClick={fetchProjects}
                  disabled={loading.projects}
                  sx={{
                    color: 'white',
                    background: 'rgba(255, 255, 255, 0.1)',
                    backdropFilter: 'blur(10px)',
                    '&:hover': {
                      background: 'rgba(255, 255, 255, 0.2)',
                    },
                  }}
                >
                  <RefreshIcon />
                </IconButton>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  size="small"
                  component={Link}
                  to="/projects/new"
                  sx={{
                    background: 'linear-gradient(135deg, #6366f1, #818cf8)',
                    color: 'white',
                    fontWeight: 600,
                    px: 2,
                    '&:hover': {
                      background: 'linear-gradient(135deg, #4f46e5, #6366f1)',
                      transform: 'translateY(-1px)',
                    },
                  }}
                >
                  New Project
                </Button>
              </Box>
            </Box>
            <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.2)', mb: 2 }} />

            {loading.projects ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
                <CircularProgress />
              </Box>
            ) : projects.length > 0 ? (
              <List>
                {projects.map(project => (
                  <ListItem key={project.id} divider>
                    <ListItemText
                      primary={project.name}
                      secondary={`${project.source_system} → ${project.target_system}`}
                    />
                    <ListItemSecondaryAction>
                      {getStatusChip(project.status)}
                      <IconButton
                        edge="end"
                        component={Link}
                        to={`/projects/${project.id}`}
                        sx={{ ml: 1 }}
                      >
                        <ArrowForwardIcon />
                      </IconButton>
                      {project.status !== 'IN_PROGRESS' && (
                        <IconButton
                          edge="end"
                          onClick={() => startMigration(project.id)}
                          sx={{ ml: 1 }}
                          color="primary"
                        >
                          <StartIcon />
                        </IconButton>
                      )}
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            ) : (
              <Box sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  No projects yet. Create your first migration project to get started.
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<AddIcon />}
                  component={Link}
                  to="/projects/new"
                >
                  Create Project
                </Button>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper
            className="glass-card"
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              minHeight: 400,
              background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.06) 100%)',
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 600,
                  color: 'white',
                }}
              >
                Data Sources
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <IconButton
                  size="small"
                  onClick={fetchDataSources}
                  disabled={loading.dataSources}
                  sx={{
                    color: 'white',
                    background: 'rgba(255, 255, 255, 0.1)',
                    backdropFilter: 'blur(10px)',
                    '&:hover': {
                      background: 'rgba(255, 255, 255, 0.2)',
                    },
                  }}
                >
                  <RefreshIcon />
                </IconButton>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  size="small"
                  component={Link}
                  to="/data-sources/new"
                  sx={{
                    background: 'linear-gradient(135deg, #3b82f6, #60a5fa)',
                    color: 'white',
                    fontWeight: 600,
                    px: 2,
                    '&:hover': {
                      background: 'linear-gradient(135deg, #2563eb, #3b82f6)',
                      transform: 'translateY(-1px)',
                    },
                  }}
                >
                  Add Source
                </Button>
              </Box>
            </Box>
            <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.2)', mb: 2 }} />

            {loading.dataSources ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
                <CircularProgress />
              </Box>
            ) : dataSources.length > 0 ? (
              <List>
                {dataSources.map(source => (
                  <ListItem key={source.id} divider>
                    <ListItemText
                      primary={source.name}
                      secondary={`Type: ${source.source_type}`}
                    />
                    <ListItemSecondaryAction>
                      <Chip label={`${source.entities?.length || 0} entities`} size="small" />
                      <IconButton
                        edge="end"
                        component={Link}
                        to={`/data-sources/${source.id}`}
                        sx={{ ml: 1 }}
                      >
                        <ArrowForwardIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            ) : (
              <Box sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  No data sources connected. Add a data source to begin.
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<AddIcon />}
                  component={Link}
                  to="/data-sources/new"
                >
                  Add Data Source
                </Button>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;

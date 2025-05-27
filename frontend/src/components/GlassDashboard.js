import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  Avatar,
  Fab,
  Tooltip,
  useTheme,
  alpha
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  TrendingUp,
  Storage,
  CloudSync,
  Security,
  Analytics,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

const GlassDashboard = () => {
  const theme = useTheme();
  const [stats, setStats] = useState({
    totalProjects: 12,
    activeProjects: 8,
    completedMigrations: 45,
    dataProcessed: '2.4TB',
    successRate: 98.5,
    avgMigrationTime: '4.2h'
  });

  const [recentProjects, setRecentProjects] = useState([
    {
      id: 1,
      name: 'Customer Data Migration',
      status: 'in_progress',
      progress: 75,
      source: 'MySQL',
      target: 'PostgreSQL',
      lastUpdate: '2 hours ago'
    },
    {
      id: 2,
      name: 'Legacy System Upgrade',
      status: 'completed',
      progress: 100,
      source: 'Oracle',
      target: 'MongoDB',
      lastUpdate: '1 day ago'
    },
    {
      id: 3,
      name: 'Cloud Migration Project',
      status: 'planning',
      progress: 25,
      source: 'On-Premise',
      target: 'AWS RDS',
      lastUpdate: '3 hours ago'
    }
  ]);

  // Glass morphism styles
  const glassStyle = {
    background: alpha(theme.palette.background.paper, 0.1),
    backdropFilter: 'blur(20px)',
    border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
    borderRadius: '16px',
    boxShadow: `0 8px 32px ${alpha(theme.palette.common.black, 0.1)}`,
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
    hover: { 
      scale: 1.02,
      boxShadow: `0 12px 40px ${alpha(theme.palette.common.black, 0.15)}`
    }
  };

  const StatCard = ({ icon, title, value, subtitle, color = 'primary' }) => (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover="hover"
      transition={{ duration: 0.3 }}
    >
      <Card sx={{ ...glassStyle, height: '100%' }}>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <Avatar
              sx={{
                bgcolor: alpha(theme.palette[color].main, 0.1),
                color: theme.palette[color].main,
                mr: 2
              }}
            >
              {icon}
            </Avatar>
            <Typography variant="h6" color="textPrimary">
              {title}
            </Typography>
          </Box>
          <Typography variant="h4" fontWeight="bold" color={`${color}.main`}>
            {value}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            {subtitle}
          </Typography>
        </CardContent>
      </Card>
    </motion.div>
  );

  const ProjectCard = ({ project }) => {
    const getStatusColor = (status) => {
      switch (status) {
        case 'completed': return 'success';
        case 'in_progress': return 'primary';
        case 'planning': return 'warning';
        default: return 'default';
      }
    };

    return (
      <motion.div
        variants={cardVariants}
        initial="hidden"
        animate="visible"
        whileHover="hover"
        transition={{ duration: 0.3 }}
      >
        <Card sx={{ ...glassStyle, mb: 2 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6" fontWeight="bold">
                {project.name}
              </Typography>
              <Chip
                label={project.status.replace('_', ' ')}
                color={getStatusColor(project.status)}
                size="small"
                sx={{ textTransform: 'capitalize' }}
              />
            </Box>
            
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography variant="body2" color="textSecondary">
                {project.source} → {project.target}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {project.progress}%
              </Typography>
            </Box>
            
            <LinearProgress
              variant="determinate"
              value={project.progress}
              sx={{
                mb: 1,
                height: 8,
                borderRadius: 4,
                backgroundColor: alpha(theme.palette.grey[500], 0.2),
                '& .MuiLinearProgress-bar': {
                  borderRadius: 4,
                  background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
                }
              }}
            />
            
            <Typography variant="caption" color="textSecondary">
              Last updated: {project.lastUpdate}
            </Typography>
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  return (
    <Box sx={{ p: 3, minHeight: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Typography variant="h4" fontWeight="bold" color="white">
            MigrateIQ Dashboard
          </Typography>
          <Typography variant="subtitle1" color="rgba(255,255,255,0.8)">
            Welcome back! Here's your migration overview
          </Typography>
        </motion.div>
        
        <Box display="flex" gap={1}>
          <Tooltip title="Refresh">
            <IconButton sx={{ color: 'white' }}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Notifications">
            <IconButton sx={{ color: 'white' }}>
              <NotificationsIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Settings">
            <IconButton sx={{ color: 'white' }}>
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Stats Grid */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={2}>
          <StatCard
            icon={<DashboardIcon />}
            title="Total Projects"
            value={stats.totalProjects}
            subtitle="All time"
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <StatCard
            icon={<TrendingUp />}
            title="Active"
            value={stats.activeProjects}
            subtitle="In progress"
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <StatCard
            icon={<Storage />}
            title="Data Processed"
            value={stats.dataProcessed}
            subtitle="Total volume"
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <StatCard
            icon={<CloudSync />}
            title="Completed"
            value={stats.completedMigrations}
            subtitle="Migrations"
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <StatCard
            icon={<Security />}
            title="Success Rate"
            value={`${stats.successRate}%`}
            subtitle="Quality score"
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <StatCard
            icon={<Analytics />}
            title="Avg Time"
            value={stats.avgMigrationTime}
            subtitle="Per migration"
            color="warning"
          />
        </Grid>
      </Grid>

      {/* Recent Projects */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Card sx={{ ...glassStyle }}>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" mb={3}>
                  Recent Projects
                </Typography>
                <AnimatePresence>
                  {recentProjects.map((project, index) => (
                    <motion.div
                      key={project.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ duration: 0.3, delay: index * 0.1 }}
                    >
                      <ProjectCard project={project} />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
        
        <Grid item xs={12} lg={4}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <Card sx={{ ...glassStyle, height: '100%' }}>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" mb={3}>
                  Quick Actions
                </Typography>
                {/* Quick actions content would go here */}
                <Typography variant="body2" color="textSecondary">
                  Quick action buttons and shortcuts will be implemented here.
                </Typography>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
      </Grid>

      {/* Floating Action Button */}
      <Tooltip title="New Migration Project">
        <Fab
          color="primary"
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            '&:hover': {
              transform: 'scale(1.1)',
            }
          }}
        >
          <AddIcon />
        </Fab>
      </Tooltip>
    </Box>
  );
};

export default GlassDashboard;

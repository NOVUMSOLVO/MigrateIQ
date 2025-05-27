/**
 * NHS Compliance Dashboard Component
 * 
 * Displays NHS and CQC compliance status, metrics, and alerts for healthcare data migration.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Security as SecurityIcon,
  HealthAndSafety as HealthIcon,
  Assessment as AssessmentIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Styled components for glass morphism effect
const GlassCard = styled(Card)(({ theme }) => ({
  background: 'rgba(255, 255, 255, 0.1)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255, 255, 255, 0.2)',
  borderRadius: '16px',
  transition: 'all 0.3s ease',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
  },
}));

const MetricCard = styled(GlassCard)(({ theme }) => ({
  textAlign: 'center',
  padding: theme.spacing(2),
  height: '100%',
}));

// Types
interface ComplianceData {
  organization: {
    organization_name: string;
    ods_code: string;
    dspt_status: string;
  };
  dspt_status: {
    status: string;
    days_until_expiry: number | null;
    scores: {
      data_security: number;
      staff_responsibilities: number;
      training: number;
    };
  };
  audit_summary: {
    last_30_days: {
      total: number;
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
  };
  safety_incidents: {
    last_30_days: {
      total: number;
      open: number;
      closed: number;
    };
  };
  compliance_score: {
    score: number;
    percentage: number;
    grade: string;
  };
  alerts: Array<{
    type: 'warning' | 'critical' | 'info';
    title: string;
    message: string;
    action_required: string;
  }>;
}

const NHSComplianceDashboard: React.FC = () => {
  const [complianceData, setComplianceData] = useState<ComplianceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<any>(null);

  useEffect(() => {
    fetchComplianceData();
  }, []);

  const fetchComplianceData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/nhs-compliance/dashboard/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch compliance data');
      }

      const data = await response.json();
      setComplianceData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'compliant':
      case 'standards_met':
        return 'success';
      case 'non_compliant':
      case 'standards_not_met':
        return 'error';
      case 'in_progress':
      case 'plan_agreed':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A':
        return '#4caf50';
      case 'B':
        return '#8bc34a';
      case 'C':
        return '#ff9800';
      case 'D':
        return '#ff5722';
      case 'F':
        return '#f44336';
      default:
        return '#9e9e9e';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          NHS Compliance Dashboard
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Error loading compliance data: {error}
        </Alert>
      </Box>
    );
  }

  if (!complianceData) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">
          No compliance data available. Please configure your NHS organization.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          NHS Compliance Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          {complianceData.organization.organization_name} ({complianceData.organization.ods_code})
        </Typography>
      </Box>

      {/* Alerts */}
      {complianceData.alerts.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Compliance Alerts
          </Typography>
          {complianceData.alerts.map((alert, index) => (
            <Alert
              key={index}
              severity={alert.type === 'critical' ? 'error' : alert.type as any}
              sx={{ mb: 1 }}
              action={
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => setSelectedAlert(alert)}
                >
                  Details
                </Button>
              }
            >
              <strong>{alert.title}</strong>: {alert.message}
            </Alert>
          ))}
        </Box>
      )}

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* DSPT Status */}
        <Grid item xs={12} md={3}>
          <MetricCard>
            <SecurityIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
            <Typography variant="h6" gutterBottom>
              DSPT Status
            </Typography>
            <Chip
              label={complianceData.dspt_status.status.replace('_', ' ')}
              color={getStatusColor(complianceData.dspt_status.status) as any}
              sx={{ mb: 1 }}
            />
            {complianceData.dspt_status.days_until_expiry && (
              <Typography variant="body2" color="text.secondary">
                Expires in {complianceData.dspt_status.days_until_expiry} days
              </Typography>
            )}
          </MetricCard>
        </Grid>

        {/* Compliance Score */}
        <Grid item xs={12} md={3}>
          <MetricCard>
            <AssessmentIcon sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
            <Typography variant="h6" gutterBottom>
              Compliance Score
            </Typography>
            <Typography
              variant="h3"
              sx={{ color: getGradeColor(complianceData.compliance_score.grade) }}
            >
              {complianceData.compliance_score.grade}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {complianceData.compliance_score.percentage}%
            </Typography>
          </MetricCard>
        </Grid>

        {/* Audit Events */}
        <Grid item xs={12} md={3}>
          <MetricCard>
            <InfoIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
            <Typography variant="h6" gutterBottom>
              Audit Events (30d)
            </Typography>
            <Typography variant="h3">
              {complianceData.audit_summary.last_30_days.total}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {complianceData.audit_summary.last_30_days.critical} critical
            </Typography>
          </MetricCard>
        </Grid>

        {/* Safety Incidents */}
        <Grid item xs={12} md={3}>
          <MetricCard>
            <HealthIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
            <Typography variant="h6" gutterBottom>
              Safety Incidents (30d)
            </Typography>
            <Typography variant="h3">
              {complianceData.safety_incidents.last_30_days.total}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {complianceData.safety_incidents.last_30_days.open} open
            </Typography>
          </MetricCard>
        </Grid>
      </Grid>

      {/* DSPT Scores */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <GlassCard>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                DSPT Assessment Scores
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Data Security: {complianceData.dspt_status.scores.data_security}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={complianceData.dspt_status.scores.data_security}
                  sx={{ mb: 1 }}
                />
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Staff Responsibilities: {complianceData.dspt_status.scores.staff_responsibilities}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={complianceData.dspt_status.scores.staff_responsibilities}
                  sx={{ mb: 1 }}
                />
              </Box>
              <Box>
                <Typography variant="body2" gutterBottom>
                  Training: {complianceData.dspt_status.scores.training}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={complianceData.dspt_status.scores.training}
                />
              </Box>
            </CardContent>
          </GlassCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <GlassCard>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <List>
                <ListItem button>
                  <ListItemIcon>
                    <SecurityIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="View DSPT Assessment"
                    secondary="Review current DSPT status and evidence"
                  />
                </ListItem>
                <Divider />
                <ListItem button>
                  <ListItemIcon>
                    <HealthIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Safety Incident Report"
                    secondary="Report a new patient safety incident"
                  />
                </ListItem>
                <Divider />
                <ListItem button>
                  <ListItemIcon>
                    <AssessmentIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Compliance Checklist"
                    secondary="Review migration compliance requirements"
                  />
                </ListItem>
              </List>
            </CardContent>
          </GlassCard>
        </Grid>
      </Grid>

      {/* Alert Details Dialog */}
      <Dialog
        open={!!selectedAlert}
        onClose={() => setSelectedAlert(null)}
        maxWidth="sm"
        fullWidth
      >
        {selectedAlert && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {getAlertIcon(selectedAlert.type)}
                {selectedAlert.title}
              </Box>
            </DialogTitle>
            <DialogContent>
              <Typography variant="body1" gutterBottom>
                {selectedAlert.message}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                <strong>Action Required:</strong> {selectedAlert.action_required}
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedAlert(null)}>Close</Button>
              <Button variant="contained" color="primary">
                Take Action
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default NHSComplianceDashboard;

import React, { useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  Work,
  Article,
  Speed,
  Add,
  PlayArrow,
  CheckCircle,
  Error,
  Schedule,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { dashboardService } from '@/services/dashboardService';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'react-hot-toast';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // Fetch dashboard data
  const {
    data: dashboardData,
    isLoading,
    error,
    refetch,
  } = useQuery('dashboardData', dashboardService.getDashboardData, {
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch system health
  const { data: systemHealth } = useQuery(
    'systemHealth',
    dashboardService.getSystemHealth,
    {
      refetchInterval: 60000, // Refetch every minute
    }
  );

  useEffect(() => {
    if (error) {
      toast.error('Failed to load dashboard data');
    }
  }, [error]);

  const handleCreateProject = () => {
    navigate('/projects?action=create');
  };

  const handleCreateJob = () => {
    navigate('/jobs?action=create');
  };

  const handleViewProjects = () => {
    navigate('/projects');
  };

  const handleViewJobs = () => {
    navigate('/jobs');
  };

  const handleViewContent = () => {
    navigate('/content');
  };

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  const stats = dashboardData?.statistics || {
    total_projects: 0,
    total_jobs: 0,
    completed_jobs: 0,
    success_rate: 0,
    total_content: 0,
  };

  const recentJobs = dashboardData?.recent_activity?.jobs || [];
  const recentContent = dashboardData?.recent_activity?.content || [];

  const getJobStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'failed':
        return <Error color="error" />;
      case 'running':
        return <PlayArrow color="primary" />;
      case 'pending':
        return <Schedule color="warning" />;
      default:
        return <Schedule />;
    }
  };

  const getJobStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'primary';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          Welcome back, {user?.full_name || user?.email?.split('@')[0] || 'User'}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here's what's happening with your scraping projects today.
        </Typography>
      </Box>

      {/* Quick Actions */}
      <Box mb={4}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="contained"
              fullWidth
              startIcon={<Add />}
              onClick={handleCreateProject}
              sx={{ py: 1.5 }}
            >
              New Project
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="outlined"
              fullWidth
              startIcon={<Work />}
              onClick={handleCreateJob}
              sx={{ py: 1.5 }}
            >
              New Job
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="outlined"
              fullWidth
              startIcon={<Article />}
              onClick={handleViewContent}
              sx={{ py: 1.5 }}
            >
              View Content
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="outlined"
              fullWidth
              startIcon={<Speed />}
              onClick={() => navigate('/monitoring')}
              sx={{ py: 1.5 }}
            >
              Monitoring
            </Button>
          </Grid>
        </Grid>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Projects
                  </Typography>
                  <Typography variant="h4">{stats.total_projects}</Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <TrendingUp />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Jobs
                  </Typography>
                  <Typography variant="h4">{stats.total_jobs}</Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <Work />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Success Rate
                  </Typography>
                  <Typography variant="h4">
                    {Math.round(stats.success_rate * 100)}%
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <CheckCircle />
                </Avatar>
              </Box>
              <Box mt={2}>
                <LinearProgress
                  variant="determinate"
                  value={stats.success_rate * 100}
                  color="success"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Content Items
                  </Typography>
                  <Typography variant="h4">{stats.total_content}</Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'warning.main' }}>
                  <Article />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">Recent Jobs</Typography>
                <Button size="small" onClick={handleViewJobs}>
                  View All
                </Button>
              </Box>
              <List>
                {recentJobs.length === 0 ? (
                  <ListItem>
                    <ListItemText
                      primary="No recent jobs"
                      secondary="Create your first scraping job to get started"
                    />
                  </ListItem>
                ) : (
                  recentJobs.slice(0, 5).map((job, index) => (
                    <React.Fragment key={job.id}>
                      <ListItem>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'transparent' }}>
                            {getJobStatusIcon(job.status)}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={job.name || job.url}
                          secondary={`${job.url} • ${new Date(job.created_at).toLocaleDateString()}`}
                        />
                        <Chip
                          label={job.status}
                          size="small"
                          color={getJobStatusColor(job.status) as any}
                          variant="outlined"
                        />
                      </ListItem>
                      {index < recentJobs.length - 1 && <Divider variant="inset" component="li" />}
                    </React.Fragment>
                  ))
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">Recent Content</Typography>
                <Button size="small" onClick={handleViewContent}>
                  View All
                </Button>
              </Box>
              <List>
                {recentContent.length === 0 ? (
                  <ListItem>
                    <ListItemText
                      primary="No content extracted yet"
                      secondary="Run some scraping jobs to see extracted content here"
                    />
                  </ListItem>
                ) : (
                  recentContent.slice(0, 5).map((content, index) => (
                    <React.Fragment key={content.id}>
                      <ListItem>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'secondary.main' }}>
                            <Article />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={content.title || 'Untitled Content'}
                          secondary={`${content.url} • ${new Date(content.created_at).toLocaleDateString()}`}
                        />
                        {content.content_type && (
                          <Chip
                            label={content.content_type}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </ListItem>
                      {index < recentContent.length - 1 && <Divider variant="inset" component="li" />}
                    </React.Fragment>
                  ))
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Health */}
      {systemHealth && (
        <Box mt={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Chip
                  label={systemHealth.overall}
                  color={systemHealth.overall === 'healthy' ? 'success' : 'error'}
                  variant="filled"
                />
                <Typography variant="body2" color="text.secondary">
                  All systems operational
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>
      )}
    </Box>
  );
};

export default DashboardPage;

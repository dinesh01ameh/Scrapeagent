import React from 'react';
import { Box, Typography, Card, CardContent, Button } from '@mui/material';
import { Work, Add } from '@mui/icons-material';

const JobsPage: React.FC = () => {
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Scraping Jobs
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage and monitor your scraping jobs and tasks.
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} size="large">
          New Job
        </Button>
      </Box>

      <Card>
        <CardContent sx={{ textAlign: 'center', py: 8 }}>
          <Work sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Jobs page coming soon
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This page will show all your scraping jobs with real-time status updates.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default JobsPage;

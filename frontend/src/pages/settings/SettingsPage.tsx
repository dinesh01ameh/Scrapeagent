import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';
import { Settings } from '@mui/icons-material';

const SettingsPage: React.FC = () => {
  return (
    <Box>
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your account settings and preferences.
        </Typography>
      </Box>

      <Card>
        <CardContent sx={{ textAlign: 'center', py: 8 }}>
          <Settings sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Settings page coming soon
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This page will contain user profile, API keys, and system preferences.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SettingsPage;

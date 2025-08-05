import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';
import { Article } from '@mui/icons-material';

const ContentPage: React.FC = () => {
  return (
    <Box>
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          Extracted Content
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Browse and analyze all the content extracted from your scraping jobs.
        </Typography>
      </Box>

      <Card>
        <CardContent sx={{ textAlign: 'center', py: 8 }}>
          <Article sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Content page coming soon
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This page will display all extracted content with search and filtering capabilities.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ContentPage;

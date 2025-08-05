import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Box,
  Divider,
  Chip,
} from '@mui/material';
import {
  Dashboard,
  FolderOpen,
  Work,
  Article,
  Settings,
  Analytics,
  Speed,
  CloudQueue,
} from '@mui/icons-material';
import { useAppSelector } from '@/store';

interface SidebarProps {
  drawerWidth: number;
}

const menuItems = [
  {
    text: 'Dashboard',
    icon: <Dashboard />,
    path: '/dashboard',
    description: 'Overview and statistics',
  },
  {
    text: 'Projects',
    icon: <FolderOpen />,
    path: '/projects',
    description: 'Manage scraping projects',
  },
  {
    text: 'Jobs',
    icon: <Work />,
    path: '/jobs',
    description: 'Scraping jobs and tasks',
    badge: 'active',
  },
  {
    text: 'Content',
    icon: <Article />,
    path: '/content',
    description: 'Extracted content and data',
  },
  {
    text: 'Analytics',
    icon: <Analytics />,
    path: '/analytics',
    description: 'Performance and insights',
    disabled: true,
  },
  {
    text: 'Monitoring',
    icon: <Speed />,
    path: '/monitoring',
    description: 'System health and metrics',
    disabled: true,
  },
  {
    text: 'Queue',
    icon: <CloudQueue />,
    path: '/queue',
    description: 'Job queue management',
    disabled: true,
  },
];

const bottomMenuItems = [
  {
    text: 'Settings',
    icon: <Settings />,
    path: '/settings',
    description: 'Account and preferences',
  },
];

const Sidebar: React.FC<SidebarProps> = ({ drawerWidth }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { sidebarOpen } = useAppSelector((state) => state.ui);

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const drawerContent = (
    <>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              width: 32,
              height: 32,
              borderRadius: 1,
              bgcolor: 'primary.main',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography variant="h6" color="white" fontWeight="bold">
              S
            </Typography>
          </Box>
          <Box>
            <Typography variant="h6" noWrap>
              SwissKnife
            </Typography>
            <Typography variant="caption" color="text.secondary" noWrap>
              AI Scraper
            </Typography>
          </Box>
        </Box>
      </Toolbar>

      <Divider />

      {/* Main Navigation */}
      <List sx={{ px: 1, py: 2 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              onClick={() => !item.disabled && handleNavigation(item.path)}
              disabled={item.disabled}
              sx={{
                borderRadius: 2,
                minHeight: 48,
                bgcolor: isActive(item.path) ? 'primary.main' : 'transparent',
                color: isActive(item.path) ? 'white' : 'inherit',
                '&:hover': {
                  bgcolor: isActive(item.path) ? 'primary.dark' : 'action.hover',
                },
                '&.Mui-disabled': {
                  opacity: 0.5,
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color: isActive(item.path) ? 'white' : 'inherit',
                  minWidth: 40,
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                secondary={!isActive(item.path) ? item.description : undefined}
                primaryTypographyProps={{
                  fontSize: '0.875rem',
                  fontWeight: isActive(item.path) ? 600 : 400,
                }}
                secondaryTypographyProps={{
                  fontSize: '0.75rem',
                  color: isActive(item.path) ? 'rgba(255,255,255,0.7)' : 'text.secondary',
                }}
              />
              {item.badge && (
                <Chip
                  label={item.badge}
                  size="small"
                  color="secondary"
                  sx={{ height: 20, fontSize: '0.6875rem' }}
                />
              )}
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* Bottom Navigation */}
      <Box sx={{ flexGrow: 1 }} />
      <Divider />
      <List sx={{ px: 1, py: 2 }}>
        {bottomMenuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              onClick={() => handleNavigation(item.path)}
              sx={{
                borderRadius: 2,
                minHeight: 48,
                bgcolor: isActive(item.path) ? 'primary.main' : 'transparent',
                color: isActive(item.path) ? 'white' : 'inherit',
                '&:hover': {
                  bgcolor: isActive(item.path) ? 'primary.dark' : 'action.hover',
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color: isActive(item.path) ? 'white' : 'inherit',
                  minWidth: 40,
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                secondary={!isActive(item.path) ? item.description : undefined}
                primaryTypographyProps={{
                  fontSize: '0.875rem',
                  fontWeight: isActive(item.path) ? 600 : 400,
                }}
                secondaryTypographyProps={{
                  fontSize: '0.75rem',
                  color: isActive(item.path) ? 'rgba(255,255,255,0.7)' : 'text.secondary',
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* Version Info */}
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          Version 1.0.0
        </Typography>
      </Box>
    </>
  );

  return (
    <Box
      component="nav"
      sx={{ width: { sm: sidebarOpen ? drawerWidth : 0 }, flexShrink: { sm: 0 } }}
    >
      <Drawer
        variant="persistent"
        open={sidebarOpen}
        sx={{
          display: { xs: 'none', sm: 'block' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            borderRight: '1px solid',
            borderColor: 'divider',
          },
        }}
      >
        {drawerContent}
      </Drawer>
    </Box>
  );
};

export default Sidebar;

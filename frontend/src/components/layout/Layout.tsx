import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box, CssBaseline, Toolbar } from '@mui/material';
import { useAppSelector } from '../../store';
import Sidebar from './Sidebar';
import Header from './Header';

const DRAWER_WIDTH = 280;

const Layout: React.FC = () => {
  const { sidebarOpen } = useAppSelector((state) => state.ui);

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />

      {/* Header */}
      <Header drawerWidth={DRAWER_WIDTH} />

      {/* Sidebar */}
      <Sidebar drawerWidth={DRAWER_WIDTH} />

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${sidebarOpen ? DRAWER_WIDTH : 0}px)` },
          ml: { sm: sidebarOpen ? 0 : `-${DRAWER_WIDTH}px` },
          transition: (theme) =>
            theme.transitions.create(['margin', 'width'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
};

export default Layout;

import React from 'react';
import { Box, CssBaseline, Toolbar } from '@mui/material';
import { useAppSelector } from '../../store';
import { MockAuthProvider } from '../../contexts/MockAuthContext';
import Sidebar from './Sidebar';
import Header from './Header';

const DRAWER_WIDTH = 280;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { sidebarOpen } = useAppSelector((state) => state.ui);

  return (
    <MockAuthProvider>
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
          {children}
        </Box>
      </Box>
    </MockAuthProvider>
  );
};

export default Layout;

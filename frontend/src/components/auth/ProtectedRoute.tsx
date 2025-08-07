import React, { ReactNode, useEffect, useState, useRef, Component, ErrorInfo } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography, Button, Alert } from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';
import { debugLogger, logNavigation, logComponentMount, logComponentUnmount } from '../../utils/debugLogger';

interface ProtectedRouteProps {
  children: ReactNode;
}

// Navigation Error Boundary Component
interface NavigationErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  navigationAttempts: number;
}

export class NavigationErrorBoundary extends Component<
  { children: React.ReactNode },
  NavigationErrorBoundaryState
> {
  private maxNavigationAttempts = 5;

  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      navigationAttempts: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<NavigationErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    debugLogger.error('NavigationErrorBoundary', 'ERROR_CAUGHT', { error: error.message, errorInfo });

    this.setState({
      error,
      errorInfo,
      navigationAttempts: this.state.navigationAttempts + 1
    });

    // If too many navigation errors, force a hard reset
    if (this.state.navigationAttempts >= this.maxNavigationAttempts) {
      debugLogger.error('NavigationErrorBoundary', 'MAX_ERRORS_REACHED', { attempts: this.state.navigationAttempts });
      localStorage.clear();
      window.location.href = '/login';
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
    debugLogger.log('NavigationErrorBoundary', 'MANUAL_RESET');
  };

  handleForceLogin = () => {
    localStorage.clear();
    window.location.href = '/login';
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          minHeight="100vh"
          gap={3}
          p={3}
        >
          <Alert severity="error" sx={{ maxWidth: 600 }}>
            <Typography variant="h6" gutterBottom>
              Navigation Error Detected
            </Typography>
            <Typography variant="body2" gutterBottom>
              The application encountered a navigation error. This might be due to authentication issues.
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Error: {this.state.error?.message}
            </Typography>
          </Alert>

          <Box display="flex" gap={2}>
            <Button variant="contained" onClick={this.handleReset}>
              Try Again
            </Button>
            <Button variant="outlined" onClick={this.handleForceLogin}>
              Go to Login
            </Button>
          </Box>

          {process.env.NODE_ENV === 'development' && (
            <Box mt={2} p={2} bgcolor="grey.100" borderRadius={1} maxWidth={800}>
              <Typography variant="caption" component="pre" sx={{ fontSize: '0.75rem' }}>
                {this.state.error?.stack}
              </Typography>
            </Box>
          )}
        </Box>
      );
    }

    return this.props.children;
  }
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const {
    isAuthenticated,
    isLoading,
    user,
    authState,
    canNavigateToProtectedRoute,
    shouldRedirectToLogin
  } = useAuth();
  const location = useLocation();
  const [initialLoad, setInitialLoad] = useState(true);
  const [hasRedirected, setHasRedirected] = useState(false);
  const redirectAttempts = useRef(0);
  const maxRedirectAttempts = 3;
  const componentMounted = useRef(false);

  // Component lifecycle logging
  useEffect(() => {
    componentMounted.current = true;
    logComponentMount('ProtectedRoute', {
      path: location.pathname,
      isAuthenticated,
      authState,
      canNavigate: canNavigateToProtectedRoute
    });

    return () => {
      componentMounted.current = false;
      logComponentUnmount('ProtectedRoute');
    };
  }, []);

  // Log state changes
  useEffect(() => {
    if (componentMounted.current) {
      debugLogger.log('ProtectedRoute', 'STATE_CHANGE', {
        path: location.pathname,
        authState,
        isAuthenticated,
        isLoading,
        hasUser: !!user,
        canNavigate: canNavigateToProtectedRoute,
        shouldRedirect: shouldRedirectToLogin,
        redirectAttempts: redirectAttempts.current
      });
    }
  }, [authState, isAuthenticated, isLoading, user, location.pathname]);

  // Prevent rapid navigation during initial load
  useEffect(() => {
    if (!isLoading && authState !== 'INITIALIZING' && authState !== 'CHECKING_TOKEN') {
      const timer = setTimeout(() => {
        setInitialLoad(false);
        debugLogger.log('ProtectedRoute', 'INITIAL_LOAD_COMPLETE', { authState });
      }, 300); // Reduced delay since state machine provides better control
      return () => clearTimeout(timer);
    }
  }, [isLoading, authState]);

  // Reset redirect attempts when authentication state changes
  useEffect(() => {
    if (authState === 'AUTHENTICATED' || authState === 'UNAUTHENTICATED') {
      redirectAttempts.current = 0;
      setHasRedirected(false);
      debugLogger.log('ProtectedRoute', 'REDIRECT_ATTEMPTS_RESET', { authState });
    }
  }, [authState]);

  // Show loading spinner while checking authentication or during initial load
  if (isLoading || initialLoad || authState === 'INITIALIZING' || authState === 'CHECKING_TOKEN') {
    const loadingMessage = authState === 'CHECKING_TOKEN' ? 'Validating credentials...' : 'Authenticating...';

    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        gap={2}
      >
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary">
          {loadingMessage}
        </Typography>
        {process.env.NODE_ENV === 'development' && (
          <Typography variant="caption" color="text.disabled">
            Auth State: {authState}
          </Typography>
        )}
      </Box>
    );
  }

  // Handle authentication errors
  if (authState === 'VALIDATION_ERROR') {
    debugLogger.error('ProtectedRoute', 'VALIDATION_ERROR_STATE');
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        gap={3}
      >
        <Alert severity="error">
          <Typography variant="h6" gutterBottom>
            Authentication Error
          </Typography>
          <Typography variant="body2">
            Unable to validate your session. Please log in again.
          </Typography>
        </Alert>
        <Button variant="contained" onClick={() => window.location.href = '/login'}>
          Go to Login
        </Button>
      </Box>
    );
  }

  // Use state machine logic for redirects
  if (shouldRedirectToLogin && !canNavigateToProtectedRoute) {
    if (redirectAttempts.current >= maxRedirectAttempts) {
      debugLogger.error('ProtectedRoute', 'MAX_REDIRECT_ATTEMPTS', {
        attempts: redirectAttempts.current,
        authState,
        path: location.pathname
      });

      return (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          minHeight="100vh"
          gap={3}
        >
          <Alert severity="warning">
            <Typography variant="h6" gutterBottom>
              Navigation Loop Detected
            </Typography>
            <Typography variant="body2">
              Too many redirect attempts. Please clear your browser data and try again.
            </Typography>
          </Alert>
          <Box display="flex" gap={2}>
            <Button variant="contained" onClick={() => {
              localStorage.clear();
              window.location.reload();
            }}>
              Clear Data & Reload
            </Button>
            <Button variant="outlined" onClick={() => window.location.href = '/login'}>
              Force Login
            </Button>
          </Box>
        </Box>
      );
    }

    if (!hasRedirected) {
      redirectAttempts.current += 1;
      setHasRedirected(true);

      logNavigation(location.pathname, '/login', 'AUTHENTICATION_REQUIRED', {
        attempt: redirectAttempts.current,
        authState
      });

      return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // Show loading while redirect is in progress
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        gap={2}
      >
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary">
          Redirecting to login...
        </Typography>
      </Box>
    );
  }

  // Render protected content only if fully authenticated
  if (canNavigateToProtectedRoute && authState === 'AUTHENTICATED') {
    debugLogger.log('ProtectedRoute', 'RENDER_CHILDREN', {
      path: location.pathname,
      authState,
      userEmail: user?.email
    });
    return <>{children}</>;
  }

  // Fallback loading state
  debugLogger.warn('ProtectedRoute', 'FALLBACK_LOADING', {
    authState,
    canNavigate: canNavigateToProtectedRoute,
    shouldRedirect: shouldRedirectToLogin
  });

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      gap={2}
    >
      <CircularProgress size={40} />
      <Typography variant="body2" color="text.secondary">
        Loading...
      </Typography>
      {process.env.NODE_ENV === 'development' && (
        <Typography variant="caption" color="text.disabled">
          Auth State: {authState} | Can Navigate: {canNavigateToProtectedRoute.toString()}
        </Typography>
      )}
    </Box>
  );
};

// Smart Root Redirect Component
export const SmartRootRedirect: React.FC = () => {
  const { authState, canNavigateToProtectedRoute, shouldRedirectToLogin } = useAuth();
  const [redirectAttempts, setRedirectAttempts] = useState(0);
  const maxAttempts = 3;

  useEffect(() => {
    logComponentMount('SmartRootRedirect', { authState });
    return () => logComponentUnmount('SmartRootRedirect');
  }, []);

  if (redirectAttempts >= maxAttempts) {
    debugLogger.error('SmartRootRedirect', 'MAX_ATTEMPTS_REACHED');
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        gap={2}
      >
        <Typography variant="h6" color="error">
          Navigation Error
        </Typography>
        <Button onClick={() => window.location.href = '/login'}>
          Go to Login
        </Button>
      </Box>
    );
  }

  if (canNavigateToProtectedRoute) {
    setRedirectAttempts(prev => prev + 1);
    logNavigation('/', '/dashboard', 'AUTHENTICATED_ROOT_REDIRECT');
    return <Navigate to="/dashboard" replace />;
  }

  if (shouldRedirectToLogin) {
    setRedirectAttempts(prev => prev + 1);
    logNavigation('/', '/login', 'UNAUTHENTICATED_ROOT_REDIRECT');
    return <Navigate to="/login" replace />;
  }

  // Loading state while determining redirect
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      gap={2}
    >
      <CircularProgress size={40} />
      <Typography variant="body2" color="text.secondary">
        Loading...
      </Typography>
    </Box>
  );
};

export default ProtectedRoute;

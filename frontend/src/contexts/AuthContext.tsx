import React, { createContext, useContext, useEffect, useRef, ReactNode, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { validateToken, clearError } from '../store/slices/authSlice';
import { User, Session } from '../types';
import { authStateMachine, AuthState } from '../utils/authStateMachine';
import { debugLogger, logAuthEvent, logComponentMount, logComponentUnmount } from '../utils/debugLogger';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
  authState: AuthState;
  canNavigateToProtectedRoute: boolean;
  shouldRedirectToLogin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const dispatch = useAppDispatch();
  const { user, session, isAuthenticated, isLoading, error, token } = useAppSelector(
    (state) => state.auth
  );

  const [authState, setAuthState] = useState<AuthState>(authStateMachine.getState());
  const initializationStarted = useRef(false);
  const validationInProgress = useRef(false);

  // Component lifecycle logging
  useEffect(() => {
    logComponentMount('AuthProvider', { hasToken: !!token, isAuthenticated });
    return () => logComponentUnmount('AuthProvider');
  }, []);

  // Subscribe to auth state machine changes
  useEffect(() => {
    const unsubscribe = authStateMachine.subscribe((newState, context) => {
      setAuthState(newState);
      logAuthEvent('STATE_MACHINE_TRANSITION', {
        state: newState,
        context,
        reduxState: { isAuthenticated, isLoading, user: !!user }
      });
    });

    return unsubscribe;
  }, [isAuthenticated, isLoading, user]);

  // Initialize authentication state machine once
  useEffect(() => {
    if (initializationStarted.current) {
      return;
    }
    initializationStarted.current = true;

    logAuthEvent('INITIALIZATION_START', { hasToken: !!token });

    // Initialize the state machine
    authStateMachine.send('INITIALIZE');

    // Check for existing token
    if (token) {
      logAuthEvent('TOKEN_FOUND', { tokenLength: token.length });
      authStateMachine.send('TOKEN_FOUND', { token });

      // Start validation if not already in progress
      if (!validationInProgress.current && !isAuthenticated && !isLoading) {
        validationInProgress.current = true;
        authStateMachine.send('VALIDATION_START');

        logAuthEvent('STARTING_TOKEN_VALIDATION');
        dispatch(validateToken())
          .unwrap()
          .then((result) => {
            validationInProgress.current = false;
            logAuthEvent('VALIDATION_SUCCESS', result);
            authStateMachine.send('VALIDATION_SUCCESS', { user: result.user });
          })
          .catch((error) => {
            validationInProgress.current = false;
            logAuthEvent('VALIDATION_FAILURE', error);
            authStateMachine.send('VALIDATION_FAILURE', { error: error.message });
          });
      }
    } else {
      logAuthEvent('TOKEN_NOT_FOUND');
      authStateMachine.send('TOKEN_NOT_FOUND');
    }
  }, []); // Run only once on mount

  // Handle Redux state changes and sync with state machine
  useEffect(() => {
    if (isAuthenticated && user && authState !== 'AUTHENTICATED') {
      logAuthEvent('REDUX_AUTH_SUCCESS', { user: user.email });
      authStateMachine.send('LOGIN_SUCCESS', { user, token });
    }
  }, [isAuthenticated, user, authState]);

  // Handle logout
  useEffect(() => {
    if (!token && authState === 'AUTHENTICATED') {
      logAuthEvent('LOGOUT_DETECTED');
      authStateMachine.send('LOGOUT');
      // Complete logout process
      setTimeout(() => {
        authStateMachine.send('RESET');
      }, 100);
    }
  }, [token, authState]);

  // Debug logging for state changes
  useEffect(() => {
    debugLogger.log('AuthProvider', 'STATE_UPDATE', {
      authState,
      isAuthenticated,
      isLoading,
      hasUser: !!user,
      hasToken: !!token,
      canNavigate: authStateMachine.canNavigateToProtectedRoute(),
      shouldRedirect: authStateMachine.shouldRedirectToLogin()
    });
  }, [authState, isAuthenticated, isLoading, user, token]);

  const handleClearError = () => {
    dispatch(clearError());
  };

  const contextValue: AuthContextType = {
    user,
    session,
    isAuthenticated,
    isLoading,
    error,
    clearError: handleClearError,
    authState,
    canNavigateToProtectedRoute: authStateMachine.canNavigateToProtectedRoute(),
    shouldRedirectToLogin: authStateMachine.shouldRedirectToLogin(),
  };

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

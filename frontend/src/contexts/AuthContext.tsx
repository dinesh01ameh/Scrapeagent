import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { validateToken, clearError } from '../store/slices/authSlice';
import { User, Session } from '../types';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
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

  useEffect(() => {
    // Validate token on app startup if token exists
    if (token && !isAuthenticated && !isLoading) {
      dispatch(validateToken());
    }
  }, [dispatch, token, isAuthenticated, isLoading]);

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

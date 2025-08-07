import React, { useEffect, useRef } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

interface SafeNavigateProps {
  to: string;
  replace?: boolean;
  state?: any;
}

/**
 * SafeNavigate component prevents infinite redirect loops by tracking navigation attempts
 */
const SafeNavigate: React.FC<SafeNavigateProps> = ({ to, replace = true, state }) => {
  const location = useLocation();
  const navigationAttempts = useRef(0);
  const lastNavigation = useRef<string>('');
  const maxAttempts = 3;

  useEffect(() => {
    // Reset attempts if we're navigating to a different path
    if (lastNavigation.current !== to) {
      navigationAttempts.current = 0;
      lastNavigation.current = to;
    }
  }, [to]);

  // Prevent infinite loops by checking navigation attempts
  if (navigationAttempts.current >= maxAttempts) {
    console.error(`SafeNavigate: Maximum navigation attempts (${maxAttempts}) reached for ${to}`);
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center', 
        minHeight: '100vh',
        gap: '16px'
      }}>
        <h2>Navigation Error</h2>
        <p>Unable to navigate to {to}. Please refresh the page.</p>
        <button onClick={() => window.location.reload()}>
          Refresh Page
        </button>
      </div>
    );
  }

  // Check if we're already at the target location
  if (location.pathname === to) {
    console.log(`SafeNavigate: Already at ${to}, skipping navigation`);
    return null;
  }

  navigationAttempts.current += 1;
  console.log(`SafeNavigate: Navigating to ${to} (attempt ${navigationAttempts.current})`);

  return <Navigate to={to} replace={replace} state={state} />;
};

export default SafeNavigate;
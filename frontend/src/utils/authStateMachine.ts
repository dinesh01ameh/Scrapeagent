/**
 * Authentication State Machine
 * Implements a robust state machine pattern to manage authentication flow
 * and eliminate race conditions between token validation and route protection
 */

export type AuthState = 
  | 'UNINITIALIZED'
  | 'INITIALIZING' 
  | 'CHECKING_TOKEN'
  | 'AUTHENTICATED'
  | 'UNAUTHENTICATED'
  | 'VALIDATION_ERROR'
  | 'LOGGING_OUT';

export type AuthEvent = 
  | 'INITIALIZE'
  | 'TOKEN_FOUND'
  | 'TOKEN_NOT_FOUND'
  | 'VALIDATION_START'
  | 'VALIDATION_SUCCESS'
  | 'VALIDATION_FAILURE'
  | 'LOGIN_SUCCESS'
  | 'LOGOUT'
  | 'RESET';

export interface AuthContext {
  token: string | null;
  user: any | null;
  error: string | null;
  lastValidation: number | null;
  validationInProgress: boolean;
}

export interface AuthStateTransition {
  from: AuthState;
  event: AuthEvent;
  to: AuthState;
  guard?: (context: AuthContext) => boolean;
  action?: (context: AuthContext) => Partial<AuthContext>;
}

class AuthStateMachine {
  private currentState: AuthState = 'UNINITIALIZED';
  private context: AuthContext = {
    token: null,
    user: null,
    error: null,
    lastValidation: null,
    validationInProgress: false
  };
  private listeners: Array<(state: AuthState, context: AuthContext) => void> = [];
  private transitions: AuthStateTransition[] = [
    // Initialization flow
    {
      from: 'UNINITIALIZED',
      event: 'INITIALIZE',
      to: 'INITIALIZING',
      action: (ctx) => ({ ...ctx, error: null })
    },
    {
      from: 'INITIALIZING',
      event: 'TOKEN_FOUND',
      to: 'CHECKING_TOKEN',
      action: (ctx) => ({ ...ctx, validationInProgress: true })
    },
    {
      from: 'INITIALIZING',
      event: 'TOKEN_NOT_FOUND',
      to: 'UNAUTHENTICATED',
      action: (ctx) => ({ ...ctx, token: null, user: null })
    },

    // Token validation flow
    {
      from: 'CHECKING_TOKEN',
      event: 'VALIDATION_START',
      to: 'CHECKING_TOKEN',
      action: (ctx) => ({ ...ctx, validationInProgress: true, error: null })
    },
    {
      from: 'CHECKING_TOKEN',
      event: 'VALIDATION_SUCCESS',
      to: 'AUTHENTICATED',
      action: (ctx) => ({ 
        ...ctx, 
        validationInProgress: false, 
        lastValidation: Date.now(),
        error: null 
      })
    },
    {
      from: 'CHECKING_TOKEN',
      event: 'VALIDATION_FAILURE',
      to: 'UNAUTHENTICATED',
      action: (ctx) => ({ 
        ...ctx, 
        validationInProgress: false, 
        token: null, 
        user: null,
        error: 'Token validation failed'
      })
    },

    // Login flow
    {
      from: 'UNAUTHENTICATED',
      event: 'LOGIN_SUCCESS',
      to: 'AUTHENTICATED',
      action: (ctx) => ({ 
        ...ctx, 
        error: null, 
        lastValidation: Date.now() 
      })
    },

    // Logout flow
    {
      from: 'AUTHENTICATED',
      event: 'LOGOUT',
      to: 'LOGGING_OUT',
      action: (ctx) => ({ ...ctx, validationInProgress: false })
    },
    {
      from: 'LOGGING_OUT',
      event: 'RESET',
      to: 'UNAUTHENTICATED',
      action: () => ({
        token: null,
        user: null,
        error: null,
        lastValidation: null,
        validationInProgress: false
      })
    },

    // Error recovery
    {
      from: 'VALIDATION_ERROR',
      event: 'RESET',
      to: 'UNAUTHENTICATED',
      action: () => ({
        token: null,
        user: null,
        error: null,
        lastValidation: null,
        validationInProgress: false
      })
    }
  ];

  constructor() {
    // Enable debugging in development
    if (process.env.NODE_ENV === 'development') {
      (window as any).__AUTH_STATE_MACHINE__ = this;
    }
  }

  public getState(): AuthState {
    return this.currentState;
  }

  public getContext(): AuthContext {
    return { ...this.context };
  }

  public isAuthenticated(): boolean {
    return this.currentState === 'AUTHENTICATED';
  }

  public isLoading(): boolean {
    return ['INITIALIZING', 'CHECKING_TOKEN', 'LOGGING_OUT'].includes(this.currentState);
  }

  public canNavigateToProtectedRoute(): boolean {
    return this.currentState === 'AUTHENTICATED';
  }

  public shouldRedirectToLogin(): boolean {
    return this.currentState === 'UNAUTHENTICATED';
  }

  public send(event: AuthEvent, payload?: Partial<AuthContext>): void {
    const transition = this.transitions.find(
      t => t.from === this.currentState && t.event === event
    );

    if (!transition) {
      console.warn(`No transition found for ${this.currentState} + ${event}`);
      return;
    }

    // Check guard condition if present
    if (transition.guard && !transition.guard(this.context)) {
      console.warn(`Guard condition failed for ${this.currentState} + ${event}`);
      return;
    }

    const previousState = this.currentState;
    const previousContext = { ...this.context };

    // Update context with payload
    if (payload) {
      this.context = { ...this.context, ...payload };
    }

    // Execute action if present
    if (transition.action) {
      this.context = { ...this.context, ...transition.action(this.context) };
    }

    // Transition to new state
    this.currentState = transition.to;

    // Log transition in development
    if (process.env.NODE_ENV === 'development') {
      console.log(
        `%c[AuthStateMachine] ${previousState} + ${event} → ${this.currentState}`,
        'color: #4CAF50; font-weight: bold',
        { context: this.context }
      );
    }

    // Notify listeners
    this.listeners.forEach(listener => {
      try {
        listener(this.currentState, this.context);
      } catch (error) {
        console.error('Error in auth state listener:', error);
      }
    });
  }

  public subscribe(listener: (state: AuthState, context: AuthContext) => void): () => void {
    this.listeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  public reset(): void {
    this.currentState = 'UNINITIALIZED';
    this.context = {
      token: null,
      user: null,
      error: null,
      lastValidation: null,
      validationInProgress: false
    };
    
    if (process.env.NODE_ENV === 'development') {
      console.log('%c[AuthStateMachine] RESET', 'color: #FF9800; font-weight: bold');
    }
  }

  // Debugging helpers
  public getAvailableEvents(): AuthEvent[] {
    return this.transitions
      .filter(t => t.from === this.currentState)
      .map(t => t.event);
  }

  public getTransitionHistory(): Array<{ state: AuthState; timestamp: number }> {
    // This would require implementing history tracking
    return [];
  }
}

// Create singleton instance
export const authStateMachine = new AuthStateMachine();

// Export for debugging
if (process.env.NODE_ENV === 'development') {
  (window as any).__DEBUG_AUTH_STATE_MACHINE__ = authStateMachine;
}
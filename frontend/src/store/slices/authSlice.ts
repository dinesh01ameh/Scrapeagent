import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { AuthState, User, Session, LoginForm, RegisterForm } from '../../types';
import { authService } from '../../services/authService';

const initialState: AuthState = {
  user: null,
  session: null,
  token: localStorage.getItem('token'),
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

// Async thunks
export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: LoginForm, { rejectWithValue }) => {
    try {
      console.log('Redux: Starting login process');
      const response = await authService.login(credentials);

      if (!response.access_token) {
        throw new Error('No access token received from server');
      }

      localStorage.setItem('token', response.access_token);
      console.log('Redux: Login successful, token stored');
      return response;
    } catch (error: any) {
      console.error('Redux: Login failed:', error);
      const errorMessage = error.message || 'Login failed. Please try again.';
      return rejectWithValue(errorMessage);
    }
  }
);

export const registerUser = createAsyncThunk(
  'auth/register',
  async (userData: RegisterForm, { rejectWithValue }) => {
    try {
      console.log('Redux: Starting registration process');
      const response = await authService.register(userData);

      if (!response.access_token) {
        throw new Error('No access token received from server');
      }

      localStorage.setItem('token', response.access_token);
      console.log('Redux: Registration successful, token stored');
      return response;
    } catch (error: any) {
      console.error('Redux: Registration failed:', error);
      const errorMessage = error.message || 'Registration failed. Please try again.';
      return rejectWithValue(errorMessage);
    }
  }
);

export const validateToken = createAsyncThunk(
  'auth/validateToken',
  async (_, { rejectWithValue, getState }) => {
    try {
      const state = getState() as { auth: AuthState };
      const token = state.auth.token;

      if (!token) {
        throw new Error('No token found');
      }

      const response = await authService.validateToken(token);
      return response;
    } catch (error: any) {
      localStorage.removeItem('token');
      return rejectWithValue(error.message || 'Token validation failed');
    }
  }
);

export const logoutUser = createAsyncThunk('auth/logout', async (_, { getState }) => {
  try {
    const state = getState() as { auth: AuthState };
    const token = state.auth.token;

    if (token) {
      await authService.logout(token);
    }
  } catch (error) {
    // Continue with logout even if API call fails
    console.error('Logout API call failed:', error);
  } finally {
    localStorage.removeItem('token');
  }
});

export const refreshToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { rejectWithValue, getState }) => {
    try {
      const state = getState() as { auth: AuthState };
      const currentToken = state.auth.token;

      if (!currentToken) {
        throw new Error('No token to refresh');
      }

      const response = await authService.refreshToken(currentToken);
      localStorage.setItem('token', response.access_token);
      return response;
    } catch (error: any) {
      localStorage.removeItem('token');
      return rejectWithValue(error.message || 'Token refresh failed');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
  },
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.session = null; // Backend doesn't return session in current implementation
        state.token = action.payload.access_token;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        state.isAuthenticated = false;
      });

    // Register
    builder
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.session = null; // Backend doesn't return session in current implementation
        state.token = action.payload.access_token;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        state.isAuthenticated = false;
      });

    // Validate Token
    builder
      .addCase(validateToken.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(validateToken.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.session = action.payload.session;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(validateToken.rejected, (state, action) => {
        state.isLoading = false;
        state.user = null;
        state.session = null;
        state.token = null;
        state.isAuthenticated = false;
        state.error = action.payload as string;
      });

    // Logout
    builder.addCase(logoutUser.fulfilled, (state) => {
      state.user = null;
      state.session = null;
      state.token = null;
      state.isAuthenticated = false;
      state.error = null;
      state.isLoading = false;
    });

    // Refresh Token
    builder
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.token = action.payload.access_token;
        state.user = action.payload.user;
        state.session = null; // Backend doesn't return session in current implementation
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(refreshToken.rejected, (state, action) => {
        state.user = null;
        state.session = null;
        state.token = null;
        state.isAuthenticated = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError, setLoading, updateUser } = authSlice.actions;
export default authSlice.reducer;

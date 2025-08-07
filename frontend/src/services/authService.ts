import { apiClient } from './apiClient';
import { User, Session, LoginForm, RegisterForm, AuthResponse } from '../types';

// Backend AuthResponse structure
interface BackendAuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

interface ValidationResponse {
  valid: boolean;
  user?: User;
  expires_at?: string;
}

class AuthService {
  // Login user
  async login(credentials: LoginForm): Promise<AuthResponse> {
    try {
      console.log('Attempting login for:', credentials.email);
      const response = await apiClient.post<BackendAuthResponse>('/auth/login', credentials);

      console.log('Raw login response:', response);

      // Check if response exists
      if (!response) {
        throw new Error('No response received from server');
      }

      // Check if response.data exists
      if (!response.data) {
        console.error('Response data is missing:', response);
        throw new Error('Invalid response from server - no data');
      }

      const backendData = response.data;
      console.log('Login response data:', backendData);

      // Validate required fields exist
      if (!backendData.access_token) {
        console.error('Missing access_token in response:', backendData);
        throw new Error('Server did not return authentication token');
      }

      if (!backendData.user) {
        console.error('Missing user data in response:', backendData);
        throw new Error('Server did not return user information');
      }

      console.log('Login successful for:', credentials.email);

      // Transform backend response to frontend format
      return {
        access_token: backendData.access_token,
        token_type: backendData.token_type || 'bearer',
        expires_in: backendData.expires_in || 3600,
        user: backendData.user,
      };
    } catch (error: any) {
      console.error('Login error details:', {
        message: error.message,
        response: error.response,
        stack: error.stack,
      });
      throw new Error(error.message || 'Login failed');
    }
  }

  // Register new user
  async register(userData: RegisterForm): Promise<AuthResponse> {
    try {
      // Only send fields that the backend expects
      const registrationData = {
        email: userData.email,
        password: userData.password,
        full_name: userData.full_name,
      };

      console.log('Attempting registration for:', userData.email);
      const response = await apiClient.post<BackendAuthResponse>(
        '/auth/register',
        registrationData
      );

      console.log('Raw registration response:', response);

      // Check if response exists
      if (!response) {
        throw new Error('No response received from server');
      }

      // Check if response.data exists
      if (!response.data) {
        console.error('Response data is missing:', response);
        throw new Error('Invalid response from server - no data');
      }

      const backendData = response.data;
      console.log('Registration response data:', backendData);

      // Validate required fields exist
      if (!backendData.access_token) {
        console.error('Missing access_token in response:', backendData);
        throw new Error('Server did not return authentication token');
      }

      if (!backendData.user) {
        console.error('Missing user data in response:', backendData);
        throw new Error('Server did not return user information');
      }

      console.log('Registration successful for:', userData.email);

      // Transform backend response to frontend format
      return {
        access_token: backendData.access_token,
        token_type: backendData.token_type || 'bearer',
        expires_in: backendData.expires_in || 3600,
        user: backendData.user,
      };
    } catch (error: any) {
      console.error('Registration error details:', {
        message: error.message,
        response: error.response,
        stack: error.stack,
      });
      throw new Error(error.message || 'Registration failed');
    }
  }

  // Validate existing token
  async validateToken(token: string): Promise<ValidationResponse> {
    try {
      const response = await apiClient.post<ValidationResponse>('/auth/validate', { token });
      const data = response.data!;
      
      if (!data.valid) {
        throw new Error('Token is invalid');
      }
      
      return data;
    } catch (error: any) {
      throw new Error(error.message || 'Token validation failed');
    }
  }

  // Refresh token
  async refreshToken(token: string): Promise<AuthResponse> {
    try {
      const response = await apiClient.post<BackendAuthResponse>('/auth/refresh', { token });
      const backendData = response.data!;

      // Transform backend response to frontend format
      return {
        access_token: backendData.access_token,
        token_type: backendData.token_type,
        expires_in: backendData.expires_in,
        user: backendData.user,
      };
    } catch (error: any) {
      throw new Error(error.message || 'Token refresh failed');
    }
  }

  // Logout user
  async logout(token: string): Promise<void> {
    try {
      await apiClient.post('/auth/logout', { token });
    } catch (error: any) {
      // Don't throw error for logout - continue with local cleanup
      console.error('Logout API call failed:', error.message);
    }
  }

  // Get current user profile
  async getProfile(): Promise<User> {
    try {
      const response = await apiClient.get<User>('/auth/profile');
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to get user profile');
    }
  }

  // Update user profile
  async updateProfile(userData: Partial<User>): Promise<User> {
    try {
      const response = await apiClient.patch<User>('/auth/profile', userData);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to update profile');
    }
  }

  // Change password
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    try {
      await apiClient.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
    } catch (error: any) {
      throw new Error(error.message || 'Failed to change password');
    }
  }

  // Regenerate API key
  async regenerateApiKey(): Promise<{ api_key: string }> {
    try {
      const response = await apiClient.post<{ api_key: string }>('/auth/regenerate-api-key');
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to regenerate API key');
    }
  }

  // Get user sessions
  async getSessions(): Promise<Session[]> {
    try {
      const response = await apiClient.get<Session[]>('/auth/sessions');
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to get sessions');
    }
  }

  // Deactivate session
  async deactivateSession(sessionId: string): Promise<void> {
    try {
      await apiClient.delete(`/auth/sessions/${sessionId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to deactivate session');
    }
  }

  // Request password reset
  async requestPasswordReset(email: string): Promise<void> {
    try {
      await apiClient.post('/auth/request-password-reset', { email });
    } catch (error: any) {
      throw new Error(error.message || 'Failed to request password reset');
    }
  }

  // Reset password with token
  async resetPassword(token: string, newPassword: string): Promise<void> {
    try {
      await apiClient.post('/auth/reset-password', {
        token,
        new_password: newPassword,
      });
    } catch (error: any) {
      throw new Error(error.message || 'Failed to reset password');
    }
  }

  // Verify email
  async verifyEmail(token: string): Promise<void> {
    try {
      await apiClient.post('/auth/verify-email', { token });
    } catch (error: any) {
      throw new Error(error.message || 'Failed to verify email');
    }
  }

  // Resend verification email
  async resendVerificationEmail(): Promise<void> {
    try {
      await apiClient.post('/auth/resend-verification');
    } catch (error: any) {
      throw new Error(error.message || 'Failed to resend verification email');
    }
  }

  // Check if user is authenticated (client-side check)
  isAuthenticated(): boolean {
    const token = localStorage.getItem('token');
    return !!token;
  }

  // Get stored token
  getToken(): string | null {
    return localStorage.getItem('token');
  }

  // Clear stored authentication data
  clearAuth(): void {
    localStorage.removeItem('token');
  }
}

export const authService = new AuthService();
export default authService;

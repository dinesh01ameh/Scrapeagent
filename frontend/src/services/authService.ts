import { apiClient } from './apiClient';
import { User, Session, LoginForm, RegisterForm } from '../types';

interface AuthResponse {
  user: User;
  session: Session;
  token: string;
}

interface ValidationResponse {
  user: User;
  session: Session;
}

class AuthService {
  // Login user
  async login(credentials: LoginForm): Promise<AuthResponse> {
    try {
      const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Login failed');
    }
  }

  // Register new user
  async register(userData: RegisterForm): Promise<AuthResponse> {
    try {
      // Remove confirmPassword before sending to API
      const { confirmPassword, ...registrationData } = userData;

      const response = await apiClient.post<AuthResponse>('/auth/register', registrationData);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Registration failed');
    }
  }

  // Validate existing token
  async validateToken(token: string): Promise<ValidationResponse> {
    try {
      const response = await apiClient.post<ValidationResponse>('/auth/validate', { token });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Token validation failed');
    }
  }

  // Refresh token
  async refreshToken(token: string): Promise<AuthResponse> {
    try {
      const response = await apiClient.post<AuthResponse>('/auth/refresh', { token });
      return response.data!;
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

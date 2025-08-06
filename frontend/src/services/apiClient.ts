import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse } from '../types';

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8601';

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log successful responses for debugging
        console.log('API Success:', {
          status: response.status,
          url: response.config?.url,
          method: response.config?.method,
          data: response.data,
        });
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 errors (unauthorized)
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          // Try to refresh token
          try {
            const token = localStorage.getItem('token');
            if (token) {
              const refreshResponse = await this.post('/auth/refresh', { token });
              const newToken = refreshResponse.data?.token;

              if (newToken) {
                localStorage.setItem('token', newToken);
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return this.client(originalRequest);
              }
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            localStorage.removeItem('token');
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        // Handle network errors
        if (!error.response) {
          return Promise.reject(new Error('Network error. Please check your connection.'));
        }

        // Handle API errors with improved messaging
        const status = error.response.status;
        const errorData = error.response.data;

        console.error('API Error:', {
          status,
          errorData,
          url: error.config?.url,
          method: error.config?.method,
        });

        // Extract error message from FastAPI response format
        let errorMessage = 'An error occurred';

        if (errorData?.detail) {
          // FastAPI HTTPException format
          errorMessage = errorData.detail;
        } else if (errorData?.message) {
          // Custom error format
          errorMessage = errorData.message;
        } else if (errorData?.error) {
          // Alternative error format
          errorMessage = errorData.error;
        } else if (error.message) {
          // Fallback to axios error message
          errorMessage = error.message;
        }

        // Provide specific user-friendly messages for common scenarios
        if (status === 401) {
          if (errorMessage.includes('Invalid email or password')) {
            errorMessage =
              'Invalid email or password. If you forgot your password, please try the "Forgot Password" option.';
          } else {
            errorMessage = 'Authentication failed. Please check your credentials.';
          }
        } else if (status === 400) {
          if (errorMessage.includes('Email already registered')) {
            errorMessage =
              'This email is already registered. Please try logging in instead. If you forgot your password, use "Forgot Password".';
          } else if (errorMessage.includes('validation')) {
            errorMessage = 'Please check your input and try again.';
          }
        } else if (status === 500) {
          errorMessage = 'Server error. Please try again later.';
        }

        return Promise.reject(new Error(errorMessage));
      }
    );
  }

  // Generic request method
  private async request<T = any>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.request<T>(config);

      // Return the response in ApiResponse format
      return {
        data: response.data,
        status: response.status,
        message: 'Success',
      } as ApiResponse<T>;
    } catch (error: any) {
      throw error;
    }
  }

  // HTTP methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'GET', url });
  }

  async post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'POST', url, data });
  }

  async put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'PUT', url, data });
  }

  async patch<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'PATCH', url, data });
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'DELETE', url });
  }

  // File upload method
  async uploadFile<T = any>(
    url: string,
    file: File,
    onUploadProgress?: (progressEvent: any) => void
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<T>({
      method: 'POST',
      url,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
  }

  // Download file method
  async downloadFile(url: string, filename?: string): Promise<void> {
    try {
      const response = await this.client.get(url, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');

      link.href = downloadUrl;
      link.download = filename || 'download';
      document.body.appendChild(link);
      link.click();

      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error: any) {
      throw new Error(`Download failed: ${error.message}`);
    }
  }

  // Health check method
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.get('/health');
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  // Get base URL
  getBaseURL(): string {
    return this.baseURL;
  }

  // Update base URL
  setBaseURL(url: string): void {
    this.baseURL = url;
    this.client.defaults.baseURL = url;
  }

  // Set default headers
  setDefaultHeader(key: string, value: string): void {
    this.client.defaults.headers.common[key] = value;
  }

  // Remove default header
  removeDefaultHeader(key: string): void {
    delete this.client.defaults.headers.common[key];
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();
export default apiClient;

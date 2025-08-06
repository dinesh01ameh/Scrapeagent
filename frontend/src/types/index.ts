// User and Authentication Types
export interface User {
  id: string;
  email: string;
  username?: string;
  full_name?: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  subscription_tier: string;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
  metadata?: Record<string, any>;
}

export interface Session {
  id: string;
  user_id: string;
  session_token: string;
  name: string;
  description?: string;
  is_active: boolean;
  expires_at?: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface AuthState {
  user: User | null;
  session: Session | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Project Types
export interface Project {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  status: 'active' | 'inactive' | 'archived';
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

// Scraping Job Types
export interface ScrapingJob {
  id: string;
  user_id: string;
  project_id?: string;
  session_id?: string;
  name?: string;
  url: string;
  query?: string;
  content_type?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  priority: number;
  scheduled_at?: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  retry_count: number;
  max_retries: number;
  processing_time_seconds?: number;
  extraction_config: Record<string, any>;
  proxy_config: Record<string, any>;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

// Scraped Content Types
export interface ScrapedContent {
  id: string;
  job_id: string;
  user_id: string;
  url: string;
  content_type?: string;
  title?: string;
  raw_content?: string;
  processed_content?: Record<string, any>;
  extracted_data?: Record<string, any>;
  llm_analysis?: Record<string, any>;
  content_hash: string;
  file_size?: number;
  language?: string;
  sentiment_score?: number;
  quality_score?: number;
  is_duplicate: boolean;
  duplicate_of?: string;
  scraped_at: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

// API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

// Dashboard Statistics
export interface DashboardStats {
  user: User;
  statistics: {
    total_projects: number;
    total_jobs: number;
    completed_jobs: number;
    success_rate: number;
    total_content: number;
  };
  recent_activity: {
    jobs: ScrapingJob[];
    content: ScrapedContent[];
  };
}

// Form Types
export interface LoginForm {
  email: string;
  password: string;
}

export interface RegisterForm {
  email: string;
  password: string;
  confirmPassword: string;
  username?: string;
  full_name: string;
  terms?: boolean;
}

export interface ProjectForm {
  name: string;
  description?: string;
  settings?: Record<string, any>;
}

export interface JobForm {
  name?: string;
  url: string;
  query?: string;
  project_id?: string;
  priority?: number;
  scheduled_at?: string;
  extraction_config?: Record<string, any>;
  proxy_config?: Record<string, any>;
}

// UI State Types
export interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  loading: boolean;
  notifications: Notification[];
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// Proxy Types
export interface ProxyStats {
  total_proxies: number;
  healthy_proxies: number;
  unhealthy_proxies: number;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  average_response_time: number;
  overall_success_rate: number;
  pools: Record<
    string,
    {
      count: number;
      healthy: number;
      unhealthy: number;
      total_requests: number;
      successful_requests: number;
      failed_requests: number;
      average_response_time: number;
      success_rate: number;
    }
  >;
}

// System Health Types
export interface SystemHealth {
  postgres: {
    status: string;
    latency_ms?: number;
    pool_size?: number;
    pool_max_size?: number;
    pool_min_size?: number;
    error?: string;
  };
  supabase: {
    status: string;
    latency_ms?: number;
    error?: string;
  };
  overall: string;
}

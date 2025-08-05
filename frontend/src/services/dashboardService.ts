import { apiClient } from './apiClient';
import { DashboardStats, SystemHealth, ProxyStats } from '@/types';

class DashboardService {
  // Get user dashboard data
  async getDashboardData(): Promise<DashboardStats> {
    try {
      const response = await apiClient.get<DashboardStats>('/dashboard');
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch dashboard data');
    }
  }

  // Get system health status
  async getSystemHealth(): Promise<SystemHealth> {
    try {
      const response = await apiClient.get<SystemHealth>('/health');
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch system health');
    }
  }

  // Get proxy statistics
  async getProxyStats(): Promise<ProxyStats> {
    try {
      const response = await apiClient.get<ProxyStats>('/admin/proxy/statistics');
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch proxy statistics');
    }
  }

  // Get usage analytics
  async getUsageAnalytics(params: {
    period?: 'day' | 'week' | 'month' | 'year';
    start_date?: string;
    end_date?: string;
  } = {}): Promise<{
    jobs_over_time: Array<{ date: string; count: number; success_count: number; failed_count: number }>;
    content_over_time: Array<{ date: string; count: number; size_bytes: number }>;
    top_domains: Array<{ domain: string; count: number; success_rate: number }>;
    content_types: Array<{ type: string; count: number; percentage: number }>;
    performance_metrics: {
      avg_processing_time: number;
      avg_response_time: number;
      success_rate: number;
      total_requests: number;
    };
  }> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.period) queryParams.append('period', params.period);
      if (params.start_date) queryParams.append('start_date', params.start_date);
      if (params.end_date) queryParams.append('end_date', params.end_date);

      const response = await apiClient.get(`/analytics/usage?${queryParams.toString()}`);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch usage analytics');
    }
  }

  // Get recent activity
  async getRecentActivity(limit: number = 20): Promise<Array<{
    id: string;
    type: 'job_created' | 'job_completed' | 'job_failed' | 'project_created' | 'content_extracted';
    title: string;
    description: string;
    timestamp: string;
    metadata?: Record<string, any>;
  }>> {
    try {
      const response = await apiClient.get(`/dashboard/activity?limit=${limit}`);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch recent activity');
    }
  }

  // Get performance metrics
  async getPerformanceMetrics(params: {
    period?: 'hour' | 'day' | 'week';
    hours?: number;
  } = {}): Promise<{
    response_times: Array<{ timestamp: string; avg_time: number; p95_time: number; p99_time: number }>;
    throughput: Array<{ timestamp: string; requests_per_second: number }>;
    error_rates: Array<{ timestamp: string; error_rate: number; total_requests: number }>;
    resource_usage: Array<{ timestamp: string; cpu_percent: number; memory_percent: number }>;
  }> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.period) queryParams.append('period', params.period);
      if (params.hours) queryParams.append('hours', params.hours.toString());

      const response = await apiClient.get(`/metrics/performance?${queryParams.toString()}`);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch performance metrics');
    }
  }

  // Get quota and usage limits
  async getQuotaUsage(): Promise<{
    current_period: {
      start_date: string;
      end_date: string;
    };
    limits: {
      max_jobs_per_month: number;
      max_content_size_gb: number;
      max_concurrent_jobs: number;
      max_api_calls_per_hour: number;
    };
    usage: {
      jobs_this_month: number;
      content_size_gb: number;
      concurrent_jobs: number;
      api_calls_this_hour: number;
    };
    percentages: {
      jobs_used: number;
      storage_used: number;
      concurrent_used: number;
      api_calls_used: number;
    };
  }> {
    try {
      const response = await apiClient.get('/dashboard/quota');
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch quota usage');
    }
  }

  // Get alerts and notifications
  async getAlerts(): Promise<Array<{
    id: string;
    type: 'info' | 'warning' | 'error' | 'success';
    title: string;
    message: string;
    timestamp: string;
    read: boolean;
    action_url?: string;
    action_text?: string;
  }>> {
    try {
      const response = await apiClient.get('/dashboard/alerts');
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch alerts');
    }
  }

  // Mark alert as read
  async markAlertRead(alertId: string): Promise<void> {
    try {
      await apiClient.patch(`/dashboard/alerts/${alertId}`, { read: true });
    } catch (error: any) {
      throw new Error(error.message || 'Failed to mark alert as read');
    }
  }

  // Get system status
  async getSystemStatus(): Promise<{
    status: 'operational' | 'degraded' | 'maintenance' | 'outage';
    components: Array<{
      name: string;
      status: 'operational' | 'degraded' | 'outage';
      response_time?: number;
      uptime_percentage?: number;
    }>;
    incidents: Array<{
      id: string;
      title: string;
      status: 'investigating' | 'identified' | 'monitoring' | 'resolved';
      created_at: string;
      updated_at: string;
    }>;
  }> {
    try {
      const response = await apiClient.get('/status');
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch system status');
    }
  }

  // Export dashboard data
  async exportDashboardData(format: 'json' | 'csv' = 'json'): Promise<void> {
    try {
      const filename = `dashboard-export-${new Date().toISOString().split('T')[0]}.${format}`;
      await apiClient.downloadFile(`/dashboard/export?format=${format}`, filename);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to export dashboard data');
    }
  }
}

export const dashboardService = new DashboardService();
export default dashboardService;

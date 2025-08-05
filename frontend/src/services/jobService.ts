import { apiClient } from './apiClient';
import { ScrapingJob, JobForm, PaginatedResponse, ScrapedContent } from '@/types';

class JobService {
  // Get all jobs with pagination and filtering
  async getJobs(params: {
    page?: number;
    limit?: number;
    status?: string;
    project_id?: string;
    search?: string;
  } = {}): Promise<PaginatedResponse<ScrapingJob>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', params.limit.toString());
      if (params.status) queryParams.append('status', params.status);
      if (params.project_id) queryParams.append('project_id', params.project_id);
      if (params.search) queryParams.append('search', params.search);

      const response = await apiClient.get<PaginatedResponse<ScrapingJob>>(
        `/jobs?${queryParams.toString()}`
      );
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch jobs');
    }
  }

  // Get single job by ID
  async getJob(jobId: string): Promise<ScrapingJob> {
    try {
      const response = await apiClient.get<ScrapingJob>(`/jobs/${jobId}`);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch job');
    }
  }

  // Create new job
  async createJob(jobData: JobForm): Promise<ScrapingJob> {
    try {
      const response = await apiClient.post<ScrapingJob>('/jobs', jobData);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to create job');
    }
  }

  // Update existing job
  async updateJob(jobId: string, jobData: Partial<JobForm>): Promise<ScrapingJob> {
    try {
      const response = await apiClient.patch<ScrapingJob>(`/jobs/${jobId}`, jobData);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to update job');
    }
  }

  // Delete job
  async deleteJob(jobId: string): Promise<void> {
    try {
      await apiClient.delete(`/jobs/${jobId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to delete job');
    }
  }

  // Cancel running job
  async cancelJob(jobId: string): Promise<ScrapingJob> {
    try {
      const response = await apiClient.post<ScrapingJob>(`/jobs/${jobId}/cancel`);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to cancel job');
    }
  }

  // Retry failed job
  async retryJob(jobId: string): Promise<ScrapingJob> {
    try {
      const response = await apiClient.post<ScrapingJob>(`/jobs/${jobId}/retry`);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to retry job');
    }
  }

  // Get job results/content
  async getJobResults(jobId: string, params: {
    page?: number;
    limit?: number;
  } = {}): Promise<PaginatedResponse<ScrapedContent>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', params.limit.toString());

      const response = await apiClient.get<PaginatedResponse<ScrapedContent>>(
        `/jobs/${jobId}/results?${queryParams.toString()}`
      );
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch job results');
    }
  }

  // Get job logs
  async getJobLogs(jobId: string): Promise<{
    logs: Array<{
      timestamp: string;
      level: string;
      message: string;
      component?: string;
    }>;
  }> {
    try {
      const response = await apiClient.get(`/jobs/${jobId}/logs`);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch job logs');
    }
  }

  // Start job immediately
  async startJob(jobId: string): Promise<ScrapingJob> {
    try {
      const response = await apiClient.post<ScrapingJob>(`/jobs/${jobId}/start`);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to start job');
    }
  }

  // Schedule job for later execution
  async scheduleJob(jobId: string, scheduledAt: string): Promise<ScrapingJob> {
    try {
      const response = await apiClient.post<ScrapingJob>(`/jobs/${jobId}/schedule`, {
        scheduled_at: scheduledAt
      });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to schedule job');
    }
  }

  // Duplicate job
  async duplicateJob(jobId: string, newName?: string): Promise<ScrapingJob> {
    try {
      const response = await apiClient.post<ScrapingJob>(`/jobs/${jobId}/duplicate`, {
        name: newName
      });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to duplicate job');
    }
  }

  // Export job results
  async exportJobResults(jobId: string, format: 'json' | 'csv' | 'xlsx' = 'json'): Promise<void> {
    try {
      const filename = `job-${jobId}-results.${format}`;
      await apiClient.downloadFile(`/jobs/${jobId}/export?format=${format}`, filename);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to export job results');
    }
  }

  // Get job statistics
  async getJobStats(jobId: string): Promise<{
    total_content: number;
    processing_time: number;
    success_rate: number;
    errors_count: number;
    content_types: Record<string, number>;
    extraction_stats: Record<string, any>;
  }> {
    try {
      const response = await apiClient.get(`/jobs/${jobId}/stats`);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch job statistics');
    }
  }

  // Create job with natural language query
  async createJobFromNaturalLanguage(query: string, projectId?: string): Promise<{
    job: ScrapingJob;
    interpretation: {
      intent: string;
      entities: Record<string, any>;
      confidence: number;
      suggested_config: Record<string, any>;
    };
  }> {
    try {
      const response = await apiClient.post('/jobs/from-natural-language', {
        query,
        project_id: projectId
      });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to create job from natural language');
    }
  }

  // Get job templates
  async getJobTemplates(): Promise<{
    id: string;
    name: string;
    description: string;
    config: JobForm;
    category: string;
  }[]> {
    try {
      const response = await apiClient.get('/jobs/templates');
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch job templates');
    }
  }

  // Create job from template
  async createFromTemplate(templateId: string, jobData: {
    name?: string;
    url: string;
    project_id?: string;
  }): Promise<ScrapingJob> {
    try {
      const response = await apiClient.post<ScrapingJob>('/jobs/from-template', {
        template_id: templateId,
        ...jobData
      });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to create job from template');
    }
  }

  // Bulk operations
  async bulkDeleteJobs(jobIds: string[]): Promise<{ deleted_count: number }> {
    try {
      const response = await apiClient.post('/jobs/bulk-delete', { job_ids: jobIds });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to delete jobs');
    }
  }

  async bulkCancelJobs(jobIds: string[]): Promise<{ cancelled_count: number }> {
    try {
      const response = await apiClient.post('/jobs/bulk-cancel', { job_ids: jobIds });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to cancel jobs');
    }
  }

  async bulkRetryJobs(jobIds: string[]): Promise<{ retried_count: number }> {
    try {
      const response = await apiClient.post('/jobs/bulk-retry', { job_ids: jobIds });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to retry jobs');
    }
  }
}

export const jobService = new JobService();
export default jobService;

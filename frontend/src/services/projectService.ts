import { apiClient } from './apiClient';
import { Project, ProjectForm, PaginatedResponse } from '@/types';

class ProjectService {
  // Get all projects with pagination and filtering
  async getProjects(params: {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
  } = {}): Promise<PaginatedResponse<Project>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', params.limit.toString());
      if (params.search) queryParams.append('search', params.search);
      if (params.status) queryParams.append('status', params.status);

      const response = await apiClient.get<PaginatedResponse<Project>>(
        `/projects?${queryParams.toString()}`
      );
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch projects');
    }
  }

  // Get single project by ID
  async getProject(projectId: string): Promise<Project> {
    try {
      const response = await apiClient.get<Project>(`/projects/${projectId}`);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch project');
    }
  }

  // Create new project
  async createProject(projectData: ProjectForm): Promise<Project> {
    try {
      const response = await apiClient.post<Project>('/projects', projectData);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to create project');
    }
  }

  // Update existing project
  async updateProject(projectId: string, projectData: Partial<ProjectForm>): Promise<Project> {
    try {
      const response = await apiClient.patch<Project>(`/projects/${projectId}`, projectData);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to update project');
    }
  }

  // Delete project
  async deleteProject(projectId: string): Promise<void> {
    try {
      await apiClient.delete(`/projects/${projectId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to delete project');
    }
  }

  // Get project statistics
  async getProjectStats(projectId: string): Promise<{
    total_jobs: number;
    completed_jobs: number;
    failed_jobs: number;
    pending_jobs: number;
    total_content: number;
    success_rate: number;
    avg_processing_time: number;
  }> {
    try {
      const response = await apiClient.get(`/projects/${projectId}/stats`);
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch project statistics');
    }
  }

  // Archive project
  async archiveProject(projectId: string): Promise<Project> {
    try {
      const response = await apiClient.patch<Project>(`/projects/${projectId}`, {
        status: 'archived'
      });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to archive project');
    }
  }

  // Restore archived project
  async restoreProject(projectId: string): Promise<Project> {
    try {
      const response = await apiClient.patch<Project>(`/projects/${projectId}`, {
        status: 'active'
      });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to restore project');
    }
  }

  // Duplicate project
  async duplicateProject(projectId: string, newName: string): Promise<Project> {
    try {
      const response = await apiClient.post<Project>(`/projects/${projectId}/duplicate`, {
        name: newName
      });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to duplicate project');
    }
  }

  // Export project data
  async exportProject(projectId: string, format: 'json' | 'csv' = 'json'): Promise<void> {
    try {
      const filename = `project-${projectId}-export.${format}`;
      await apiClient.downloadFile(`/projects/${projectId}/export?format=${format}`, filename);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to export project');
    }
  }

  // Get project activity log
  async getProjectActivity(projectId: string, params: {
    page?: number;
    limit?: number;
  } = {}): Promise<PaginatedResponse<{
    id: string;
    action: string;
    description: string;
    timestamp: string;
    user_id: string;
    metadata?: Record<string, any>;
  }>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', params.limit.toString());

      const response = await apiClient.get(
        `/projects/${projectId}/activity?${queryParams.toString()}`
      );
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch project activity');
    }
  }

  // Update project settings
  async updateProjectSettings(projectId: string, settings: Record<string, any>): Promise<Project> {
    try {
      const response = await apiClient.patch<Project>(`/projects/${projectId}/settings`, {
        settings
      });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to update project settings');
    }
  }

  // Get project templates
  async getProjectTemplates(): Promise<{
    id: string;
    name: string;
    description: string;
    settings: Record<string, any>;
    category: string;
  }[]> {
    try {
      const response = await apiClient.get('/projects/templates');
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch project templates');
    }
  }

  // Create project from template
  async createFromTemplate(templateId: string, projectData: {
    name: string;
    description?: string;
  }): Promise<Project> {
    try {
      const response = await apiClient.post<Project>('/projects/from-template', {
        template_id: templateId,
        ...projectData
      });
      return response.data!;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to create project from template');
    }
  }
}

export const projectService = new ProjectService();
export default projectService;

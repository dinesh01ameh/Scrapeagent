import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Add,
  MoreVert,
  Edit,
  Delete,
  Archive,
  Unarchive,
  FileCopy,
  FolderOpen,
  Schedule,
} from '@mui/icons-material';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useAppDispatch } from '../../store';
import {
  fetchProjects,
  createProject,
  updateProject,
  deleteProject,
} from '../../store/slices/projectsSlice';
import { projectService } from '../../services/projectService';
import { Project, ProjectForm } from '../../types';
import { toast } from 'react-hot-toast';

// Validation schema
const projectSchema = yup.object({
  name: yup
    .string()
    .required('Project name is required')
    .min(3, 'Project name must be at least 3 characters')
    .max(100, 'Project name must be less than 100 characters'),
  description: yup.string().max(500, 'Description must be less than 500 characters'),
});

const ProjectsPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuProject, setMenuProject] = useState<Project | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProjectForm>({
    resolver: yupResolver(projectSchema),
  });

  // Fetch projects
  const {
    data: projectsData,
    isLoading,
    error,
    refetch,
  } = useQuery('projects', () => projectService.getProjects(), {
    refetchOnWindowFocus: false,
  });

  // Create project mutation
  const createMutation = useMutation(projectService.createProject, {
    onSuccess: () => {
      queryClient.invalidateQueries('projects');
      toast.success('Project created successfully!');
      setCreateDialogOpen(false);
      reset();
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to create project');
    },
  });

  // Update project mutation
  const updateMutation = useMutation(
    ({ id, data }: { id: string; data: Partial<ProjectForm> }) =>
      projectService.updateProject(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('projects');
        toast.success('Project updated successfully!');
        setEditDialogOpen(false);
        reset();
        setSelectedProject(null);
      },
      onError: (error: any) => {
        toast.error(error.message || 'Failed to update project');
      },
    }
  );

  // Delete project mutation
  const deleteMutation = useMutation(projectService.deleteProject, {
    onSuccess: () => {
      queryClient.invalidateQueries('projects');
      toast.success('Project deleted successfully!');
      setDeleteDialogOpen(false);
      setSelectedProject(null);
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to delete project');
    },
  });

  // Archive project mutation
  const archiveMutation = useMutation(projectService.archiveProject, {
    onSuccess: () => {
      queryClient.invalidateQueries('projects');
      toast.success('Project archived successfully!');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to archive project');
    },
  });

  // Restore project mutation
  const restoreMutation = useMutation(projectService.restoreProject, {
    onSuccess: () => {
      queryClient.invalidateQueries('projects');
      toast.success('Project restored successfully!');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to restore project');
    },
  });

  useEffect(() => {
    // Check if we should open create dialog from URL params
    if (searchParams.get('action') === 'create') {
      setCreateDialogOpen(true);
      // Remove the action param
      setSearchParams({});
    }
  }, [searchParams, setSearchParams]);

  const handleCreateProject = () => {
    setCreateDialogOpen(true);
  };

  const handleEditProject = (project: Project) => {
    setSelectedProject(project);
    reset({
      name: project.name,
      description: project.description || '',
    });
    setEditDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteProject = (project: Project) => {
    setSelectedProject(project);
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleArchiveProject = (project: Project) => {
    if (project.status === 'archived') {
      restoreMutation.mutate(project.id);
    } else {
      archiveMutation.mutate(project.id);
    }
    handleMenuClose();
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, project: Project) => {
    setAnchorEl(event.currentTarget);
    setMenuProject(project);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuProject(null);
  };

  const onCreateSubmit = (data: ProjectForm) => {
    createMutation.mutate(data);
  };

  const onEditSubmit = (data: ProjectForm) => {
    if (selectedProject) {
      updateMutation.mutate({ id: selectedProject.id, data });
    }
  };

  const confirmDelete = () => {
    if (selectedProject) {
      deleteMutation.mutate(selectedProject.id);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'warning';
      case 'archived':
        return 'default';
      default:
        return 'default';
    }
  };

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Projects
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Projects
        </Typography>
        <Alert severity="error">Failed to load projects. Please try again.</Alert>
      </Box>
    );
  }

  const projects = projectsData?.data || [];

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Projects
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Organize your scraping tasks into projects for better management.
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={handleCreateProject} size="large">
          New Project
        </Button>
      </Box>

      {/* Projects Grid */}
      {projects.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <FolderOpen sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No projects yet
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Create your first project to start organizing your scraping tasks.
            </Typography>
            <Button variant="contained" startIcon={<Add />} onClick={handleCreateProject}>
              Create Project
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {projects.map((project) => (
            <Grid item xs={12} sm={6} md={4} key={project.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Typography variant="h6" noWrap>
                      {project.name}
                    </Typography>
                    <IconButton size="small" onClick={(e) => handleMenuOpen(e, project)}>
                      <MoreVert />
                    </IconButton>
                  </Box>

                  <Typography variant="body2" color="text.secondary" mb={2}>
                    {project.description || 'No description provided'}
                  </Typography>

                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <Chip
                      label={project.status}
                      size="small"
                      color={getStatusColor(project.status) as any}
                      variant="outlined"
                    />
                    <Typography variant="caption" color="text.secondary">
                      Created {new Date(project.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                </CardContent>

                <CardActions>
                  <Button size="small" startIcon={<Schedule />}>
                    View Jobs
                  </Button>
                  <Button
                    size="small"
                    startIcon={<Edit />}
                    onClick={() => handleEditProject(project)}
                  >
                    Edit
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Project Menu */}
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        <MenuItem onClick={() => menuProject && handleEditProject(menuProject)}>
          <Edit fontSize="small" sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={() => menuProject && handleArchiveProject(menuProject)}>
          {menuProject?.status === 'archived' ? (
            <>
              <Unarchive fontSize="small" sx={{ mr: 1 }} />
              Restore
            </>
          ) : (
            <>
              <Archive fontSize="small" sx={{ mr: 1 }} />
              Archive
            </>
          )}
        </MenuItem>
        <MenuItem onClick={() => menuProject && handleDeleteProject(menuProject)}>
          <Delete fontSize="small" sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Create Project Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Project</DialogTitle>
        <form onSubmit={handleSubmit(onCreateSubmit)}>
          <DialogContent>
            <TextField
              {...register('name')}
              fullWidth
              label="Project Name"
              margin="normal"
              error={!!errors.name}
              helperText={errors.name?.message}
              autoFocus
            />
            <TextField
              {...register('description')}
              fullWidth
              label="Description (optional)"
              margin="normal"
              multiline
              rows={3}
              error={!!errors.description}
              helperText={errors.description?.message}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={isSubmitting || createMutation.isLoading}
            >
              {createMutation.isLoading ? 'Creating...' : 'Create Project'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Edit Project Dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Edit Project</DialogTitle>
        <form onSubmit={handleSubmit(onEditSubmit)}>
          <DialogContent>
            <TextField
              {...register('name')}
              fullWidth
              label="Project Name"
              margin="normal"
              error={!!errors.name}
              helperText={errors.name?.message}
              autoFocus
            />
            <TextField
              {...register('description')}
              fullWidth
              label="Description (optional)"
              margin="normal"
              multiline
              rows={3}
              error={!!errors.description}
              helperText={errors.description?.message}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={isSubmitting || updateMutation.isLoading}
            >
              {updateMutation.isLoading ? 'Updating...' : 'Update Project'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Project</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{selectedProject?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={confirmDelete}
            color="error"
            variant="contained"
            disabled={deleteMutation.isLoading}
          >
            {deleteMutation.isLoading ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProjectsPage;

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { ScrapingJob, JobForm } from '../../types';
import { jobService } from '../../services/jobService';

interface JobsState {
  jobs: ScrapingJob[];
  currentJob: ScrapingJob | null;
  loading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
  hasMore: boolean;
  filters: {
    status?: string;
    project_id?: string;
    search?: string;
  };
}

const initialState: JobsState = {
  jobs: [],
  currentJob: null,
  loading: false,
  error: null,
  totalCount: 0,
  currentPage: 1,
  hasMore: true,
  filters: {},
};

// Async thunks
export const fetchJobs = createAsyncThunk(
  'jobs/fetchJobs',
  async (
    params: {
      page?: number;
      limit?: number;
      status?: string;
      project_id?: string;
      search?: string;
    } = {},
    { rejectWithValue }
  ) => {
    try {
      const response = await jobService.getJobs(params);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch jobs');
    }
  }
);

export const fetchJob = createAsyncThunk(
  'jobs/fetchJob',
  async (jobId: string, { rejectWithValue }) => {
    try {
      const response = await jobService.getJob(jobId);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch job');
    }
  }
);

export const createJob = createAsyncThunk(
  'jobs/createJob',
  async (jobData: JobForm, { rejectWithValue }) => {
    try {
      const response = await jobService.createJob(jobData);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to create job');
    }
  }
);

export const updateJob = createAsyncThunk(
  'jobs/updateJob',
  async ({ id, data }: { id: string; data: Partial<JobForm> }, { rejectWithValue }) => {
    try {
      const response = await jobService.updateJob(id, data);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update job');
    }
  }
);

export const deleteJob = createAsyncThunk(
  'jobs/deleteJob',
  async (jobId: string, { rejectWithValue }) => {
    try {
      await jobService.deleteJob(jobId);
      return jobId;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to delete job');
    }
  }
);

export const cancelJob = createAsyncThunk(
  'jobs/cancelJob',
  async (jobId: string, { rejectWithValue }) => {
    try {
      const response = await jobService.cancelJob(jobId);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to cancel job');
    }
  }
);

export const retryJob = createAsyncThunk(
  'jobs/retryJob',
  async (jobId: string, { rejectWithValue }) => {
    try {
      const response = await jobService.retryJob(jobId);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to retry job');
    }
  }
);

const jobsSlice = createSlice({
  name: 'jobs',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setCurrentJob: (state, action: PayloadAction<ScrapingJob | null>) => {
      state.currentJob = action.payload;
    },
    setFilters: (state, action: PayloadAction<typeof initialState.filters>) => {
      state.filters = action.payload;
    },
    resetJobs: (state) => {
      state.jobs = [];
      state.currentPage = 1;
      state.hasMore = true;
      state.totalCount = 0;
    },
    updateJobStatus: (
      state,
      action: PayloadAction<{ id: string; status: string; error_message?: string }>
    ) => {
      const { id, status, error_message } = action.payload;
      const job = state.jobs.find((j) => j.id === id);

      if (job) {
        job.status = status as any;
        if (error_message) {
          job.error_message = error_message;
        }
        if (status === 'running') {
          job.started_at = new Date().toISOString();
        } else if (status === 'completed' || status === 'failed') {
          job.completed_at = new Date().toISOString();
        }
      }

      if (state.currentJob?.id === id) {
        state.currentJob = { ...state.currentJob, status: status as any };
        if (error_message) {
          state.currentJob.error_message = error_message;
        }
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch Jobs
    builder
      .addCase(fetchJobs.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchJobs.fulfilled, (state, action) => {
        state.loading = false;
        const { data, total, page, has_next } = action.payload;

        if (page === 1) {
          state.jobs = data;
        } else {
          state.jobs = [...state.jobs, ...data];
        }

        state.totalCount = total;
        state.currentPage = page;
        state.hasMore = has_next;
        state.error = null;
      })
      .addCase(fetchJobs.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Fetch Single Job
    builder
      .addCase(fetchJob.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchJob.fulfilled, (state, action) => {
        state.loading = false;
        state.currentJob = action.payload;
        state.error = null;
      })
      .addCase(fetchJob.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Create Job
    builder
      .addCase(createJob.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createJob.fulfilled, (state, action) => {
        state.loading = false;
        state.jobs.unshift(action.payload);
        state.totalCount += 1;
        state.error = null;
      })
      .addCase(createJob.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Update Job
    builder.addCase(updateJob.fulfilled, (state, action) => {
      const updatedJob = action.payload;
      const index = state.jobs.findIndex((j) => j.id === updatedJob.id);

      if (index !== -1) {
        state.jobs[index] = updatedJob;
      }

      if (state.currentJob?.id === updatedJob.id) {
        state.currentJob = updatedJob;
      }
    });

    // Delete Job
    builder.addCase(deleteJob.fulfilled, (state, action) => {
      const deletedId = action.payload;
      state.jobs = state.jobs.filter((j) => j.id !== deletedId);
      state.totalCount -= 1;

      if (state.currentJob?.id === deletedId) {
        state.currentJob = null;
      }
    });

    // Cancel Job
    builder.addCase(cancelJob.fulfilled, (state, action) => {
      const updatedJob = action.payload;
      const index = state.jobs.findIndex((j) => j.id === updatedJob.id);

      if (index !== -1) {
        state.jobs[index] = updatedJob;
      }

      if (state.currentJob?.id === updatedJob.id) {
        state.currentJob = updatedJob;
      }
    });

    // Retry Job
    builder.addCase(retryJob.fulfilled, (state, action) => {
      const updatedJob = action.payload;
      const index = state.jobs.findIndex((j) => j.id === updatedJob.id);

      if (index !== -1) {
        state.jobs[index] = updatedJob;
      }

      if (state.currentJob?.id === updatedJob.id) {
        state.currentJob = updatedJob;
      }
    });
  },
});

export const { clearError, setCurrentJob, setFilters, resetJobs, updateJobStatus } =
  jobsSlice.actions;

export default jobsSlice.reducer;

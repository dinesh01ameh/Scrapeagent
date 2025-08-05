# SwissKnife AI Scraper - Frontend Dashboard

React-based web dashboard for the SwissKnife AI Scraper platform.

## Features

- **Authentication**: Login/register with JWT token management
- **Dashboard**: Real-time statistics and activity monitoring
- **Project Management**: Create, edit, and organize scraping projects
- **Job Management**: Monitor and control scraping jobs
- **Content Browser**: View and analyze extracted content
- **Responsive Design**: Mobile-friendly interface
- **Real-time Updates**: WebSocket integration for live updates

## Tech Stack

- **React 18** with TypeScript
- **Material-UI (MUI)** for components and theming
- **Redux Toolkit** for state management
- **React Router** for navigation
- **React Query** for API data fetching
- **React Hook Form** with Yup validation
- **Axios** for HTTP requests
- **Socket.IO** for real-time updates

## Getting Started

### Prerequisites

- Node.js 16+ and npm/yarn
- Backend API running on port 8601

### Installation

1. Install dependencies:
```bash
npm install
```

2. Copy environment configuration:
```bash
cp .env.example .env
```

3. Update `.env` with your API URL if different from default

4. Start the development server:
```bash
npm start
```

The app will open at [http://localhost:8650](http://localhost:8650)

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues
- `npm run format` - Format code with Prettier
- `npm run type-check` - Run TypeScript type checking

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── auth/           # Authentication components
│   └── layout/         # Layout components (Header, Sidebar)
├── contexts/           # React contexts
├── hooks/              # Custom React hooks
├── pages/              # Page components
│   ├── auth/           # Login/Register pages
│   ├── dashboard/      # Dashboard page
│   ├── projects/       # Projects management
│   ├── jobs/           # Jobs management
│   ├── content/        # Content browser
│   └── settings/       # Settings page
├── services/           # API service layer
├── store/              # Redux store and slices
├── types/              # TypeScript type definitions
└── utils/              # Utility functions
```

## API Integration

The frontend communicates with the backend API through:

- **Authentication**: JWT token-based authentication
- **REST API**: CRUD operations for projects, jobs, content
- **WebSocket**: Real-time updates for job status and notifications
- **File Upload**: Support for file uploads and downloads

## State Management

- **Redux Toolkit** for global state
- **React Query** for server state and caching
- **Local Storage** for authentication tokens
- **Context API** for authentication state

## Styling

- **Material-UI** theme system
- **Responsive design** with breakpoints
- **Dark/Light theme** support (planned)
- **Custom components** following Material Design

## Development

### Code Style

- **ESLint** with React and TypeScript rules
- **Prettier** for code formatting
- **Husky** for pre-commit hooks (planned)

### Testing

- **Jest** and **React Testing Library**
- **Component testing** for UI components
- **Integration testing** for user flows
- **API mocking** with MSW (planned)

## Deployment

### Production Build

```bash
npm run build
```

### Docker

```bash
docker build -t swissknife-frontend .
docker run -p 3000:3000 swissknife-frontend
```

### Environment Variables

- `REACT_APP_API_URL` - Backend API URL
- `REACT_APP_ENV` - Environment (development/production)
- `REACT_APP_DEBUG` - Enable debug mode

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation as needed
4. Use conventional commit messages

## License

This project is part of the SwissKnife AI Scraper platform.

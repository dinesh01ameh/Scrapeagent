#!/bin/bash

# SwissKnife AI Scraper - Docker Launch Script
# Complete containerized deployment script

set -e

echo "🐳 SwissKnife AI Scraper - Docker Launch"
echo "========================================"

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    echo "✅ Docker is running"
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
    echo "✅ Docker Compose is available"
}

# Function to build and start services
launch_services() {
    local mode=$1
    
    echo ""
    echo "🚀 Launching SwissKnife AI Scraper in $mode mode..."
    
    case $mode in
        "development")
            echo "📦 Building and starting development environment..."
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
            ;;
        "production")
            echo "📦 Building and starting production environment..."
            docker-compose -f docker-compose.prod.yml up --build -d
            ;;
        *)
            echo "📦 Building and starting default environment..."
            docker-compose up --build -d
            ;;
    esac
}

# Function to show service status
show_status() {
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    
    echo ""
    echo "🌐 Access URLs:"
    echo "  Frontend Dashboard: http://localhost:8650"
    echo "  Backend API:        http://localhost:8601"
    echo "  API Documentation:  http://localhost:8601/docs"
    echo "  PostgreSQL:         localhost:5432"
    echo "  Redis:              localhost:6379"
    echo "  Ollama:             http://localhost:11434"
}

# Function to wait for services to be healthy
wait_for_services() {
    echo ""
    echo "⏳ Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep -q "Up (healthy)"; then
            echo "✅ Services are healthy!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - Waiting for services..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    echo "⚠️  Services may not be fully healthy yet. Check logs if needed."
}

# Function to show logs
show_logs() {
    echo ""
    echo "📋 Recent logs:"
    docker-compose logs --tail=20
}

# Main execution
main() {
    local mode=${1:-"default"}
    
    # Pre-flight checks
    check_docker
    check_docker_compose
    
    # Launch services
    launch_services $mode
    
    # Wait for services
    wait_for_services
    
    # Show status
    show_status
    
    echo ""
    echo "🎉 SwissKnife AI Scraper is now running!"
    echo ""
    echo "📝 Useful commands:"
    echo "  View logs:     docker-compose logs -f"
    echo "  Stop services: docker-compose down"
    echo "  Restart:       docker-compose restart"
    echo "  Shell access:  docker-compose exec swissknife bash"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Follow logs
    docker-compose logs -f
}

# Handle script arguments
case ${1:-""} in
    "dev"|"development")
        main "development"
        ;;
    "prod"|"production")
        main "production"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "stop")
        echo "🛑 Stopping all services..."
        docker-compose down
        ;;
    "status")
        show_status
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [dev|prod|logs|stop|status|help]"
        echo ""
        echo "Commands:"
        echo "  dev        - Start in development mode with hot reload"
        echo "  prod       - Start in production mode"
        echo "  logs       - Show and follow logs"
        echo "  stop       - Stop all services"
        echo "  status     - Show service status"
        echo "  help       - Show this help message"
        ;;
    *)
        main "default"
        ;;
esac

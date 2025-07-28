#!/bin/bash

# Bug Report Triage Service - Docker Start Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Bug Report Triage Service - Docker Setup${NC}"
echo "================================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${RED}❗ Please edit .env file with your API keys before continuing${NC}"
    echo -e "${YELLOW}   Required: OPENAI_API_KEY${NC}"
    echo -e "${YELLOW}   Optional: GITHUB_API_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME${NC}"
    echo ""
    read -p "Press Enter after configuring .env file..."
fi

# Check if OpenAI API key is set
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo -e "${RED}❗ OPENAI_API_KEY not found or invalid in .env file${NC}"
    echo -e "${YELLOW}   Please add your OpenAI API key to .env file${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment configuration found${NC}"

# Create logs directory
mkdir -p logs

# Function to start services
start_infrastructure() {
    echo -e "\n${BLUE}🚀 Starting infrastructure services (Kafka, Redis, UIs)...${NC}"
    docker-compose up -d zookeeper kafka redis kafka-ui redis-commander
    
    echo -e "\n${YELLOW}⏳ Waiting for services to be ready...${NC}"
    echo "This may take 30-60 seconds for Kafka to fully initialize..."
    
    # Wait for Kafka to be ready
    echo -n "Waiting for Kafka: "
    for i in {1..30}; do
        if docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for Redis to be ready
    echo -n "Waiting for Redis: "
    for i in {1..10}; do
        if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
}

start_full_service() {
    echo -e "\n${BLUE}🏃 Starting full service (including Bug Triage Service)...${NC}"
    docker-compose --profile full up -d
    
    echo -e "\n${GREEN}✅ All services started successfully!${NC}"
    show_service_info
}

show_service_info() {
    echo -e "\n${BLUE}📋 Service Information:${NC}"
    echo "================================"
    echo -e "🔗 Kafka UI:        ${GREEN}http://localhost:8080${NC}"
    echo -e "🔗 Redis Commander: ${GREEN}http://localhost:8081${NC}"
    echo -e "📊 Kafka:           ${GREEN}localhost:9092${NC}"
    echo -e "💾 Redis:           ${GREEN}localhost:6379${NC}"
    echo ""
    echo -e "${BLUE}📝 Useful Commands:${NC}"
    echo "• View logs:           docker-compose logs -f"
    echo "• View service logs:   docker-compose logs -f bug-triage-service"
    echo "• Stop all:           docker-compose down"
    echo "• Stop with cleanup:   docker-compose down -v"
    echo ""
}

show_menu() {
    echo -e "\n${BLUE}🎯 What would you like to do?${NC}"
    echo "1) Start infrastructure only (Kafka, Redis, UIs)"
    echo "2) Start full service (including Bug Triage Service)"
    echo "3) Stop all services"
    echo "4) View service status"
    echo "5) View logs"
    echo "6) Clean up (stop and remove volumes)"
    echo "7) Exit"
    echo ""
    read -p "Enter your choice (1-7): " choice
    
    case $choice in
        1)
            start_infrastructure
            show_service_info
            ;;
        2)
            start_infrastructure
            start_full_service
            ;;
        3)
            echo -e "\n${YELLOW}🛑 Stopping all services...${NC}"
            docker-compose down
            echo -e "${GREEN}✅ All services stopped${NC}"
            ;;
        4)
            echo -e "\n${BLUE}📊 Service Status:${NC}"
            docker-compose ps
            ;;
        5)
            echo -e "\n${BLUE}📋 Recent logs (Ctrl+C to exit):${NC}"
            docker-compose logs -f --tail=50
            ;;
        6)
            echo -e "\n${RED}🧹 Cleaning up (this will remove all data)...${NC}"
            read -p "Are you sure? (y/N): " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                docker-compose down -v --remove-orphans
                docker system prune -f
                echo -e "${GREEN}✅ Cleanup completed${NC}"
            else
                echo -e "${YELLOW}Cleanup cancelled${NC}"
            fi
            ;;
        7)
            echo -e "\n${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid choice${NC}"
            ;;
    esac
}

# Main execution
if [ "$1" = "infrastructure" ]; then
    start_infrastructure
    show_service_info
elif [ "$1" = "full" ]; then
    start_infrastructure
    start_full_service
elif [ "$1" = "stop" ]; then
    docker-compose down
elif [ "$1" = "clean" ]; then
    docker-compose down -v --remove-orphans
    docker system prune -f
else
    # Interactive mode
    while true; do
        show_menu
        echo ""
        read -p "Press Enter to continue..."
        clear
    done
fi

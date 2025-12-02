#!/bin/bash

# MCP Tool-Calling Agent - Deployment Verification Script
# This script verifies that the application is running correctly

echo "🔍 MCP Tool-Calling Agent - Deployment Verification"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
echo -e "\n📦 Checking Docker..."
if ! docker --version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not installed or not running${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Docker is available${NC}"
fi

# Check if docker-compose is available
echo -e "\n🐙 Checking Docker Compose..."
if ! docker-compose --version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Docker Compose is available${NC}"
fi

# Start the application
echo -e "\n🚀 Starting MCP Tool-Calling Agent..."
docker-compose up -d --build

# Wait for services to be ready
echo -e "\n⏳ Waiting for services to start..."
sleep 30

# Check if container is running
echo -e "\n🔍 Checking container status..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Container is running${NC}"
else
    echo -e "${RED}❌ Container failed to start${NC}"
    docker-compose logs
    exit 1
fi

# Test health endpoint
echo -e "\n🩺 Testing health endpoint..."
health_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$health_response" = "200" ]; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed (HTTP $health_response)${NC}"
    exit 1
fi

# Test main frontend
echo -e "\n🌐 Testing frontend..."
frontend_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$frontend_response" = "200" ]; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${RED}❌ Frontend is not accessible (HTTP $frontend_response)${NC}"
    exit 1
fi

# Test API documentation
echo -e "\n📚 Testing API documentation..."
docs_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$docs_response" = "200" ]; then
    echo -e "${GREEN}✅ API documentation is accessible${NC}"
else
    echo -e "${RED}❌ API documentation is not accessible (HTTP $docs_response)${NC}"
    exit 1
fi

# Test tools endpoint
echo -e "\n🔧 Testing tools endpoint..."
tools_response=$(curl -s -X GET http://localhost:8000/tools | jq -r '.success')
if [ "$tools_response" = "true" ]; then
    echo -e "${GREEN}✅ Tools endpoint is working${NC}"
    # Show available tools
    echo -e "\n📋 Available tools:"
    curl -s -X GET http://localhost:8000/tools | jq -r '.tools[].name' | sed 's/^/  - /'
else
    echo -e "${YELLOW}⚠️  Tools endpoint may have issues${NC}"
fi

# Test agent endpoint with simple query
echo -e "\n🤖 Testing agent endpoint..."
agent_test=$(curl -s -X POST "http://localhost:8000/agent" \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate 2 + 2", "context": {}}' | jq -r '.success')

if [ "$agent_test" = "true" ]; then
    echo -e "${GREEN}✅ Agent endpoint is working${NC}"
else
    echo -e "${YELLOW}⚠️  Agent endpoint may have issues (this is normal without OpenAI key)${NC}"
fi

echo -e "\n🎉 Deployment Verification Complete!"
echo -e "======================================"
echo -e "🌐 Application URL: ${GREEN}http://localhost:8000${NC}"
echo -e "📚 API Documentation: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "🩺 Health Check: ${GREEN}http://localhost:8000/health${NC}"

echo -e "\n📝 Next Steps:"
echo -e "1. Open ${GREEN}http://localhost:8000${NC} in your browser"
echo -e "2. Try the example queries to test functionality"
echo -e "3. Upload a PDF file to test document processing"
echo -e "4. Add OpenAI API key in .env for enhanced features"
echo -e "5. Check logs with: ${YELLOW}docker-compose logs -f${NC}"

echo -e "\n🛑 To stop the application:"
echo -e "   ${YELLOW}docker-compose down${NC}"

echo -e "\n✨ Happy testing! ✨"
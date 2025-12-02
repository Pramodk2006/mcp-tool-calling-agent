# MCP Tool-Calling Agent - Deployment Verification Script (PowerShell)
# This script verifies that the application is running correctly on Windows

Write-Host "🔍 MCP Tool-Calling Agent - Deployment Verification" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

function Test-Command($Command) {
    try {
        & $Command --version | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Test-HttpEndpoint($Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        return $response.StatusCode
    } catch {
        return $null
    }
}

# Check if Docker is running
Write-Host "`n📦 Checking Docker..." -ForegroundColor Yellow
if (Test-Command "docker") {
    Write-Host "✅ Docker is available" -ForegroundColor Green
} else {
    Write-Host "❌ Docker is not installed or not running" -ForegroundColor Red
    exit 1
}

# Check if docker-compose is available
Write-Host "`n🐙 Checking Docker Compose..." -ForegroundColor Yellow
if (Test-Command "docker-compose") {
    Write-Host "✅ Docker Compose is available" -ForegroundColor Green
} else {
    Write-Host "❌ Docker Compose is not installed" -ForegroundColor Red
    exit 1
}

# Start the application
Write-Host "`n🚀 Starting MCP Tool-Calling Agent..." -ForegroundColor Yellow
docker-compose up -d --build

# Wait for services to be ready
Write-Host "`n⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check if container is running
Write-Host "`n🔍 Checking container status..." -ForegroundColor Yellow
$containerStatus = docker-compose ps
if ($containerStatus -match "Up") {
    Write-Host "✅ Container is running" -ForegroundColor Green
} else {
    Write-Host "❌ Container failed to start" -ForegroundColor Red
    docker-compose logs
    exit 1
}

# Test health endpoint
Write-Host "`n🩺 Testing health endpoint..." -ForegroundColor Yellow
$healthStatus = Test-HttpEndpoint "http://localhost:8000/health"
if ($healthStatus -eq 200) {
    Write-Host "✅ Health check passed" -ForegroundColor Green
} else {
    Write-Host "❌ Health check failed (HTTP $healthStatus)" -ForegroundColor Red
    exit 1
}

# Test main frontend
Write-Host "`n🌐 Testing frontend..." -ForegroundColor Yellow
$frontendStatus = Test-HttpEndpoint "http://localhost:8000/"
if ($frontendStatus -eq 200) {
    Write-Host "✅ Frontend is accessible" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend is not accessible (HTTP $frontendStatus)" -ForegroundColor Red
    exit 1
}

# Test API documentation
Write-Host "`n📚 Testing API documentation..." -ForegroundColor Yellow
$docsStatus = Test-HttpEndpoint "http://localhost:8000/docs"
if ($docsStatus -eq 200) {
    Write-Host "✅ API documentation is accessible" -ForegroundColor Green
} else {
    Write-Host "❌ API documentation is not accessible (HTTP $docsStatus)" -ForegroundColor Red
    exit 1
}

# Test tools endpoint
Write-Host "`n🔧 Testing tools endpoint..." -ForegroundColor Yellow
try {
    $toolsResponse = Invoke-RestMethod -Uri "http://localhost:8000/tools" -Method GET
    if ($toolsResponse.success -eq $true) {
        Write-Host "✅ Tools endpoint is working" -ForegroundColor Green
        Write-Host "`n📋 Available tools:" -ForegroundColor Cyan
        foreach ($tool in $toolsResponse.tools) {
            Write-Host "  - $($tool.name)" -ForegroundColor White
        }
    } else {
        Write-Host "⚠️  Tools endpoint may have issues" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Tools endpoint may have issues" -ForegroundColor Yellow
}

# Test agent endpoint with simple query
Write-Host "`n🤖 Testing agent endpoint..." -ForegroundColor Yellow
try {
    $agentBody = @{
        query = "Calculate 2 + 2"
        context = @{}
    } | ConvertTo-Json

    $agentResponse = Invoke-RestMethod -Uri "http://localhost:8000/agent" -Method POST -Body $agentBody -ContentType "application/json"
    
    if ($agentResponse.success -eq $true) {
        Write-Host "✅ Agent endpoint is working" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Agent endpoint may have issues (this is normal without OpenAI key)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Agent endpoint may have issues (this is normal without OpenAI key)" -ForegroundColor Yellow
}

Write-Host "`n🎉 Deployment Verification Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host "🌐 Application URL: " -ForegroundColor White -NoNewline
Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Documentation: " -ForegroundColor White -NoNewline  
Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🩺 Health Check: " -ForegroundColor White -NoNewline
Write-Host "http://localhost:8000/health" -ForegroundColor Cyan

Write-Host "`n📝 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Open " -ForegroundColor White -NoNewline
Write-Host "http://localhost:8000" -ForegroundColor Cyan -NoNewline
Write-Host " in your browser" -ForegroundColor White
Write-Host "2. Try the example queries to test functionality" -ForegroundColor White
Write-Host "3. Upload a PDF file to test document processing" -ForegroundColor White
Write-Host "4. Add OpenAI API key in .env for enhanced features" -ForegroundColor White
Write-Host "5. Check logs with: " -ForegroundColor White -NoNewline
Write-Host "docker-compose logs -f" -ForegroundColor Yellow

Write-Host "`n🛑 To stop the application:" -ForegroundColor Red
Write-Host "   docker-compose down" -ForegroundColor Yellow

Write-Host "`n✨ Happy testing! ✨" -ForegroundColor Magenta
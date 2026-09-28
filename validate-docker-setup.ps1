#!/usr/bin/env powershell
<#
.SYNOPSIS
Docker Setup Validation Script for TA Candidate Screening

.DESCRIPTION
This script validates that all Docker containers are running correctly and that
the application is responding to requests properly.

.USAGE
.\validate-docker-setup.ps1

.NOTES
Requires: Docker, Docker Compose, PowerShell 5.0+
#>

# Set error action preference
$ErrorActionPreference = "Continue"

# Color output functions
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Magenta
    Write-Host $Message -ForegroundColor Magenta
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Magenta
}

# Initialize results
$passedTests = 0
$failedTests = 0
$warnings = 0

Write-Header "Docker Setup Validation"
Write-Info "Starting validation of TA Candidate Screening Docker setup..."

# Test 1: Docker Installation
Write-Header "1. Checking Docker Installation"
try {
    $dockerVersion = docker --version
    Write-Success $dockerVersion
    $passedTests++
}
catch {
    Write-Error-Custom "Docker is not installed or not in PATH"
    $failedTests++
    exit 1
}

# Test 2: Docker Compose Installation
Write-Header "2. Checking Docker Compose Installation"
try {
    $composeVersion = docker compose version
    Write-Success $composeVersion
    $passedTests++
}
catch {
    Write-Error-Custom "Docker Compose is not installed"
    $failedTests++
    exit 1
}

# Test 3: Docker Daemon Running
Write-Header "3. Checking Docker Daemon"
try {
    docker ps > $null 2>&1
    Write-Success "Docker daemon is running"
    $passedTests++
}
catch {
    Write-Error-Custom "Docker daemon is not running"
    $failedTests++
    Write-Warning-Custom "Start Docker Desktop or Docker service and try again"
    exit 1
}

# Test 4: Environment File
Write-Header "4. Checking Environment Configuration"
if (Test-Path ".env") {
    Write-Success ".env file exists"
    $passedTests++
    
    # Check for critical variables
    $envContent = Get-Content ".env" -Raw
    $criticalVars = @("DB_PASSWORD", "JWT_SECRET_KEY", "DATABASE_URL")
    $missingVars = @()
    
    foreach ($var in $criticalVars) {
        if ($envContent -notmatch $var) {
            $missingVars += $var
        }
    }
    
    if ($missingVars.Count -gt 0) {
        Write-Warning-Custom "Missing configuration variables: $($missingVars -join ', ')"
        $warnings++
    }
    else {
        Write-Success "All critical configuration variables present"
        $passedTests++
    }
}
else {
    Write-Warning-Custom ".env file not found. Using defaults."
    $warnings++
}

# Test 5: Docker Compose File
Write-Header "5. Checking docker-compose.yml"
if (Test-Path "docker-compose.yml") {
    Write-Success "docker-compose.yml exists"
    
    try {
        docker compose config > $null 2>&1
        Write-Success "docker-compose.yml syntax is valid"
        $passedTests++
    }
    catch {
        Write-Error-Custom "docker-compose.yml has syntax errors"
        $failedTests++
    }
}
else {
    Write-Error-Custom "docker-compose.yml not found in current directory"
    $failedTests++
}

# Test 6: Container Status
Write-Header "6. Checking Container Status"
$containers = docker compose ps --format "table {{.Names}}\t{{.Status}}"

if ($containers -match "ta-screening") {
    Write-Success "Containers exist"
    Write-Info "Container Status:"
    Write-Info $containers
    $passedTests++
}
else {
    Write-Warning-Custom "No running containers found. Run: docker compose up -d"
    $warnings++
}

# Test 7: PostgreSQL Health
Write-Header "7. Checking PostgreSQL"
try {
    $pgStatus = docker compose exec -T postgres pg_isready -U postgres 2>&1
    if ($pgStatus -match "accepting") {
        Write-Success "PostgreSQL is responding"
        $passedTests++
    }
    else {
        Write-Warning-Custom "PostgreSQL status unclear"
        $warnings++
    }
}
catch {
    Write-Warning-Custom "PostgreSQL container not accessible. Run: docker compose up -d"
    $warnings++
}

# Test 8: Backend Health
Write-Header "8. Checking Backend (FastAPI)"
try {
    $backendHealth = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5 -UseBasicParsing 2>&1
    if ($backendHealth.StatusCode -eq 200) {
        Write-Success "Backend is responding (Port 8000)"
        $passedTests++
    }
    else {
        Write-Warning-Custom "Backend returned status code: $($backendHealth.StatusCode)"
        $warnings++
    }
}
catch {
    Write-Warning-Custom "Backend not accessible at http://localhost:8000"
    Write-Info "If containers are running, wait a moment and try again"
    $warnings++
}

# Test 9: Frontend Availability
Write-Header "9. Checking Frontend (Angular)"
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:4200" -Method Get -TimeoutSec 5 -UseBasicParsing 2>&1
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Success "Frontend is responding (Port 4200)"
        $passedTests++
    }
    else {
        Write-Warning-Custom "Frontend returned status code: $($frontendResponse.StatusCode)"
        $warnings++
    }
}
catch {
    Write-Warning-Custom "Frontend not accessible at http://localhost:4200"
    Write-Info "If containers are running, wait a moment and try again"
    $warnings++
}

# Test 10: API Documentation
Write-Header "10. Checking API Documentation"
try {
    $apiDocs = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method Get -TimeoutSec 5 -UseBasicParsing 2>&1
    if ($apiDocs.StatusCode -eq 200) {
        Write-Success "Swagger API documentation available at http://localhost:8000/docs"
        $passedTests++
    }
}
catch {
    Write-Warning-Custom "API documentation not accessible"
    $warnings++
}

# Test 11: Port Availability
Write-Header "11. Checking Port Availability"
$ports = @{
    "4200" = "Frontend"
    "8000" = "Backend"
    "5432" = "Database"
}

foreach ($port in $ports.GetEnumerator()) {
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", [int]$port.Name)
        Write-Success "Port $($port.Name) ($($port.Value)) is accessible"
        $passedTests++
        $connection.Close()
    }
    catch {
        Write-Warning-Custom "Port $($port.Name) ($($port.Value)) is not accessible"
        $warnings++
    }
}

# Test 12: Volume Status
Write-Header "12. Checking Docker Volumes"
try {
    $volumes = docker volume ls --filter "label=com.docker.compose.project=ta-candidate-screening" -q
    if ($volumes) {
        Write-Success "Persistent volumes found:"
        Write-Info $volumes
        $passedTests++
    }
    else {
        Write-Warning-Custom "No volumes found (normal if containers never ran)"
        $warnings++
    }
}
catch {
    Write-Warning-Custom "Could not list volumes"
    $warnings++
}

# Test 13: Network Status
Write-Header "13. Checking Docker Network"
try {
    $networks = docker network ls --filter "name=ta" -q
    if ($networks) {
        Write-Success "Docker Compose network exists"
        $passedTests++
    }
    else {
        Write-Warning-Custom "No ta-network found (normal if containers never ran)"
        $warnings++
    }
}
catch {
    Write-Warning-Custom "Could not verify network"
    $warnings++
}

# Test 14: Documentation Files
Write-Header "14. Checking Documentation Files"
$docFiles = @(
    "DOCKER_SETUP.md",
    "DOCKER_QUICK_REFERENCE.md",
    "PRODUCTION_DEPLOYMENT_GUIDE.md",
    "DOCKER_INDEX.md"
)

$missingDocs = @()
foreach ($doc in $docFiles) {
    if (-not (Test-Path $doc)) {
        $missingDocs += $doc
    }
}

if ($missingDocs.Count -eq 0) {
    Write-Success "All documentation files present"
    $passedTests++
}
else {
    Write-Warning-Custom "Missing documentation: $($missingDocs -join ', ')"
    $warnings++
}

# Test 15: Dockerfile Availability
Write-Header "15. Checking Dockerfiles"
$dockerfiles = @(
    "frontend/Dockerfile",
    "backend/Dockerfile"
)

$missingDockerfiles = @()
foreach ($dockerfile in $dockerfiles) {
    if (-not (Test-Path $dockerfile)) {
        $missingDockerfiles += $dockerfile
    }
}

if ($missingDockerfiles.Count -eq 0) {
    Write-Success "All Dockerfiles present"
    $passedTests++
}
else {
    Write-Error-Custom "Missing Dockerfiles: $($missingDockerfiles -join ', ')"
    $failedTests++
}

# Summary
Write-Header "Validation Summary"

Write-Host ""
Write-Host "Results:" -ForegroundColor Cyan
Write-Success "Passed Tests: $passedTests"
Write-Warning-Custom "Warnings: $warnings"
Write-Error-Custom "Failed Tests: $failedTests"
Write-Host ""

# Recommendations
Write-Header "Recommendations"

if ($failedTests -eq 0 -and $warnings -eq 0) {
    Write-Success "All checks passed! Your Docker setup is ready."
    Write-Info ""
    Write-Info "Next steps:"
    Write-Info "1. Frontend: http://localhost:4200"
    Write-Info "2. API Docs: http://localhost:8000/docs"
    Write-Info "3. API Health: http://localhost:8000/health"
    Write-Info ""
    Write-Info "View logs: docker compose logs -f"
    Write-Info "Stop services: docker compose down"
}
elseif ($failedTests -gt 0) {
    Write-Error-Custom ""
    Write-Error-Custom "Critical issues found. Please fix these before proceeding:"
    Write-Error-Custom "1. Review the failed tests above"
    Write-Error-Custom "2. Check DOCKER_SETUP.md for troubleshooting"
    Write-Error-Custom "3. Run: docker compose logs -f"
    exit 1
}
else {
    Write-Warning-Custom ""
    Write-Warning-Custom "Some warnings detected, but setup may still be functional:"
    Write-Warning-Custom "1. If containers aren't running, start them: docker compose up -d"
    Write-Warning-Custom "2. Wait 30-60 seconds for services to initialize"
    Write-Warning-Custom "3. Run this script again"
    Write-Warning-Custom "4. Check DOCKER_SETUP.md for troubleshooting"
}

Write-Host ""
Write-Info "For detailed information, see:"
Write-Info "- DOCKER_SETUP.md (Complete guide)"
Write-Info "- DOCKER_QUICK_REFERENCE.md (Quick commands)"
Write-Info "- PRODUCTION_DEPLOYMENT_GUIDE.md (Production setup)"

Write-Host ""

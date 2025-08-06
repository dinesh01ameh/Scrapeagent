# Serena MCP Server Startup Script for Augment Code
# This script starts Serena as an MCP server with your Scrapeagent project

# Add uv to PATH
$env:Path = "C:\Users\Administrator\.local\bin;$env:Path"

# Start Serena MCP server with your project
Write-Host "Starting Serena MCP Server for Scrapeagent project..." -ForegroundColor Green
Write-Host "Project Path: F:\Live Projects\Scrapeagent" -ForegroundColor Cyan
Write-Host "Dashboard will be available at: http://localhost:24282/dashboard/" -ForegroundColor Yellow

uvx --from git+https://github.com/oraios/serena serena start-mcp-server `
    --project "F:\Live Projects\Scrapeagent" `
    --transport stdio `
    --enable-web-dashboard true `
    --enable-gui-log-window false `
    --log-level INFO

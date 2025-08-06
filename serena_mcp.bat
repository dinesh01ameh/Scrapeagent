@echo off
set PATH=C:\Users\Administrator\.local\bin;%PATH%
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --project "F:\Live Projects\Scrapeagent" --transport stdio --enable-web-dashboard true --log-level INFO

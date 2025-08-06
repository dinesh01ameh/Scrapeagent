# Serena MCP Server Installation & Configuration Guide

**Complete Reference for Setting Up Serena MCP Server in Augment Code**

---

## Table of Contents

1. [Prerequisites and System Requirements](#prerequisites-and-system-requirements)
2. [Serena Installation Process](#serena-installation-process)
3. [MCP Server Configuration in Augment Code](#mcp-server-configuration-in-augment-code)
4. [Verification and Testing](#verification-and-testing)
5. [Troubleshooting Section](#troubleshooting-section)
6. [Project Integration](#project-integration)
7. [Best Practices](#best-practices)

---

## Prerequisites and System Requirements

### Required Software

| Software | Minimum Version | Recommended Version | Notes |
|----------|----------------|-------------------|-------|
| **Python** | 3.8+ | 3.11+ | Required for Serena runtime |
| **uv** | 0.1.0+ | Latest | Python package installer |
| **Git** | 2.20+ | Latest | For Serena repository access |
| **Augment Code** | Latest | Latest | IDE with MCP support |

### Operating System Compatibility

- ✅ **Windows 10/11** (Recommended: Use batch files for MCP commands)
- ✅ **macOS 10.15+** (Use shell scripts or direct commands)
- ✅ **Linux** (Ubuntu 20.04+, other distributions)

### System Configuration Requirements

#### Windows Specific
- **PowerShell Execution Policy**: May need adjustment for script execution
- **PATH Environment**: Ensure `uv` and Python are in system PATH
- **User Permissions**: Standard user permissions sufficient

#### macOS/Linux Specific
- **Shell Access**: Bash or Zsh shell
- **Package Managers**: Homebrew (macOS) or system package manager
- **File Permissions**: Execute permissions for scripts

---

## Serena Installation Process

### Step 1: Install uv (if not already installed)

#### Windows (PowerShell)
```powershell
# Install uv via pip
pip install uv

# Or via winget
winget install astral-sh.uv
```

#### macOS
```bash
# Install via Homebrew
brew install uv

# Or via curl
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Linux
```bash
# Install via curl
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

### Step 2: Verify uv Installation

```bash
uv --version
```
**Expected Output:** `uv 0.x.x` (version number)

### Step 3: Install Serena via uvx

```bash
uvx --from git+https://github.com/oraios/serena serena --help
```

**Expected Output:** Serena help text with available commands

### Step 4: Verify Serena Installation

```bash
uvx --from git+https://github.com/oraios/serena serena --version
```

**Expected Output:** Serena version information

### Common Installation Troubleshooting

#### Issue: "uv command not found"
**Solution:**
```bash
# Add uv to PATH (adjust path as needed)
export PATH="$HOME/.local/bin:$PATH"  # Linux/macOS
# Or restart terminal after installation
```

#### Issue: "Git repository not accessible"
**Solutions:**
1. Check internet connection
2. Verify Git is installed: `git --version`
3. Try with explicit Git protocol: `git+https://github.com/oraios/serena.git`

#### Issue: Python version conflicts
**Solution:**
```bash
# Use specific Python version with uv
uv python install 3.11
uvx --python 3.11 --from git+https://github.com/oraios/serena serena --help
```

---

## MCP Server Configuration in Augment Code

### Step 1: Access MCP Server Settings

1. Open **Augment Code**
2. Navigate to **Workspace Settings** (gear icon)
3. Click on **Tools** tab
4. Scroll to MCP servers section

### Step 2: Create Batch File (Windows Recommended)

Create a batch file in your project directory for reliable execution:

**File:** `serena_mcp.bat`
```batch
@echo off
set PATH=C:\Users\%USERNAME%\.local\bin;%PATH%
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --project "%~dp0" --transport stdio --enable-web-dashboard true --log-level INFO
```

**File:** `serena_mcp.sh` (macOS/Linux)
```bash
#!/bin/bash
export PATH="$HOME/.local/bin:$PATH"
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --project "$(dirname "$0")" --transport stdio --enable-web-dashboard true --log-level INFO
```

### Step 3: Configure MCP Server in Augment Code

#### Configuration Method 1: Using Batch File (Windows - Recommended)

**Name:**
```
Serena
```

**Command:**
```
C:\path\to\your\project\serena_mcp.bat
```

**Environment Variables:**
- Leave empty (handled by batch file)

#### Configuration Method 2: Direct Command (All Platforms)

**Name:**
```
Serena
```

**Command:**
```
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --project "C:\path\to\your\project" --transport stdio --enable-web-dashboard true --log-level INFO
```

**Environment Variables:**
- **Name:** `PATH`
- **Value:** `C:\Users\%USERNAME%\.local\bin;%PATH%` (Windows)
- **Value:** `$HOME/.local/bin:$PATH` (macOS/Linux)

### Step 4: Save Configuration

1. Click **Save** button
2. Wait for the server to initialize (may take 30-60 seconds)
3. Look for green dot indicator next to "Serena"

---

## Verification and Testing

### Visual Indicators

#### Success Indicators ✅
- **Green dot** next to "Serena" in MCP server list
- **"(26) tools"** or similar count displayed
- **Expandable tool list** showing Serena tools like:
  - `read_file`
  - `create_text_file`
  - `list_dir`
  - `find_symbol`
  - etc.

#### Failure Indicators ❌
- **Red dot** next to "Serena"
- **"No tools available"** message
- **Error messages** in server status

### Functional Testing

#### Test 1: Basic Directory Listing
In Augment Code chat, try:
```
List the files in the current project directory
```

**Expected Result:** Directory listing of your project

#### Test 2: File Reading
```
Show me the contents of README.md
```

**Expected Result:** File contents displayed

#### Test 3: Symbol Overview
```
Show me the structure of main.py
```

**Expected Result:** Code symbols and structure information

### Troubleshooting UI Issues

#### "No tools available" Tooltip (Known UI Bug)
- **Symptom:** Tooltip shows "No tools available" but tools are listed
- **Status:** This is a cosmetic UI bug in Augment Code
- **Solution:** Ignore the tooltip - if tools are listed and functional, Serena is working
- **Verification:** Test with actual commands as shown above

---

## Troubleshooting Section

### Common Issues and Solutions

#### Issue: Red Dot - Server Won't Start

**Possible Causes & Solutions:**

1. **Path Issues**
   ```bash
   # Verify uv is accessible
   where uv  # Windows
   which uv  # macOS/Linux
   ```

2. **Project Path Issues**
   - Ensure project path exists and is accessible
   - Use absolute paths in configuration
   - Check for spaces in path (use quotes)

3. **Permission Issues (Windows)**
   ```powershell
   # Check PowerShell execution policy
   Get-ExecutionPolicy
   
   # If restricted, set to RemoteSigned
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Port Conflicts**
   - Serena uses port 24282 for web dashboard
   - Check if port is available: `netstat -an | findstr 24282`

#### Issue: Tools Not Loading

**Solutions:**
1. **Restart MCP Server**
   - Toggle server off/on in Augment Code settings
   - Wait 30-60 seconds between toggle

2. **Check Logs**
   - Look for error messages in Augment Code console
   - Check Serena logs at: `~/.serena/logs/`

3. **Verify Project Activation**
   ```
   # In Augment Code chat
   What project is currently active?
   ```

#### Issue: Slow Performance

**Solutions:**
1. **Reduce Log Level**
   ```bash
   # Change --log-level INFO to --log-level WARNING
   ```

2. **Disable Web Dashboard**
   ```bash
   # Change --enable-web-dashboard true to false
   ```

### Windows-Specific Troubleshooting

#### PowerShell Execution Policy
```powershell
# Check current policy
Get-ExecutionPolicy

# Set appropriate policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Batch File Not Executing
1. **Check file permissions**
2. **Verify batch file syntax**
3. **Test batch file manually** in Command Prompt

#### Path Environment Issues
```cmd
# Verify PATH includes uv location
echo %PATH%

# Add to PATH if missing
setx PATH "%PATH%;C:\Users\%USERNAME%\.local\bin"
```

---

## Project Integration

### Setting Up for New Projects

#### Step 1: Project Directory Structure
Ensure your project has:
```
your-project/
├── .git/                 # Git repository
├── pyproject.toml        # Python project file (if applicable)
├── requirements.txt      # Dependencies (if applicable)
├── serena_mcp.bat       # MCP server script
└── src/                 # Source code
```

#### Step 2: Project-Specific Configuration

**Option A: Per-Project Batch File**
Create `serena_mcp.bat` in each project root:
```batch
@echo off
set PATH=C:\Users\%USERNAME%\.local\bin;%PATH%
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --project "%~dp0" --transport stdio --enable-web-dashboard true --log-level INFO
```

**Option B: Global Configuration with Project Parameter**
Update MCP command to point to specific project:
```
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --project "C:\full\path\to\project" --transport stdio --enable-web-dashboard true --log-level INFO
```

#### Step 3: Project Activation Verification

After configuration, verify in Augment Code:
```
What is the current active project?
```

**Expected Response:** Your project name and path

### Multi-Project Management

#### Approach 1: Multiple MCP Servers
- Create separate MCP server entries for each project
- Name them descriptively: "Serena-ProjectA", "Serena-ProjectB"
- Enable/disable as needed

#### Approach 2: Dynamic Project Switching
- Use single MCP server
- Switch projects via Serena commands:
  ```
  Activate project at /path/to/other/project
  ```

---

## Best Practices

### Performance Optimization

1. **Use Appropriate Log Levels**
   - Development: `--log-level INFO`
   - Production: `--log-level WARNING`

2. **Disable Unnecessary Features**
   - Web dashboard: `--enable-web-dashboard false` (if not needed)

3. **Project Size Considerations**
   - Large projects (>10k files): Consider excluding directories
   - Use `.gitignore` patterns to reduce file scanning

### Security Considerations

1. **Path Security**
   - Use absolute paths in production
   - Avoid exposing sensitive directories

2. **Network Security**
   - Web dashboard runs on localhost only
   - No external network access by default

3. **File Permissions**
   - Ensure Serena has appropriate read/write permissions
   - Avoid running with elevated privileges

### Maintenance

#### Regular Updates
```bash
# Update Serena to latest version
uvx --from git+https://github.com/oraios/serena serena --version

# Force reinstall if needed
uv cache clean
uvx --reinstall --from git+https://github.com/oraios/serena serena --version
```

#### Log Management
- Logs stored in: `~/.serena/logs/`
- Clean old logs periodically
- Monitor log size for large projects

#### Configuration Backup
- Save MCP server configurations
- Document project-specific settings
- Version control batch files with projects

---

## Quick Reference

### Essential Commands

```bash
# Install/Update Serena
uvx --from git+https://github.com/oraios/serena serena --version

# Start MCP Server (manual test)
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --project "." --transport stdio

# Check Serena status
uvx --from git+https://github.com/oraios/serena serena --help
```

### Configuration Templates

**Windows Batch File:**
```batch
@echo off
set PATH=C:\Users\%USERNAME%\.local\bin;%PATH%
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --project "%~dp0" --transport stdio --enable-web-dashboard true --log-level INFO
```

**MCP Server Config:**
- **Name:** `Serena`
- **Command:** `C:\path\to\project\serena_mcp.bat`
- **Environment:** Empty

### Support Resources

- **Serena Repository:** https://github.com/oraios/serena
- **Augment Code Documentation:** Check official docs
- **Community Support:** GitHub Issues

---

*This guide was created for consistent Serena MCP server setup across projects. Keep this document updated with any configuration changes or new best practices discovered during usage.*

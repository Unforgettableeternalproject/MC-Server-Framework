# MC Server Framework - v0.2.0 (Phase 2 Release)

"Hey Exera, I made something for managing Minecraft servers! (◕‿◕✿)"
"Another project? What happened to your last dozen 'amazing ideas'?"

"This one's actually useful! It can manage multiple servers, switch Java versions, and even update DNS automatically~"
"So you're telling me you automated the thing you manually mess up every time?"

"...yes. But now I won't mess it up anymore! ヾ(≧▽≦*)o"
"We'll see about that when you try to configure Cloudflare API."

## Project Overview

MC Server Framework is a **local Minecraft Java server host management framework** with modular architecture, featuring unified server instance management, automatic backup strategies, Java version switching, Cloudflare DDNS integration, PlayIt.gg tunnel support, and RCON remote console. The project has completed **Phase 2 implementation** with enhanced features including interactive CLI, system diagnostics, and standalone executable packaging.

## Core Features

✯ **Server Management**:
- 🔹 **Multi-Instance Support** - Manage unlimited Minecraft servers in standardized directories
- 🔹 **Automatic Discovery** - Scan and validate server instances with configuration detection
- 🔹 **Server Lifecycle** - Start, stop, restart with process management and PID tracking
- 🔹 **Forge 1.17+ Support** - Intelligent detection and special launch mode for modern Forge
- 🔹 **Status Monitoring** - Real-time server state, uptime tracking, and health checks
- 🔹 **Orphaned Process Cleanup** - Automatic detection and cleanup of stale PID files

✯ **Java Version Management**:
- 🔹 **Profile System** - Global Java registry with centralized path management
- 🔹 **Per-Server Configuration** - Each server can use different Java versions
- 🔹 **Validation Tools** - Built-in Java profile validation and version checking
- 🔹 **Auto-Detection** - Suggest appropriate Java versions based on server type

✯ **Backup System**:
- 🔹 **Policy-Based Backups** - Internal, external, or disabled modes
- 🔹 **Smart Retention** - Keep last N backups or backups within N days
- 🔹 **Selective Archiving** - Include/exclude patterns for world data vs. libraries
- 🔹 **Pre/Post Hooks** - Execute server commands before/after backup (save-off/save-all)
- 🔹 **Compression Support** - ZIP and TAR formats with configurable compression

✯ **DNS Integration** (Cloudflare + DuckDNS):
- 🔹 **Dynamic IP Updates** - Automatic public IP detection and DNS record updates
- 🔹 **SRV Record Support** - Players can connect without port numbers
- 🔹 **Multi-Provider** - Cloudflare (A + SRV), DuckDNS (A only)
- 🔹 **Custom Ports** - Configurable server ports with automatic SRV sync
- 🔹 **Status Tracking** - DNS update history, error logging, and health monitoring

✯ **RCON Remote Console**:
- 🔹 **Interactive Console** - Direct command execution with real-time response
- 🔹 **Single Command Mode** - Send individual commands without entering console
- 🔹 **Automatic Configuration** - Auto-setup with server.properties integration

✯ **PlayIt.gg Tunnel Support** (CGNAT Bypass):
- 🔹 **Auto Lifecycle Management** - Tunnel starts/stops with server
- 🔹 **Agent Integration** - Seamless integration with PlayIt.gg agent
- 🔹 **DNS Integration** - Combine with Cloudflare for custom domain over tunnel
- 🔹 **Status Monitoring** - Real-time tunnel health checks
- 🔹 **Cleanup Tools** - Detect and clean orphaned tunnel processes

✯ **CLI Interface**:
- 🔹 **Rich Terminal UI** - Beautiful colored tables, panels, and progress indicators
- 🔹 **Interactive Menu** - User-friendly menu system for all operations
- 🔹 **Intuitive Commands** - Simple verbs: scan, list, init, start, stop, status, backup
- 🔹 **Subcommand Structure** - Organized DNS, Java, and tunnel management commands
- 🔹 **System Diagnostics** - Comprehensive environment and configuration checker
- 🔹 **First-Run Initialization** - Automatic setup with guided configuration

## Project Structure

## Project Structure

```
MC-Server-Framework/
├── app/                     # Application source code
│   ├── cli/                 # CLI command interface
│   │   ├── commands.py      # Command definitions (scan, start, dns, etc.)
│   │   ├── interactive.py   # Interactive menu system
│   │   ├── system_check.py  # System diagnostics tool
│   │   └── network_diag.py  # Network diagnostics
│   ├── core/                # Core functional modules
│   │   ├── scanner.py       # Server instance scanner
│   │   ├── launcher.py      # Server launcher with process management
│   │   ├── java_resolver.py # Java profile resolver
│   │   ├── path_resolver.py # Path interface for standardized access
│   │   ├── backup_manager.py # Backup execution and retention
│   │   ├── dns_manager.py   # DNS update manager (Cloudflare/DuckDNS)
│   │   ├── rcon_client.py   # RCON remote console client
│   │   ├── tunnel_manager.py # PlayIt.gg tunnel manager
│   │   └── initializer.py   # First-run initialization system
│   ├── models/              # Data models
│   │   ├── server_config.py # Server configuration schema
│   │   ├── java_profile.py  # Java registry schema
│   │   ├── backup_policy.py # Backup policy and records
│   │   └── instance_status.py # Server state tracking
│   ├── utils/               # Utility functions
│   │   ├── yaml_loader.py   # YAML configuration parser
│   │   ├── fs.py            # File system operations
│   │   ├── process.py       # Process management
│   │   ├── time_utils.py    # Time formatting utilities
│   │   └── archive.py       # Compression and archiving
│   └── main.py              # Application entry point
├── config/                  # Global configuration
│   ├── app.yml              # Application settings
│   └── java_registry.yml    # Java profile registry
├── servers/                 # Server instances directory
│   └── example-server/      # Individual server instance
│       ├── server.yml       # Server configuration
│       ├── server/          # Minecraft working directory
│       ├── runtime/         # Runtime state (PIDs, logs)
│       ├── backups/         # Backup archives
│       └── temp/            # Temporary files
├── templates/               # Configuration templates
│   └── default_server.yml   # Default server configuration
├── docs/                    # Documentation
│   └── SPEC.md              # Complete specification
├── requirements.txt         # Python dependencies
├── mc-server-framework.spec # PyInstaller configuration
├── build.ps1                # PowerShell build script
├── build.bat                # Windows batch build wrapper
├── package.ps1              # Release packaging script
├── BUILD.md                 # Build and packaging guide
├── GETTING_STARTED.txt      # User quick start guide (auto-generated)
├── QUICK_BUILD.md           # Quick build reference
├── mc-host.bat              # Windows batch wrapper
├── mc-host.ps1              # PowerShell wrapper
└── README.md                # This file
```

## Installation and Configuration

### Prerequisites
- Python 3.8+
- Windows 10/11 (primary support, Linux/Mac experimental)
- Java 8/17/21 (depending on your Minecraft version)
- Optional: Cloudflare account for DNS features

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Unforgettableeternalproject/MC-Server-Framework.git
   cd MC-Server-Framework
   ```

2. **Create virtual environment**
   ```bash
   python -m venv env
   # Windows
   .\env\Scripts\activate
   # Linux/Mac
   source env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Java registry**
   - Edit `config/java_registry.yml`
   - Add your Java installation paths:
     ```yaml
     profiles:
       java21:
         path: "C:/Program Files/Java/jdk-21/bin/java.exe"
         version: "21"
         description: "Java 21 - For Minecraft 1.20.5+"
     ```

5. **Initialize your first server**
   ```bash
   python -m app.main init my-server
   ```

6. **Add server files**
   - Place `server.jar` (or Forge files) into `servers/my-server/server/`
   - Edit `servers/my-server/server.yml` as needed

7. **Start the server**
   ```bash
   python -m app.main start my-server
   ```

### Quick Start (Using Convenience Scripts)

After installation, use wrapper scripts to avoid activating virtual env each time:

```bash
# Windows Batch
mc-host.bat scan
mc-host.bat start my-server

# PowerShell
.\mc-host.ps1 dns update my-server
```

## Common Commands

## Common Commands

### Server Management

```bash
# Scan and discover all server instances
python -m app.main scan

# List all servers
python -m app.main list

# Initialize new server
python -m app.main init <server-name>

# Start server
python -m app.main start <server-name>

# Stop server
python -m app.main stop <server-name>

# Restart server
python -m app.main restart <server-name>

# Check server status
python -m app.main status <server-name>

# Create backup
python -m app.main backup create <server-name>

# Check system diagnostics
python -m app.main check

# Clean up orphaned PIDs
python -m app.main cleanup <server-name>
```

### DNS Management

```bash
# Update DNS records (detect IP and push to Cloudflare)
python -m app.main dns update <server-name>

# Force update even if IP hasn't changed
python -m app.main dns update <server-name> --force

# Check DNS status
python -m app.main dns status <server-name>

# Test DNS connection and API credentials
python -m app.main dns test <server-name>
```

### RCON Console

```bash
# Enter interactive RCON console
python -m app.main console <server-name>

# Send single command
python -m app.main send <server-name> "say Hello"
```

### Tunnel Management

```bash
# Check tunnel status
python -m app.main tunnel status <server-name>

# Start tunnel manually
python -m app.main tunnel start <server-name>

# Stop tunnel
python -m app.main tunnel stop <server-name>

# Clean up orphaned tunnel
python -m app.main tunnel cleanup <server-name>
```

### Java Management

```bash
# List all Java profiles
python -m app.main java list

# Validate all Java profiles
python -m app.main java validate
```

### System Tools

```bash
# Run system diagnostics
python -m app.main check

# View system information
python -m app.main info

# Network diagnostics
python -m app.main diagnose <server-name>
```

## Development Status

### ✅ Phase 1 - Core Functionality (Completed - v0.1.0)
**Overall Completion**: 100%

**Completed Objectives**:
- ✅ **Module Architecture** (100%)
  - Data models for server config, Java profiles, backup policies
  - Utils layer with YAML parsing, file operations, process management
  - Core layer with scanner, launcher, resolvers, managers
  
- ✅ **Server Management** (95%)
  - Multi-instance directory scanning and validation
  - Server launcher with Forge 1.17+ special detection
  - Process lifecycle management (start/stop/restart)
  - Runtime state tracking (PID, uptime, status)
  
- ✅ **Java System** (100%)
  - Global Java registry with profile management
  - Per-server Java version assignment
  - Path resolution and validation
  
- ✅ **Backup System** (90%)
  - Policy-based backup execution
  - Selective archiving with include/exclude patterns
  - Retention management (keep last N / keep days)
  - Pre/post backup hooks
  
- ✅ **DNS Integration** (95%)
  - Cloudflare API integration with A + SRV records
  - DuckDNS integration with basic A records
  - Automatic IP detection and update
  - Custom port configuration
  - Status tracking and error logging
  
- ✅ **CLI Interface** (92%)
  - Rich terminal UI with colored tables
  - All core commands implemented
  - Subcommand structure for DNS and Java
  - Convenience wrapper scripts

**Key Achievements**:
- ✅ Standardized server instance directory structure
- ✅ Unified path interface for cross-module access
- ✅ Smart Forge detection with special launch mode
- ✅ Cloudflare SRV records for port-free connection
- ✅ Comprehensive documentation (SPEC, DNS guides, packaging)

**Known Limitations**:
- ⚠️ Windows primary support (Linux/Mac experimental)
- ⚠️ No GUI (CLI only)
- ⚠️ No sub-workflow system
- ⚠️ No automatic server type detection beyond Forge

### ✅ Phase 2 - Enhanced Features (Completed - v0.2.0)
**Overall Completion**: 90%

**Completed Objectives**:
- ✅ **RCON Integration** (100%)
  - Interactive console mode
  - Single command execution
  - Auto-configuration with server.properties
  
- ✅ **PlayIt.gg Tunnel Support** (95%)
  - Auto-start/stop with server lifecycle
  - Agent integration
  - DNS combination support
  - Orphaned process detection
  
- ✅ **Interactive CLI** (100%)
  - Menu-driven interface
  - Smart server selection
  - Confirmation prompts
  - Hierarchical navigation
  
- ✅ **System Diagnostics** (100%)
  - Environment validation
  - Configuration checking
  - Dependency verification
  - Fix suggestions
  
- ✅ **First-Run Initialization** (100%)
  - Automatic directory creation
  - Configuration template generation
  - Guided setup documentation
  
- ✅ **Orphaned Process Management** (100%)
  - Auto-detection of stale PIDs
  - Automatic cleanup
  - Manual cleanup command
  
- ✅ **Network Diagnostics** (85%)
  - DNS resolution testing
  - Connection troubleshooting
  - Issue identification

### 📅 Phase 3 - Advanced Features (Planned)
**Target**: v0.3.0

**Planned Objectives**:
- 🔹 **Intelligent Detection** (Target: 85%)
  - Auto-detect server.jar and loader types
  - Generate server.yml drafts for new servers
  - Parse .bat/.sh scripts for configuration hints
  
- 🔹 **Loader Adapters** (Target: 75%)
  - Dedicated adapters for Vanilla, Paper, Purpur, Spigot
  - Fabric and NeoForge special handling
  - Version-specific launch parameter generation
  
- 🔹 **Enhanced Workflows** (Target: 80%)
  - Scheduled backups with cron-like syntax
  - Auto-restart on crash detection
  - EULA auto-initialization
  
- 🔹 **Path Management** (Target: 70%)
  - World folder auto-detection and listing
  - Mod/config directory navigation
  - Resource pack and datapack management
  
- 🔹 **Logging System** (Target: 65%)
  - Centralized log aggregation
  - Log parsing for error detection
  - Real-time log streaming

### 📅 Phase 3 - Advanced Features (Future)
**Target**: v1.0.0

**Planned Objectives**:
- 🔹 **Web UI / TUI** - Browser-based or terminal UI dashboard
- 🔹 **RCON Integration** - Remote console control
- 🔹 **Server Resource Monitoring** - CPU, RAM, disk usage tracking
- 🔹 **Update Manager** - Automatic server software updates
- 🔹 **Multi-Platform Support** - Full Linux and macOS compatibility
- 🔹 **Plugin System** - Extensible architecture for custom modules

## Configuration Guide

### Server Configuration (server.yml)

Each server has a `server.yml` in its instance directory. Key sections:

```yaml
meta:
  name: "my-server"
  display_name: "My Survival Server"
  description: "Local survival world"

server:
  root_dir: "server"              # Minecraft working directory
  startup_target: "server.jar"    # JAR file or "FORGE_SPECIAL"
  loader: "forge"                 # vanilla, paper, forge, fabric, etc.

java:
  mode: "profile"                 # Use profile from registry
  profile: "java21"               # Profile name

rcon:
  enabled: false                  # Enable RCON remote console
  host: "localhost"
  port: 25575
  password: ""                    # Must match server.properties

tunnel:
  enabled: false                  # Enable PlayIt.gg tunnel
  type: "playit"                  # playit, ngrok, cloudflared
  auto_start: true                # Start/stop with server
  executable_path: ""             # Agent path (optional, uses global config)

launch:
  min_memory: "2G"
  max_memory: "8G"
  jvm_args: []                    # Additional JVM arguments
  server_args: ["nogui"]          # Server arguments

backup:
  enabled: true
  provider: "internal"            # internal, external, disabled
  retention:
    keep_last: 10                 # Keep last 10 backups
    keep_days: 14                 # Keep backups from last 14 days
  include:
    - "world*"                    # Backup patterns
    - "server.properties"
  exclude:
    - "logs/**"                   # Exclude patterns
    - "libraries/**"

dns:
  enabled: true
  mode: "cloudflare"              # cloudflare, duckdns
  domain: "mc.example.com"        # Your domain
  server_port: 25565              # Server port
  srv_record:
    enabled: true                 # Enable SRV record
    port: 25565                   # SRV port (usually same as server_port)
  config:
    api_token: "YOUR_TOKEN"       # Cloudflare API token
    zone_id: "YOUR_ZONE_ID"       # Cloudflare zone ID
```

### Java Registry (config/java_registry.yml)

Global Java installation registry:

```yaml
profiles:
  java8:
    path: "C:/Program Files/Java/jdk1.8.0_381/bin/java.exe"
    version: "8"
    description: "Java 8 - For Minecraft 1.12.2 and earlier"

  java17:
    path: "C:/Program Files/Java/jdk-17/bin/java.exe"
    version: "17"
    description: "Java 17 - For Minecraft 1.17-1.20"

  java21:
    path: "C:/Program Files/Java/jdk-21/bin/java.exe"
    version: "21"
    description: "Java 21 - For Minecraft 1.20.5+"
```

## Building and Distribution

### Build Standalone Executable (.exe)

```powershell
# Quick build (recommended)
.\build.ps1

# Or use batch file
build.bat

# Output: dist/mc-server-framework/mc-server-framework.exe
```

The packaged version includes:
- Standalone executable (~7MB, no Python required)
- Configuration templates
- First-run initialization
- All dependencies bundled

### Create Release Package

```powershell
# After building, create distributable ZIP
.\package.ps1 -Version "v0.2.0"

# Output: release/MC-Server-Framework-v0.2.0-Windows-x64.zip
```

Release package includes:
- Executable and dependencies
- Pre-created directory structure
- User documentation (使用說明.txt)
- README and LICENSE

See [BUILD.md](BUILD.md) for detailed build instructions and troubleshooting.

## Documentation

- **System Specification**: [docs/SPEC.md](docs/SPEC.md) - Complete project specification
- **Build Guide**: [BUILD.md](BUILD.md) - PyInstaller packaging and distribution
- **Quick Build**: [QUICK_BUILD.md](QUICK_BUILD.md) - Fast build reference
- **Getting Started**: Run `python -m app.main info` for in-app documentation

## Troubleshooting

### Server Won't Start
1. Validate Java profile: `python -m app.main java validate`
2. Check if `server.jar` exists in `servers/<name>/server/`
3. Review logs: `servers/<name>/runtime/session.log`
4. For Forge 1.17+: Ensure `libraries/` directory exists

### DNS Update Failed
1. Test connection: `python -m app.main dns test <server>`
2. Verify API Token and Zone ID in `server.yml`
3. Check if domain exists in Cloudflare
4. Ensure Cloudflare Proxy is disabled (DNS only mode)

### Backup Not Working
1. Check `server.yml` backup configuration
2. Verify `backups/` directory has write permissions
3. Review backup provider setting (internal/external/disabled)

### Connection Issues

**Players cannot connect to your server? Follow these steps:**

#### 1. Verify Server Configuration
```bash
# Check server.properties configuration
# Look for these settings in servers/<name>/server/server.properties:
server-ip=0.0.0.0        # Allow external connections (or leave empty)
server-port=25565        # Default port, must match your DNS settings
online-mode=true         # Set to false only for offline/cracked servers
```

The framework will check this automatically on startup and warn you if misconfigured.

#### 2. Test DNS Resolution
```bash
# Test DNS configuration
python -m app.main dns test <server-name>

# Manually check DNS with nslookup (Windows)
nslookup mc.yourdomain.com

# Should return your public IP address
```

#### 3. Firewall Configuration

**Windows Defender Firewall:**
```powershell
# Allow Java through Windows Firewall (run as Administrator)
New-NetFirewallRule -DisplayName "Minecraft Server" -Direction Inbound -Program "C:\Program Files\Java\jdk-21\bin\java.exe" -Action Allow

# Or allow specific port
New-NetFirewallRule -DisplayName "Minecraft Port 25565" -Direction Inbound -LocalPort 25565 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Minecraft Port 25565 UDP" -Direction Inbound -LocalPort 25565 -Protocol UDP -Action Allow
```

#### 4. Router Port Forwarding

If your server is behind a router (most home networks):

1. Find your local IP address:
   ```powershell
   ipconfig
   # Look for "IPv4 Address" under your active network adapter
   ```

2. Login to your router admin panel (usually http://192.168.1.1 or http://192.168.0.1)

3. Navigate to "Port Forwarding" or "Virtual Server" settings

4. Add new rule:
   - **Service Name**: Minecraft Server
   - **External Port**: 25565
   - **Internal IP**: Your computer's local IP (from step 1)
   - **Internal Port**: 25565
   - **Protocol**: TCP/UDP or Both

5. Save and restart router if required

#### 5. ISP Restrictions

Some ISPs block common server ports or don't allow hosting:

```bash
# Test if your ISP allows port 25565
# Use online port checker: https://www.yougetsignal.com/tools/open-ports/

# Alternative: Use non-standard port
# Edit servers/<name>/server/server.properties:
server-port=25566        # Or any port above 1024

# Update server.yml:
dns:
  server_port: 25566
  srv_record:
    port: 25566
```

#### 6. Connection Testing Checklist

Test connections in this order:

✅ **Local Connection** (same computer):
```
Direct Connect: localhost:25565
```

✅ **LAN Connection** (same network):
```
Direct Connect: <your-local-ip>:25565
Example: 192.168.1.100:25565
```

✅ **External Connection** (internet):
```
Direct Connect: <your-public-ip>:25565
Get public IP: https://api.ipify.org

Then test domain:
Direct Connect: mc.yourdomain.com
```

#### 7. Common Error Messages

**"Connection timed out"**
- Firewall blocking connection
- Router port forwarding not configured
- Server not running or wrong port

**"Connection refused"**  
- Server not running
- Wrong port number
- server-ip set to localhost/127.0.0.1

**"Unknown host"**
- DNS not propagated yet (wait 5-10 minutes after DNS update)
- Domain name typo
- DNS update failed (check `dns test` output)

**"Outdated client/server"**
- Minecraft version mismatch between server and client
- Not a connection issue

#### 8. Generate Diagnostic Report

```bash
# Check server status
python -m app.main status <server-name>

# View DNS status
python -m app.main dns status <server-name>

# Test DNS connection
python -m app.main dns test <server-name>

# Check server logs
python -m app.main logs <server-name> --lines 100
```

**Still not working?** Check:
- Server logs: `servers/<name>/server/logs/latest.log`
- Framework logs: `servers/<name>/runtime/session.log`
- Crash reports: `servers/<name>/server/crash-reports/`

## License

This project is under a private license. Unauthorized copying, modification, or distribution is prohibited.

---

**Project maintained by**: U.E.P (Unforgettableeternalproject)  
**Repository**: https://github.com/Unforgettableeternalproject/MC-Server-Framework

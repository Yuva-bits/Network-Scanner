# WiFi Scanner Project

A network security scanning tool for authorized penetration testing.

## Important Warning
**Only use on networks you own or have permission to test. Unauthorized use is illegal.**

## What it does

- **Network Scanner** (`network_scanner.py`) - Scans networks to find devices, open ports, and security issues
- **Tool Installer** (`install_security_tools.py`) - Installs security tools like nmap, nikto, and metasploit

## Techniques Used

### Network Discovery
- **Ping Sweeps** - ICMP ping to discover live hosts
- **ARP Table Analysis** - MAC address discovery
- **Network Interface Detection** - Automatic interface enumeration
- **CIDR Network Detection** - Subnet range identification

### Port Scanning
- **TCP Connect Scans** - Full TCP connection attempts
- **Multi-threaded Scanning** - Parallel port scanning for speed
- **Common Port Targeting** - Focuses on ports 21, 22, 23, 25, 53, 80, 110, 443, 993, 995, 3389

### Service Enumeration
- **Banner Grabbing** - Service version identification
- **FTP Enumeration** - Anonymous login testing
- **SSH Enumeration** - SSH service detection
- **HTTP Enumeration** - Web server analysis
- **SMB Enumeration** - Windows file sharing detection

### Security Assessment
- **OS Fingerprinting** - Operating system detection
- **Vulnerability Scanning** - Basic security flaw identification
- **Default Credential Testing** - Common username/password combinations
- **Service Version Analysis** - Known vulnerability matching

### Reporting
- **JSON Report Generation** - Machine-readable security reports
- **Risk Assessment** - Vulnerability severity scoring
- **Hostname Resolution** - DNS lookups for device identification

## How to use

1. Run the network scanner:
   ```bash
   python3 src/network_scanner.py
   ```

2. Install additional security tools (optional):
   ```bash
   python3 src/install_security_tools.py
   ```

## Requirements

- Python 3.6+
- Linux or macOS
- Admin privileges (for installing security tools)

## Features

- Find devices on your network
- Scan for open ports and services
- Check for common vulnerabilities
- Generate security reports
- Install penetration testing tools

## Legal Notice

This tool is for educational and authorized testing only. 

## Author
Yuuvashree Senthilmurugan

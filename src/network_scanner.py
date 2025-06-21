#!/usr/bin/env python3

import os
import sys
import subprocess
import re
import time
import ipaddress
import platform
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
import json
import base64

# ETHICAL USAGE WARNING
print("-" * 80)
print("____ETHICAL USAGE WARNING____")
print("This tool is for educational and authorized penetration testing ONLY!")
print("Only use on networks and devices you OWN or have EXPLICIT permission to test.")
print("Unauthorized access to computer systems is ILLEGAL and UNETHICAL.")
print("-" * 80)
print()

class AdvancedNetworkScanner:
    def __init__(self):
        self.network_interface = None
        self.network_cidr = None
        self.devices = []
        self.os_type = platform.system().lower()
        self.common_passwords = [
            'admin', 'password', '123456', 'root', 'toor', 'pass', 'test',
            'guest', 'user', '1234', 'default', '', 'login', 'changeme'
        ]
        self.common_usernames = [
            'admin', 'root', 'user', 'guest', 'administrator', 'test', 'demo'
        ]
    
    def get_network_interfaces(self):
        """Get available network interfaces based on OS"""
        interfaces = []
        
        if self.os_type == 'darwin':  # macOS
            result = subprocess.run(['networksetup', '-listallhardwareports'], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                # Parse interfaces from macOS output
                pattern = r'Hardware Port: (.*?)\nDevice: (.*?)\n'
                matches = re.findall(pattern, result.stdout)
                interfaces = [{'name': device, 'description': hw_port} 
                             for hw_port, device in matches]
        elif self.os_type == 'linux':
            # For Linux, list interfaces in /sys/class/net/
            if os.path.exists('/sys/class/net/'):
                for interface in os.listdir('/sys/class/net/'):
                    if interface != 'lo':  # Skip loopback
                        interfaces.append({'name': interface, 'description': interface})
        else:
            print(f"OS {self.os_type} not fully supported yet.")
            
        return interfaces
    
    def select_interface(self):
        """Let user select a network interface"""
        interfaces = self.get_network_interfaces()
        
        if not interfaces:
            print("No network interfaces found.")
            sys.exit(1)
            
        print("Available Network Interfaces:")
        for i, interface in enumerate(interfaces, 1):
            print(f"{i}. {interface['name']} - {interface['description']}")
            
        while True:
            try:
                choice = int(input("\nSelect interface number: "))
                if 1 <= choice <= len(interfaces):
                    self.network_interface = interfaces[choice-1]['name']
                    break
                else:
                    print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a number.")
    
    def get_network_cidr(self):
        """Determine the network CIDR based on selected interface"""
        if self.os_type == 'darwin':  # macOS
            try:
                # Get IP address
                ip_cmd = subprocess.run(['ipconfig', 'getifaddr', self.network_interface], 
                                      capture_output=True, text=True)
                if ip_cmd.returncode != 0:
                    raise Exception(f"Could not get IP for {self.network_interface}")
                
                ip_address = ip_cmd.stdout.strip()
                
                # Get subnet mask
                subnet_cmd = subprocess.run(['ipconfig', 'getpacket', self.network_interface], 
                                          capture_output=True, text=True)
                subnet_match = re.search(r'subnet_mask\s+\(ip\):\s+(\d+\.\d+\.\d+\.\d+)', subnet_cmd.stdout)
                if not subnet_match:
                    raise Exception("Could not determine subnet mask")
                
                subnet_mask = subnet_match.group(1)
                
                # Convert subnet mask to CIDR notation
                subnet_bits = sum([bin(int(x)).count('1') for x in subnet_mask.split('.')])
                
                # Create network with CIDR
                ip_parts = ip_address.split('.')
                network_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/{subnet_bits}"
                self.network_cidr = network_address
                
                return network_address
                
            except Exception as e:
                print(f"Error determining network CIDR: {e}")
                self.network_cidr = input("Enter network CIDR manually (e.g., 192.168.1.0/24): ")
                return self.network_cidr
        else:
            # For other operating systems, ask user to input
            self.network_cidr = input("Enter network CIDR (e.g., 192.168.1.0/24): ")
            return self.network_cidr
    
    def advanced_scan_network(self):
        """Advanced network scan with OS detection and service enumeration"""
        if not self.network_cidr:
            self.get_network_cidr()
            
        print(f"Advanced Network Scan - {self.network_cidr}")
        print("Press Ctrl+C at any time to stop the scan")
        
        try:
            network = ipaddress.IPv4Network(self.network_cidr, strict=False)
            self.devices = []
            total_hosts = list(network.hosts())
            
            # Use ThreadPoolExecutor for faster scanning
            with ThreadPoolExecutor(max_workers=20) as executor:
                results = list(executor.map(self.scan_host_advanced, total_hosts))
                
            # Filter out None results
            self.devices = [device for device in results if device is not None]
            
            print(f"Advanced scan complete! Found {len(self.devices)} devices.")
            if self.devices:
                self.display_advanced_devices()
            else:
                print("No devices found with advanced scanning.")
                
        except KeyboardInterrupt:
            print(f"Scan interrupted by user.")
            print(f"Found {len(self.devices)} devices before interruption.")
            if self.devices:
                self.display_advanced_devices()
        except Exception as e:
            print(f"Error during advanced scan: {e}")
    
    def scan_host_advanced(self, ip):
        """Advanced scan of a single host"""
        ip_str = str(ip)
        
        # Skip network and broadcast addresses
        if ip_str.endswith('.0') or ip_str.endswith('.255'):
            return None
        
        # Quick ping check first
        ping_cmd = ['ping', '-c', '1', '-W', '1'] if self.os_type != 'darwin' else ['ping', '-c', '1', '-t', '1']
        ping_cmd.append(ip_str)
        
        try:
            result = subprocess.run(ping_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            
            if result.returncode == 0:
                device_info = {
                    'ip': ip_str,
                    'mac': self.get_mac_address(ip_str),
                    'hostname': self.get_hostname(ip_str),
                    'os': self.detect_os(ip_str),
                    'open_ports': self.quick_port_scan(ip_str),
                    'services': {}
                }
                
                # Get service information for open ports
                for port in device_info['open_ports']:
                    service_info = self.identify_service(ip_str, port)
                    if service_info:
                        device_info['services'][port] = service_info
                
                print(f"Found: {ip_str} - {device_info.get('hostname', 'Unknown')} - {device_info.get('os', 'Unknown OS')}")
                return device_info
                
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            pass
        except Exception as e:
            print(f"Error scanning {ip_str}: {e}")
        
        return None
    
    def detect_os(self, ip):
        """Basic OS detection using various techniques"""
        try:
            # TTL-based OS detection
            ping_cmd = ['ping', '-c', '1', ip]
            result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                ttl_match = re.search(r'ttl=(\d+)', result.stdout, re.IGNORECASE)
                if ttl_match:
                    ttl = int(ttl_match.group(1))
                    if ttl <= 64:
                        return "Linux/Unix"
                    elif ttl <= 128:
                        return "Windows"
                    else:
                        return "Unknown"
        except:
            pass
        
        return "Unknown"
    
    def quick_port_scan(self, ip):
        """Quick scan of common ports"""
        common_ports = [21, 22, 23, 25, 53, 80, 135, 139, 443, 445, 993, 995, 1723, 3389, 5900, 8080]
        open_ports = []
        
        for port in common_ports:
            if self.is_port_open(ip, port, timeout=1):
                open_ports.append(port)
        
        return open_ports
    
    def is_port_open(self, ip, port, timeout=3):
        """Check if a port is open using socket connection"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def identify_service(self, ip, port):
        """Try to identify the service running on a port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((ip, port))
            
            # Send HTTP request for web services
            if port in [80, 8080, 443]:
                sock.send(b"GET / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n")
                response = sock.recv(1024).decode('utf-8', errors='ignore')
                if 'Server:' in response:
                    server_match = re.search(r'Server:\s*([^\r\n]+)', response)
                    if server_match:
                        return f"HTTP - {server_match.group(1).strip()}"
                return "HTTP Service"
            
            # For SSH
            elif port == 22:
                response = sock.recv(1024).decode('utf-8', errors='ignore')
                if 'SSH' in response:
                    return f"SSH - {response.strip()}"
                return "SSH Service"
            
            # For FTP
            elif port == 21:
                response = sock.recv(1024).decode('utf-8', errors='ignore')
                if '220' in response:
                    return f"FTP - {response.strip()}"
                return "FTP Service"
            
            sock.close()
            return self.get_service_name(port)
            
        except:
            return self.get_service_name(port)
    
    def get_hostname(self, ip):
        """Get hostname for IP address"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return "Unknown"
    
    def display_advanced_devices(self):
        """Display all found devices with advanced information"""
        if not self.devices:
            print("No devices found or scan not performed.")
            return
            
        print("\nDISCOVERED NETWORK DEVICES")
        
        for i, device in enumerate(self.devices, 1):
            ip = device.get('ip', 'Unknown')
            mac = device.get('mac') or 'Unknown'
            hostname = device.get('hostname') or 'Unknown'
            os_type = device.get('os') or 'Unknown'
            open_ports = device.get('open_ports', [])
            services = device.get('services', {})
            
            print(f"\nDevice #{i}")
            print(f"   IP: {ip}")
            print(f"   MAC: {mac}")
            print(f"   Hostname: {hostname}")
            print(f"   OS: {os_type}")
            print(f"   Open Ports: {', '.join(map(str, open_ports)) if open_ports else 'None detected'}")
            
            if services:
                print("   Services:")
                for port, service in services.items():
                    print(f"     Port {port}: {service}")
    
    def select_target_advanced(self):
        """Let user select a target device for advanced assessment"""
        if not self.devices:
            print("No devices available. Run an advanced scan first.")
            return None
            
        print("\nSelect a target device for security assessment:")
        print("WARNING: Only test devices you own or have explicit permission to test!")
        
        for i, device in enumerate(self.devices, 1):
            ip = device.get('ip', 'Unknown')
            hostname = device.get('hostname', 'Unknown')
            os_type = device.get('os', 'Unknown')
            ports = len(device.get('open_ports', []))
            print(f"{i}. {ip} - {hostname} - {os_type} - {ports} open ports")
            
        while True:
            try:
                choice = int(input("\nEnter device number (0 to cancel): "))
                if choice == 0:
                    return None
                if 1 <= choice <= len(self.devices):
                    target = self.devices[choice-1]
                    print(f"\nYou selected: {target['ip']} ({target.get('hostname', 'Unknown')})")
                    confirm = input("Do you OWN this device or have EXPLICIT permission to test it? (yes/no): ")
                    if confirm.lower() in ['yes', 'y']:
                        return target
                    else:
                        print("Testing cancelled. Only test devices you own or have permission to test.")
                        return None
                else:
                    print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a number.")
    
    def run_advanced_assessment(self, target):
        """Run comprehensive security assessment"""
        if not target:
            print("No target selected.")
            return
            
        ip = target.get('ip')
        print(f"\nCOMPREHENSIVE SECURITY ASSESSMENT - {ip}")
        
        # Detailed port scan
        print("\n1. Running detailed port scan...")
        self.detailed_port_scan(ip)
        
        # Service enumeration
        print("\n2. Enumerating services...")
        self.enumerate_services(target)
        
        # Vulnerability checks
        print("\n3. Checking for common vulnerabilities...")
        self.check_vulnerabilities(target)
        
        # Credential testing (if applicable)
        print("\n4. Testing default credentials...")
        self.test_default_credentials(target)
    
    def detailed_port_scan(self, ip):
        """Detailed scan of all ports 1-1000"""
        open_ports = []
        
        try:
            for port in range(1, 1001):
                if self.is_port_open(ip, port, timeout=0.5):
                    service = self.identify_service(ip, port)
                    open_ports.append((port, service))
                    print(f"Port {port} OPEN - {service}")
        except KeyboardInterrupt:
            print("Port scan interrupted.")
        
        if not open_ports:
            print("No additional open ports found.")
    
    def enumerate_services(self, target):
        """Enumerate services on open ports"""
        open_ports = target.get('open_ports', [])
        ip = target['ip']
        
        for port in open_ports:
            if port == 21:  # FTP
                self.enumerate_ftp(ip, port)
            elif port == 22:  # SSH
                self.enumerate_ssh(ip, port)
            elif port in [80, 8080, 443]:  # HTTP/HTTPS
                self.enumerate_http(ip, port)
            elif port == 139 or port == 445:  # SMB
                self.enumerate_smb(ip, port)
    
    def enumerate_ftp(self, ip, port):
        """Enumerate FTP service"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, port))
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            print(f"   FTP Banner: {banner.strip()}")
            
            # Check for anonymous login
            sock.send(b"USER anonymous\r\n")
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            if '331' in response:
                sock.send(b"PASS anonymous@example.com\r\n")
                response = sock.recv(1024).decode('utf-8', errors='ignore')
                if '230' in response:
                    print("   WARNING: Anonymous FTP login ALLOWED!")
                else:
                    print("   Anonymous FTP login denied")
            
            sock.close()
        except Exception as e:
            print(f"   Error enumerating FTP: {e}")
    
    def enumerate_ssh(self, ip, port):
        """Enumerate SSH service"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, port))
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            print(f"   SSH Banner: {banner.strip()}")
            
            # Extract SSH version
            if 'SSH-' in banner:
                version_match = re.search(r'SSH-([\d.]+)', banner)
                if version_match:
                    version = version_match.group(1)
                    print(f"   SSH Version: {version}")
                    
                    # Check for known vulnerable versions
                    if version.startswith('1.'):
                        print("   WARNING: SSH version 1.x detected - VULNERABLE!")
            
            sock.close()
        except Exception as e:
            print(f"   Error enumerating SSH: {e}")
    
    def enumerate_http(self, ip, port):
        """Enumerate HTTP service"""
        try:
            protocol = "https" if port == 443 else "http"
            import urllib.request
            import urllib.error
            
            # Get server header
            req = urllib.request.Request(f"{protocol}://{ip}:{port}/")
            req.add_header('User-Agent', 'Security-Scanner/1.0')
            
            try:
                response = urllib.request.urlopen(req, timeout=5)
                headers = response.headers
                
                print(f"   Server: {headers.get('Server', 'Unknown')}")
                print(f"   Status: {response.status} {response.reason}")
                
                # Check for common directories
                common_dirs = ['/admin', '/login', '/phpmyadmin', '/wp-admin', '/backup']
                for directory in common_dirs:
                    try:
                        test_req = urllib.request.Request(f"{protocol}://{ip}:{port}{directory}")
                        test_resp = urllib.request.urlopen(test_req, timeout=2)
                        print(f"   Found directory: {directory}")
                    except:
                        pass
                        
            except urllib.error.HTTPError as e:
                print(f"   HTTP Error: {e.code} {e.reason}")
            except Exception as e:
                print(f"   Connection error: {e}")
                
        except Exception as e:
            print(f"   Error enumerating HTTP: {e}")
    
    def enumerate_smb(self, ip, port):
        """Enumerate SMB service"""
        print(f"   SMB service detected on port {port}")
        # Basic SMB enumeration would require additional libraries
        print("   INFO: SMB enumeration requires additional tools (smbclient, enum4linux)")
    
    def check_vulnerabilities(self, target):
        """Check for common vulnerabilities"""
        ip = target['ip']
        open_ports = target.get('open_ports', [])
        
        vulnerabilities = []
        
        # Check for unencrypted services
        if 21 in open_ports:
            vulnerabilities.append("FTP (unencrypted) service running")
        if 23 in open_ports:
            vulnerabilities.append("Telnet (unencrypted) service running")
        if 80 in open_ports and 443 not in open_ports:
            vulnerabilities.append("HTTP without HTTPS - unencrypted web traffic")
        
        # Check for dangerous services
        if 445 in open_ports:
            vulnerabilities.append("SMB service exposed - potential for lateral movement")
        if 3389 in open_ports:
            vulnerabilities.append("RDP service exposed - brute force target")
        
        if vulnerabilities:
            print("   WARNING: Potential vulnerabilities found:")
            for vuln in vulnerabilities:
                print(f"     • {vuln}")
        else:
            print("   No obvious vulnerabilities detected in basic scan")
    
    def test_default_credentials(self, target):
        """Test common default credentials"""
        ip = target['ip']
        open_ports = target.get('open_ports', [])
        
        print("   WARNING: This is for authorized testing only!")
        
        # Test SSH if available
        if 22 in open_ports:
            self.test_ssh_credentials(ip)
        
        # Test FTP if available
        if 21 in open_ports:
            self.test_ftp_credentials(ip)
    
    def test_ssh_credentials(self, ip):
        """Test SSH with common credentials"""
        print("     SSH credential testing would require paramiko library")
        print("     Common combinations to test manually:")
        for username in ['root', 'admin', 'user']:
            for password in ['password', '123456', 'admin']:
                print(f"       {username}:{password}")
    
    def test_ftp_credentials(self, ip):
        """Test FTP with common credentials"""
        try:
            # Test anonymous login
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, 21))
            sock.recv(1024)  # Get banner
            
            sock.send(b"USER anonymous\r\n")
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            if '331' in response:
                sock.send(b"PASS anonymous@test.com\r\n")
                response = sock.recv(1024).decode('utf-8', errors='ignore')
                if '230' in response:
                    print("     WARNING: Anonymous FTP access SUCCESSFUL!")
                else:
                    print("     Anonymous FTP access denied")
            
            sock.close()
        except Exception as e:
            print(f"     Error testing FTP credentials: {e}")
    
    def get_mac_address(self, ip):
        """Try to get MAC address for an IP"""
        try:
            if self.os_type == 'darwin':  # macOS
                # Use arp on macOS
                arp_cmd = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=1)
                if arp_cmd.returncode == 0:
                    mac_match = re.search(r'(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))', arp_cmd.stdout)
                    if mac_match:
                        return mac_match.group(1)
            else:
                # For Linux and others
                arp_cmd = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=1)
                if arp_cmd.returncode == 0:
                    mac_match = re.search(r'(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))', arp_cmd.stdout)
                    if mac_match:
                        return mac_match.group(1)
        except:
            pass
        return None
    
    def get_service_name(self, port):
        """Return common service name for a port"""
        services = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            443: "HTTPS",
            445: "SMB",
            3389: "RDP",
            8080: "HTTP Alternate"
        }
        return services.get(port, "Unknown")

    def scan_network(self):
        """Basic network scan (original method for compatibility)"""
        if not self.network_cidr:
            self.get_network_cidr()
            
        print(f"Scanning network {self.network_cidr}...")
        print("Press Ctrl+C at any time to stop the scan")
        
        try:
            network = ipaddress.IPv4Network(self.network_cidr, strict=False)
            
            # Prepare for storing results
            self.devices = []
            total_hosts = list(network.hosts())
            
            # Use ping for basic scanning
            for i, ip in enumerate(total_hosts):
                ip_str = str(ip)
                
                # Skip network and broadcast addresses
                if ip_str.endswith('.0') or ip_str.endswith('.255'):
                    continue
                
                # Show progress
                progress = f"[{i+1}/{len(total_hosts)}]"
                print(f"{progress} Checking {ip_str}...", end='\r')
                
                # Use ping with short timeout for speed
                ping_cmd = ['ping', '-c', '1', '-W', '1']
                if self.os_type == 'darwin':  # macOS
                    ping_cmd = ['ping', '-c', '1', '-t', '1']
                    
                ping_cmd.append(ip_str)
                
                try:
                    result = subprocess.run(ping_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
                    
                    if result.returncode == 0:
                        # Try to get MAC address for the IP
                        mac = self.get_mac_address(ip_str)
                        device_info = {'ip': ip_str, 'mac': mac}
                        
                        # Try to get hostname
                        try:
                            hostname_cmd = subprocess.run(['host', ip_str], capture_output=True, text=True, timeout=1)
                            if hostname_cmd.returncode == 0 and "not found" not in hostname_cmd.stdout:
                                hostname_match = re.search(r'pointer\s+([^\s]+)\.', hostname_cmd.stdout)
                                if hostname_match:
                                    device_info['hostname'] = hostname_match.group(1)
                        except:
                            pass  # Ignore hostname lookup failures
                        
                        self.devices.append(device_info)
                        device_name = device_info.get('hostname', 'Unknown')
                        print(f"{progress} ✓ Found: {ip_str} ({mac if mac else 'Unknown MAC'}) - {device_name}".ljust(80))
                        
                except subprocess.TimeoutExpired:
                    # Skip if ping times out
                    pass
                except KeyboardInterrupt:
                    print(f"\n\nScan interrupted by user at {ip_str}")
                    print(f"Scanned {i+1} of {len(total_hosts)} addresses")
                    break
            
            print(f"Scan complete! Found {len(self.devices)} devices.")
            if self.devices:
                self.display_devices()
            else:
                print("No devices responded to ping.")
            
        except KeyboardInterrupt:
            print(f"Scan interrupted by user.")
            print(f"Found {len(self.devices)} devices before interruption.")
            if self.devices:
                self.display_devices()
        except Exception as e:
            print(f"Error during scan: {e}")

    def display_devices(self):
        """Display all found devices (basic format)"""
        if not self.devices:
            print("No devices found or scan not performed.")
            return
            
        print("Connected Devices:")
        print(f"{'IP Address':<16} {'MAC Address':<20} {'Hostname':<30}")
        print("-" * 66)
        
        for i, device in enumerate(self.devices, 1):
            ip = device.get('ip', 'Unknown')
            mac = device.get('mac') or 'Unknown'
            hostname = device.get('hostname') or 'Unknown'
            print(f"{ip:<16} {mac:<20} {hostname:<30}")
    
    def select_target(self):
        """Let user select a target device (basic method)"""
        if not self.devices:
            print("No devices available. Run a scan first.")
            return None
            
        print("\nSelect a target device:")
        for i, device in enumerate(self.devices, 1):
            ip = device.get('ip', 'Unknown')
            mac = device.get('mac', 'Unknown')
            hostname = device.get('hostname', 'Unknown')
            print(f"{i}. {ip} - {mac} - {hostname}")
            
        while True:
            try:
                choice = int(input("\nEnter device number (0 to cancel): "))
                if choice == 0:
                    return None
                if 1 <= choice <= len(self.devices):
                    return self.devices[choice-1]
                else:
                    print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a number.")
    
    def run_security_assessment(self, target):
        """Run basic security assessment on target device"""
        if not target:
            print("No target selected.")
            return
            
        ip = target.get('ip')
        print(f"Basic Security Assessment for {ip}")
        self.scan_common_ports(ip)
        
    def scan_common_ports(self, ip):
        """Scan common ports on target IP"""
        common_ports = [21, 22, 23, 25, 53, 80, 443, 445, 3389, 8080]
        open_ports = []
        
        print("Press Ctrl+C to stop port scanning")
        
        try:
            for i, port in enumerate(common_ports):
                try:
                    progress = f"[{i+1}/{len(common_ports)}]"
                    print(f"{progress} Checking port {port}...", end='\r')
                    
                    cmd = ['nc', '-z', '-G', '1', ip, str(port)]
                    if self.os_type != 'darwin':
                        cmd = ['nc', '-z', '-w', '1', ip, str(port)]
                        
                    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
                    
                    if result.returncode == 0:
                        open_ports.append(port)
                        service = self.get_service_name(port)
                        print(f"{progress} ✓ Port {port} is OPEN ({service})".ljust(60))
                        
                except subprocess.TimeoutExpired:
                    # Skip if connection times out
                    pass
                except KeyboardInterrupt:
                    print(f"Port scan interrupted at port {port}")
                    break
                except:
                    # Skip any other errors
                    pass
                    
        except KeyboardInterrupt:
            print(f"Port scan interrupted by user.")
        
        print(f"Port scan complete!")
        if not open_ports:
            print("No common ports found open.")
        else:
            print(f"Open ports on {ip}:")
            for port in open_ports:
                service = self.get_service_name(port)
                print(f"- Port {port}: {service}")

    def generate_security_report(self, target, assessment_results=None):
        """Generate comprehensive security report"""
        if not target:
            print("No target selected for report generation.")
            return
        
        import datetime
        
        ip = target['ip']
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"security_report_{ip}_{timestamp}.txt"
        
        try:
            with open(filename, 'w') as f:
                # Header
                f.write("=" * 80 + "\n")
                f.write("COMPREHENSIVE SECURITY ASSESSMENT REPORT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Target: {ip}\n")
                f.write(f"Hostname: {target.get('hostname', 'Unknown')}\n")
                f.write(f"Assessment Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\nWARNING: This report contains sensitive security information.\n")
                f.write("WARNING: Only use for authorized penetration testing purposes.\n")
                f.write("=" * 80 + "\n\n")
                
                # Device Information
                f.write("1. DEVICE INFORMATION\n")
                f.write("-" * 30 + "\n")
                f.write(f"IP Address: {target.get('ip', 'Unknown')}\n")
                f.write(f"MAC Address: {target.get('mac', 'Unknown')}\n")
                f.write(f"Hostname: {target.get('hostname', 'Unknown')}\n")
                f.write(f"Operating System: {target.get('os', 'Unknown')}\n\n")
                
                # Open Ports and Services
                f.write("2. OPEN PORTS AND SERVICES\n")
                f.write("-" * 30 + "\n")
                open_ports = target.get('open_ports', [])
                services = target.get('services', {})
                
                if open_ports:
                    for port in open_ports:
                        service = services.get(port, self.get_service_name(port))
                        f.write(f"Port {port}: {service}\n")
                else:
                    f.write("No open ports detected in scan\n")
                f.write("\n")
                
                # Vulnerability Assessment
                f.write("3. VULNERABILITY ASSESSMENT\n")
                f.write("-" * 30 + "\n")
                vulnerabilities = self.assess_vulnerabilities(target)
                if vulnerabilities:
                    for vuln in vulnerabilities:
                        f.write(f"• {vuln}\n")
                else:
                    f.write("No obvious vulnerabilities detected\n")
                f.write("\n")
                
                # Security Recommendations
                f.write("4. SECURITY RECOMMENDATIONS\n")
                f.write("-" * 30 + "\n")
                recommendations = self.generate_recommendations(target)
                for rec in recommendations:
                    f.write(f"• {rec}\n")
                f.write("\n")
                
                # Risk Assessment
                f.write("5. RISK ASSESSMENT\n")
                f.write("-" * 30 + "\n")
                risk_level = self.calculate_risk_level(target)
                f.write(f"Overall Risk Level: {risk_level}\n")
                f.write(f"Risk Factors: {len(vulnerabilities)} vulnerabilities, {len(open_ports)} open ports\n\n")
                
                # Technical Details
                f.write("6. TECHNICAL DETAILS\n")
                f.write("-" * 30 + "\n")
                f.write("Scanning Methods Used:\n")
                f.write("• ICMP Ping Sweep\n")
                f.write("• TCP Port Scanning\n")
                f.write("• Service Enumeration\n")
                f.write("• Banner Grabbing\n")
                f.write("• OS Detection via TTL Analysis\n")
                f.write("• Default Credential Testing\n\n")
                
                # Disclaimer
                f.write("7. DISCLAIMER\n")
                f.write("-" * 30 + "\n")
                f.write("This report is generated for authorized security testing purposes only.\n")
                f.write("The results should be used to improve security posture.\n")
                f.write("Any unauthorized use of this information is strictly prohibited.\n\n")
                
                f.write("=" * 80 + "\n")
                f.write("END OF REPORT\n")
                f.write("=" * 80 + "\n")
            
            print(f"Security report generated: {filename}")
            print(f"Report includes device info, vulnerabilities, and recommendations")
            
        except Exception as e:
            print(f"Error generating report: {e}")
    
    def assess_vulnerabilities(self, target):
        """Assess vulnerabilities based on discovered services"""
        vulnerabilities = []
        open_ports = target.get('open_ports', [])
        
        # Check for unencrypted services
        if 21 in open_ports:
            vulnerabilities.append("FTP service running - transmits credentials in plaintext")
        if 23 in open_ports:
            vulnerabilities.append("Telnet service running - unencrypted remote access")
        if 80 in open_ports and 443 not in open_ports:
            vulnerabilities.append("HTTP without HTTPS - web traffic not encrypted")
        
        # Check for potentially dangerous services
        if 445 in open_ports:
            vulnerabilities.append("SMB service exposed - potential for ransomware/lateral movement")
        if 3389 in open_ports:
            vulnerabilities.append("RDP service exposed - common brute force target")
        if 22 in open_ports:
            vulnerabilities.append("SSH service exposed - ensure strong authentication")
        
        # Check for administrative interfaces
        if 8080 in open_ports:
            vulnerabilities.append("Alternative HTTP port active - may be admin interface")
        
        # Add generic recommendations based on port count
        if len(open_ports) > 10:
            vulnerabilities.append("Many ports open - consider principle of least privilege")
        
        return vulnerabilities
    
    def generate_recommendations(self, target):
        """Generate security recommendations"""
        recommendations = []
        open_ports = target.get('open_ports', [])
        
        # Port-specific recommendations
        if 21 in open_ports:
            recommendations.append("Disable FTP or use SFTP/FTPS for encrypted file transfer")
        if 23 in open_ports:
            recommendations.append("Replace Telnet with SSH for secure remote access")
        if 80 in open_ports and 443 not in open_ports:
            recommendations.append("Implement HTTPS with proper SSL/TLS certificates")
        if 445 in open_ports:
            recommendations.append("Secure SMB with proper authentication and access controls")
        if 3389 in open_ports:
            recommendations.append("Secure RDP with NLA, strong passwords, and IP restrictions")
        if 22 in open_ports:
            recommendations.append("Harden SSH: disable root login, use key authentication")
        
        # General recommendations
        recommendations.extend([
            "Implement network segmentation and firewalls",
            "Keep all software and systems updated",
            "Use strong, unique passwords with MFA where possible",
            "Monitor network traffic and logs for suspicious activity",
            "Conduct regular security assessments",
            "Implement intrusion detection/prevention systems"
        ])
        
        return recommendations
    
    def calculate_risk_level(self, target):
        """Calculate overall risk level"""
        open_ports = target.get('open_ports', [])
        vulnerabilities = self.assess_vulnerabilities(target)
        
        risk_score = 0
        
        # Risk factors
        risk_score += len(open_ports) * 2  # Each open port adds risk
        risk_score += len(vulnerabilities) * 5  # Each vulnerability adds more risk
        
        # High-risk services
        high_risk_ports = [21, 23, 445, 3389]
        for port in high_risk_ports:
            if port in open_ports:
                risk_score += 10
        
        # Determine risk level
        if risk_score >= 50:
            return "CRITICAL"
        elif risk_score >= 30:
            return "HIGH"
        elif risk_score >= 15:
            return "MEDIUM"
        elif risk_score >= 5:
            return "LOW"
        else:
            return "MINIMAL"

def main():
    print("Advanced Network Security Scanner")
    
    scanner = AdvancedNetworkScanner()
    
    while True:
        print("\nSCANNING OPTIONS:")
        print("1. Select Network Interface")
        print("2. Basic Network Scan")
        print("3. Advanced Network Scan")
        print("4. Display Devices")
        print("5. Basic Security Assessment")
        print("6. Advanced Security Assessment")
        print("7. Generate Security Report")
        print("8. Install Additional Security Tools")
        print("9. Exit")
        
        choice = input("\nEnter your choice: ")
        
        if choice == '1':
            scanner.select_interface()
        elif choice == '2':
            if not scanner.network_interface:
                print("Please select a network interface first.")
                continue
            scanner.scan_network()
        elif choice == '3':
            if not scanner.network_interface:
                print("Please select a network interface first.")
                continue
            scanner.advanced_scan_network()
        elif choice == '4':
            print("Choose display format:")
            print("1. Basic format")
            print("2. Advanced format")
            display_choice = input("Enter choice (1 or 2): ")
            if display_choice == '1':
                scanner.display_devices()
            elif display_choice == '2':
                scanner.display_advanced_devices()
        elif choice == '5':
            target = scanner.select_target()
            if target:
                scanner.run_security_assessment(target)
        elif choice == '6':
            target = scanner.select_target_advanced()
            if target:
                scanner.run_advanced_assessment(target)
        elif choice == '7':
            target = scanner.select_target_advanced()
            if target:
                scanner.generate_security_report(target)
        elif choice == '8':
            print("To install additional security tools, run:")
            print("python3 src/install_security_tools.py")
        elif choice == '9':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interrupted by user. Exiting...") 
#!/usr/bin/env python3

import subprocess
import sys
import platform

def install_security_tools():
    """Install additional security tools for enhanced penetration testing"""
    
    print("Security Tools Installer")
    print("-" * 40)
    print("Only use these tools on systems you own or have explicit permission to test.")
    print()
    
    os_type = platform.system().lower()
    
    if os_type == 'darwin':  # macOS
        install_macos_tools()
    elif os_type == 'linux':
        install_linux_tools()
    else:
        print(f"X Unsupported OS: {os_type}")
        sys.exit(1)

def install_macos_tools():
    """Install security tools on macOS"""
    
    # Check if Homebrew is installed
    try:
        subprocess.run(['brew', '--version'], check=True, stdout=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("X Homebrew not found. Please install Homebrew first:")
        print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        return
    
    tools = [
        ('nmap', 'Network discovery and security auditing'),
        ('netcat', 'Networking utility for reading/writing network connections'),
        ('masscan', 'Fast port scanner'),
        ('nikto', 'Web server scanner'),
        ('sqlmap', 'SQL injection testing tool'),
        ('john', 'Password cracking tool'),
        ('hydra', 'Login cracker'),
        ('aircrack-ng', 'WiFi security auditing'),
        ('wireshark', 'Network protocol analyzer'),
        ('metasploit', 'Penetration testing framework')
    ]
    
    print("Available security tools:")
    for i, (tool, description) in enumerate(tools, 1):
        print(f"{i:2d}. {tool:<15} - {description}")
    
    print("\nWARNING: These are powerful security tools!")
    
    choice = input("\nInstall all tools? (y/n): ")
    if choice.lower() not in ['y', 'yes']:
        print("Installation cancelled.")
        return
    
    for tool, description in tools:
        try:
            subprocess.run(['brew', 'install', tool], check=True)
            print(f"✓ {tool} installed successfully")
        except subprocess.CalledProcessError:
            print(f"X Failed to install {tool}")

def install_linux_tools():
    """Install security tools on Linux"""
    
    # Detect package manager
    package_managers = [
        ('apt', ['apt', 'update'], ['apt', 'install', '-y']),
        ('yum', ['yum', 'update'], ['yum', 'install', '-y']),
        ('pacman', ['pacman', '-Sy'], ['pacman', '-S', '--noconfirm'])
    ]
    
    pm_cmd = None
    for pm, update_cmd, install_cmd in package_managers:
        try:
            subprocess.run([pm, '--version'], check=True, stdout=subprocess.DEVNULL)
            pm_cmd = (pm, update_cmd, install_cmd)
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    if not pm_cmd:
        print("X No supported package manager found")
        return
    
    pm_name, update_cmd, install_cmd = pm_cmd
    
    # Update package list
    try:
        subprocess.run(update_cmd, check=True)
    except subprocess.CalledProcessError:
        print("X Failed to update package list")
        return
    
    tools = [
        'nmap',
        'netcat',
        'masscan',
        'nikto',
        'sqlmap',
        'john',
        'hydra',
        'aircrack-ng',
        'wireshark',
        'metasploit-framework'
    ]
    
    for tool in tools:
        try:
            subprocess.run(install_cmd + [tool], check=True)
            print(f"✓ {tool} installed successfully")
        except subprocess.CalledProcessError:
            print(f"X Failed to install {tool}")

def install_python_packages():
    """Install Python packages for security testing"""
    
    packages = [
        'paramiko',      # SSH client
        'requests',      # HTTP library
        'beautifulsoup4', # Web scraping
        'scapy',         # Packet manipulation
        'python-nmap',   # Nmap Python wrapper
        'impacket',      # Network protocols
        'pycryptodome',  # Cryptography
        'netaddr',       # Network address manipulation
    ]
    
    for package in packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"X Failed to install {package}")

def main():
    print("Security Tools Installation Script")
    print("ETHICAL USE ONLY - Use only on systems you own or have permission to test.")
    print()
    
    if input("Continue? (y/n): ").lower() not in ['y', 'yes']:
        print("Installation cancelled.")
        return
    
    install_security_tools()
    install_python_packages()
    
    print("\nInstallation complete!")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Script to find an available port for the MigrateIQ application.
"""
import socket
import os
import sys
import argparse

def is_port_available(port):
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except socket.error:
            return False

def find_available_port(start_port=8000, end_port=9000):
    """Find an available port in the given range."""
    for port in range(start_port, end_port + 1):
        if is_port_available(port):
            return port
    return None

def write_port_to_env(port, env_file='.env'):
    """Write the port to the .env file."""
    # Check if .env file exists
    if not os.path.exists(env_file):
        # Create .env file
        with open(env_file, 'w') as f:
            f.write(f'PORT={port}\n')
        return
    
    # Read existing .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Check if PORT is already defined
    port_defined = False
    for i, line in enumerate(lines):
        if line.startswith('PORT='):
            lines[i] = f'PORT={port}\n'
            port_defined = True
            break
    
    # If PORT is not defined, add it
    if not port_defined:
        lines.append(f'PORT={port}\n')
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.writelines(lines)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Find an available port for MigrateIQ.')
    parser.add_argument('--start', type=int, default=8000, help='Start of port range')
    parser.add_argument('--end', type=int, default=9000, help='End of port range')
    parser.add_argument('--env-file', default='.env', help='Path to .env file')
    parser.add_argument('--backend-env-file', default='backend/.env', help='Path to backend .env file')
    args = parser.parse_args()
    
    # Find an available port
    port = find_available_port(args.start, args.end)
    if port is None:
        print(f"No available ports found in range {args.start}-{args.end}")
        sys.exit(1)
    
    # Write port to .env files
    write_port_to_env(port, args.env_file)
    write_port_to_env(port, args.backend_env_file)
    
    print(f"Found available port: {port}")
    return port

if __name__ == '__main__':
    main()

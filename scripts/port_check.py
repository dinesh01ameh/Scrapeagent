#!/usr/bin/env python3
"""
Port Management Utility Script
Standalone script to check and manage port 8601
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.port_manager import PortManager, get_port_info
from config.settings import get_settings


def main():
    """Main function for port management"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/port_check.py <command>")
        print("\nAvailable commands:")
        print("  status    - Check port status")
        print("  kill      - Kill processes on port 8601")
        print("  cleanup   - Clean up old SwissKnife processes")
        print("  prepare   - Prepare port for use (kill + cleanup)")
        print("  info      - Detailed port information")
        return
    
    command = sys.argv[1].lower()
    settings = get_settings()
    port = settings.PORT
    
    port_manager = PortManager(port)
    
    if command == "status":
        print(f"🔍 Checking port {port} status...")
        if port_manager.is_port_available(port):
            print(f"✅ Port {port} is available")
        else:
            print(f"❌ Port {port} is busy")
            process = port_manager.find_process_using_port(port)
            if process:
                print(f"   Process: {process.name} (PID: {process.pid})")
                print(f"   Command: {' '.join(process.cmdline)}")
    
    elif command == "kill":
        print(f"🔪 Killing processes on port {port}...")
        success = port_manager.kill_process_on_port(port, force=True)
        if success:
            print(f"✅ Port {port} is now available")
        else:
            print(f"❌ Failed to free port {port}")
    
    elif command == "cleanup":
        print("🧹 Cleaning up old SwissKnife processes...")
        cleaned = port_manager.cleanup_old_processes()
        print(f"✅ Cleaned up {cleaned} processes")
    
    elif command == "prepare":
        print(f"🔧 Preparing port {port} for use...")
        success = port_manager.setup_port_rule()
        if success:
            print(f"✅ Port {port} is ready for use")
        else:
            print(f"❌ Failed to prepare port {port}")
    
    elif command == "info":
        print(f"📊 Detailed information for port {port}:")
        info = get_port_info(port)
        print(json.dumps(info, indent=2, default=str))
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python scripts/port_check.py' without arguments to see available commands")


if __name__ == "__main__":
    main()

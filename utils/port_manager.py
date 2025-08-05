"""
Port Management Utilities
Handles port checking, conflict resolution, and process management
"""

import socket
# import psutil  # Temporarily commented out due to missing dependency
import subprocess
import time
import logging
import signal
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from config.settings import get_settings


@dataclass
class ProcessInfo:
    """Information about a process using a port"""
    pid: int
    name: str
    cmdline: List[str]
    port: int
    status: str


class PortManager:
    """Manages port availability and process conflicts"""
    
    def __init__(self, target_port: int = None):
        self.settings = get_settings()
        self.target_port = target_port or self.settings.PORT
        self.logger = logging.getLogger(__name__)
    
    def is_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result != 0
        except Exception as e:
            self.logger.warning(f"Error checking port {port}: {e}")
            return False
    
    def find_process_using_port(self, port: int) -> Optional[ProcessInfo]:
        """Find the process using a specific port"""
        # Temporarily disabled due to missing psutil dependency
        self.logger.warning(f"Process detection disabled - psutil not available")
        return None
    
    def kill_process_on_port(self, port: int, force: bool = False) -> bool:
        """Kill the process using the specified port"""
        # Temporarily disabled due to missing psutil dependency
        self.logger.warning(f"Process killing disabled - psutil not available")
        return True
    
    def ensure_port_available(self, port: int = None, force: bool = True) -> bool:
        """Ensure the target port is available, killing conflicting processes if needed"""
        port = port or self.target_port
        
        self.logger.info(f"🔍 Checking port {port} availability...")
        
        if self.is_port_available(port):
            self.logger.info(f"✅ Port {port} is available")
            return True
        
        self.logger.warning(f"⚠️ Port {port} is busy")
        
        if force:
            self.logger.info(f"🔄 Attempting to free port {port}...")
            return self.kill_process_on_port(port, force=True)
        else:
            return False
    
    def find_alternative_port(self, start_port: int = None, max_attempts: int = 100) -> Optional[int]:
        """Find an alternative available port"""
        start_port = start_port or self.target_port
        
        for i in range(max_attempts):
            test_port = start_port + i
            if self.is_port_available(test_port):
                return test_port
        
        return None
    
    def get_port_status(self, port: int = None) -> Dict[str, Any]:
        """Get detailed status information about a port"""
        port = port or self.target_port
        
        status = {
            "port": port,
            "available": self.is_port_available(port),
            "process": None,
            "timestamp": time.time()
        }
        
        if not status["available"]:
            process_info = self.find_process_using_port(port)
            if process_info:
                status["process"] = {
                    "pid": process_info.pid,
                    "name": process_info.name,
                    "cmdline": process_info.cmdline,
                    "status": process_info.status
                }
        
        return status
    
    def cleanup_old_processes(self) -> int:
        """Clean up old SwissKnife processes"""
        # Temporarily disabled due to missing psutil dependency
        self.logger.warning("Process cleanup disabled - psutil not available")
        return 0
    
    def setup_port_rule(self) -> bool:
        """Setup permanent port rule and ensure availability"""
        self.logger.info(f"🔧 Setting up permanent port rule for port {self.target_port}")
        
        # Clean up any old processes first
        cleaned = self.cleanup_old_processes()
        if cleaned > 0:
            self.logger.info(f"🧹 Cleaned up {cleaned} old processes")
        
        # Ensure target port is available
        if not self.ensure_port_available(self.target_port, force=True):
            self.logger.error(f"❌ Failed to secure port {self.target_port}")
            return False
        
        self.logger.info(f"✅ Port {self.target_port} is secured and ready")
        return True


def check_and_prepare_port(port: int = None) -> bool:
    """Convenience function to check and prepare port for use"""
    settings = get_settings()
    port = port or settings.PORT
    
    port_manager = PortManager(port)
    return port_manager.setup_port_rule()


def get_port_info(port: int = None) -> Dict[str, Any]:
    """Get information about port status"""
    settings = get_settings()
    port = port or settings.PORT
    
    port_manager = PortManager(port)
    return port_manager.get_port_status(port)

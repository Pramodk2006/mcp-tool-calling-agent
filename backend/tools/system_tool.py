"""
System/File Info Tool for MCP Agent
Provides system information and file operations with safety restrictions
"""
import json
import logging
import os
import platform
import psutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import stat
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    name: str
    path: str
    size: int
    is_directory: bool
    permissions: str
    modified_time: str
    created_time: str

class SystemTool:
    """System and file information tool with safety restrictions"""
    
    def __init__(self, allowed_paths: Optional[List[str]] = None):
        self.name = "system_tool"
        self.description = "Get system information and file/directory listings with safety restrictions"
        
        # Define allowed base paths for security
        self.allowed_paths = allowed_paths or [
            os.getcwd(),  # Current working directory
            os.path.expanduser("~/Documents"),  # User documents
            os.path.expanduser("~/Desktop"),    # User desktop
            "./",  # Relative paths from current directory
        ]
        
    def get_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for this tool"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["system_info", "list_directory", "file_info", "disk_usage"],
                        "description": "Type of operation to perform"
                    },
                    "path": {
                        "type": "string",
                        "description": "File or directory path (required for file operations)"
                    },
                    "include_hidden": {
                        "type": "boolean",
                        "description": "Include hidden files/directories (default: false)",
                        "default": False
                    },
                    "max_files": {
                        "type": "integer",
                        "description": "Maximum number of files to list (default: 100)",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["operation"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "operation": {"type": "string"},
                    "result": {"type": "object"},
                    "timestamp": {"type": "string"},
                    "error": {"type": "string"}
                }
            }
        }
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the system tool"""
        try:
            operation = arguments.get("operation", "").strip()
            path = arguments.get("path", "").strip()
            include_hidden = arguments.get("include_hidden", False)
            max_files = arguments.get("max_files", 100)
            
            if not operation:
                return {
                    "success": False,
                    "error": "Operation parameter is required",
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.info(f"Executing system operation: {operation}")
            
            # Route to appropriate operation
            if operation == "system_info":
                result = self._get_system_info()
            elif operation == "list_directory":
                if not path:
                    path = os.getcwd()
                result = self._list_directory(path, include_hidden, max_files)
            elif operation == "file_info":
                if not path:
                    return {
                        "success": False,
                        "error": "Path parameter is required for file_info operation",
                        "operation": operation,
                        "timestamp": datetime.now().isoformat()
                    }
                result = self._get_file_info(path)
            elif operation == "disk_usage":
                if not path:
                    path = os.getcwd()
                result = self._get_disk_usage(path)
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}",
                    "operation": operation,
                    "timestamp": datetime.now().isoformat()
                }
            
            return {
                "success": True,
                "operation": operation,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in system operation: {str(e)}")
            return {
                "success": False,
                "error": f"System operation error: {str(e)}",
                "operation": arguments.get("operation", ""),
                "timestamp": datetime.now().isoformat()
            }
    
    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is within allowed directories"""
        try:
            abs_path = os.path.abspath(path)
            
            for allowed in self.allowed_paths:
                allowed_abs = os.path.abspath(allowed)
                if abs_path.startswith(allowed_abs):
                    return True
            
            return False
        except:
            return False
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get general system information"""
        try:
            system_info = {
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": platform.python_version()
                },
                "cpu": {
                    "physical_cores": psutil.cpu_count(logical=False),
                    "total_cores": psutil.cpu_count(logical=True),
                    "cpu_usage_percent": psutil.cpu_percent(interval=1)
                },
                "memory": {
                    "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                    "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                    "used_percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                    "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
                    "used_percent": psutil.disk_usage('/').percent
                },
                "current_directory": os.getcwd(),
                "user": os.getenv("USER") or os.getenv("USERNAME") or "unknown"
            }
            
            return system_info
            
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return {"error": str(e)}
    
    def _list_directory(self, path: str, include_hidden: bool, max_files: int) -> Dict[str, Any]:
        """List directory contents with safety checks"""
        try:
            if not self._is_path_allowed(path):
                return {"error": "Access to this path is not allowed for security reasons"}
            
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
            
            if not os.path.isdir(path):
                return {"error": f"Path is not a directory: {path}"}
            
            files = []
            directories = []
            
            try:
                entries = os.listdir(path)
            except PermissionError:
                return {"error": f"Permission denied accessing: {path}"}
            
            count = 0
            for entry in entries:
                if count >= max_files:
                    break
                
                # Skip hidden files if not requested
                if not include_hidden and entry.startswith('.'):
                    continue
                
                entry_path = os.path.join(path, entry)
                
                try:
                    stat_info = os.stat(entry_path)
                    is_dir = os.path.isdir(entry_path)
                    
                    file_info = {
                        "name": entry,
                        "path": entry_path,
                        "size": stat_info.st_size,
                        "is_directory": is_dir,
                        "permissions": stat.filemode(stat_info.st_mode),
                        "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        "created_time": datetime.fromtimestamp(stat_info.st_ctime).isoformat()
                    }
                    
                    if is_dir:
                        directories.append(file_info)
                    else:
                        files.append(file_info)
                    
                    count += 1
                    
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue
            
            return {
                "path": path,
                "total_entries": len(files) + len(directories),
                "directories": directories,
                "files": files,
                "truncated": count >= max_files
            }
            
        except Exception as e:
            logger.error(f"Error listing directory: {str(e)}")
            return {"error": str(e)}
    
    def _get_file_info(self, path: str) -> Dict[str, Any]:
        """Get detailed information about a file or directory"""
        try:
            if not self._is_path_allowed(path):
                return {"error": "Access to this path is not allowed for security reasons"}
            
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
            
            try:
                stat_info = os.stat(path)
            except PermissionError:
                return {"error": f"Permission denied accessing: {path}"}
            
            is_dir = os.path.isdir(path)
            
            file_info = {
                "name": os.path.basename(path),
                "path": os.path.abspath(path),
                "size": stat_info.st_size,
                "size_human": self._human_readable_size(stat_info.st_size),
                "is_directory": is_dir,
                "is_file": os.path.isfile(path),
                "is_symlink": os.path.islink(path),
                "permissions": stat.filemode(stat_info.st_mode),
                "owner_readable": os.access(path, os.R_OK),
                "owner_writable": os.access(path, os.W_OK),
                "owner_executable": os.access(path, os.X_OK),
                "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "created_time": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "accessed_time": datetime.fromtimestamp(stat_info.st_atime).isoformat()
            }
            
            if is_dir:
                try:
                    entries = os.listdir(path)
                    file_info["directory_contents_count"] = len(entries)
                except PermissionError:
                    file_info["directory_contents_count"] = "Permission denied"
            else:
                # Add file extension and MIME type info
                _, ext = os.path.splitext(path)
                file_info["extension"] = ext
                file_info["mime_type"] = self._get_mime_type(ext)
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {"error": str(e)}
    
    def _get_disk_usage(self, path: str) -> Dict[str, Any]:
        """Get disk usage information for a path"""
        try:
            if not self._is_path_allowed(path):
                return {"error": "Access to this path is not allowed for security reasons"}
            
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
            
            usage = psutil.disk_usage(path)
            
            return {
                "path": path,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "used_percent": round((usage.used / usage.total) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting disk usage: {str(e)}")
            return {"error": str(e)}
    
    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type based on file extension"""
        mime_types = {
            ".txt": "text/plain",
            ".py": "text/x-python",
            ".js": "text/javascript", 
            ".html": "text/html",
            ".css": "text/css",
            ".json": "application/json",
            ".xml": "application/xml",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".mp3": "audio/mpeg",
            ".mp4": "video/mp4",
            ".zip": "application/zip"
        }
        
        return mime_types.get(extension.lower(), "application/octet-stream")

# Tool instance for registration
system_tool = SystemTool()
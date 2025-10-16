#!/usr/bin/env python3
"""
Directory Browser API Server
Provides REST API endpoints to browse directory contents on the server
"""

import os
import sys
import json
import stat
import time
import threading
import zipfile
import tempfile
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import logging

# Configuration
directory_toserve = ""  # Set in config.ini

# Set up basic logging first
import os

# Ensure logs directory exists
os.makedirs('./logs', exist_ok=True)

# Set up logging with error handling
handlers = [logging.StreamHandler()]

try:
    # Try to add file handler
    handlers.append(logging.FileHandler('./logs/directory_server.log'))
except (PermissionError, OSError) as e:
    print(f"Warning: Could not create log file: {e}")
    print("Logging to console only.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

# Get configuration from config.ini if available
import configparser
try:
    config = configparser.ConfigParser()
    config.read('config.ini')
except Exception as e:
    logger.warning(f"Could not read config.ini: {e}")

# Configure logging based on config.ini
if 'Logging' in config:
    log_level = config.get('Logging', 'level', fallback='INFO')
    # Update the logging level if specified in config
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(numeric_level)
logger.info(f"Logging set to {log_level} level")

# Get flask debug setting from config.ini
flask_debug_mode = config.get('Logging', 'flaskdebug', fallback='False').lower() in ('True', 'true', '1', 'yes', 'on')
logger.info(f"Flask debug mode: {flask_debug_mode}")

# Set directory to serve from config.ini, if not set, stop the server
if 'Scrape' in config and 'media_dir' in config['Scrape']:
    directory_toserve = config['Scrape']['media_dir']
    logger.info(f"Using media directory from config.ini: {directory_toserve}")
    if not os.path.exists(directory_toserve):
        logger.error(f"Media directory does not exist: {directory_toserve}")
        sys.exit(1)
else:
    logger.error("No media directory set in config.ini")
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Suppress Werkzeug request logs
import logging
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

# Performance monitoring
request_times = {}
active_requests = set()
request_lock = threading.Lock()

@app.before_request
def before_request():
    """Log request start time and track active requests"""
    request.start_time = time.time()
    request_id = f"{request.remote_addr}-{time.time()}"
    request.request_id = request_id
    
    with request_lock:
        active_requests.add(request_id)
        request_times[request_id] = request.start_time
    
    logger.info(f"Request started: {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def after_request(response):
    """Log request completion time and performance metrics"""
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        request_id = getattr(request, 'request_id', 'unknown')
        
        with request_lock:
            if request_id in active_requests:
                active_requests.remove(request_id)
            if request_id in request_times:
                del request_times[request_id]
        
        logger.info(f"Request completed: {request.method} {request.path} - {response.status_code} in {duration:.3f}s")
        
        # Log slow requests
        if duration > 5.0:
            logger.warning(f"Slow request detected: {request.method} {request.path} took {duration:.3f}s")
    
    return response


def get_file_info(file_path):
    """Get detailed information about a file or directory"""
    try:
        stat_info = os.stat(file_path)
        
        # Get file type
        if stat.S_ISDIR(stat_info.st_mode):
            file_type = "directory"
        elif stat.S_ISLNK(stat_info.st_mode):
            file_type = "symlink"
        else:
            file_type = "file"
        
        # Get file size
        if file_type == "directory":
            size = None
        else:
            size = stat_info.st_size
        
        # Get permissions
        permissions = oct(stat_info.st_mode)[-3:]
        
        # Get modification time
        mtime = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
        
        return {
            "name": os.path.basename(file_path),
            "path": file_path,
            "type": file_type,
            "size": size,
            "permissions": permissions,
            "modified": mtime,
            "readable": os.access(file_path, os.R_OK)
        }
    except (OSError, PermissionError) as e:
        logger.warning(f"Error accessing {file_path}: {e}")
        return None

def is_safe_path(base_path, target_path):
    """Check if the target path is within the base path (security check)"""
    try:
        base_path = os.path.abspath(base_path)
        target_path = os.path.abspath(target_path)
        return target_path.startswith(base_path)
    except:
        return False

@app.route('/api/directory', methods=['GET'])
def get_directory_contents():
    """Get contents of a directory"""
    try:
        # Get path parameter (now relative), default to root
        relative_path = request.args.get('path', '')
        
        # Convert relative path back to absolute for server operations
        if relative_path:
            path = os.path.join(directory_toserve, relative_path)
        else:
            path = directory_toserve
        
        # Debug logging
        logger.info(f"Directory request - Requested relative path: {relative_path}, Server root: {directory_toserve}")
        logger.info(f"Path exists: {os.path.exists(path)}, Is directory: {os.path.isdir(path) if os.path.exists(path) else 'N/A'}")
        
        # Security check - ensure path is within allowed directory
        if not is_safe_path(directory_toserve, path):
            logger.warning(f"Security check failed - Requested: {path}, Allowed root: {directory_toserve}")
            return jsonify({"error": "Access denied: Path outside allowed directory"}), 403
        
        # Check if path exists and is a directory
        if not os.path.exists(path):
            return jsonify({"error": "Directory does not exist"}), 404
        
        if not os.path.isdir(path):
            return jsonify({"error": "Path is not a directory"}), 400
        
        # Get directory contents
        try:
            items = os.listdir(path)
        except PermissionError:
            return jsonify({"error": "Permission denied"}), 403
        
        # Get detailed info for each item
        contents = []
        for item in items:
            item_path = os.path.join(path, item)
            file_info = get_file_info(item_path)
            if file_info:
                # Convert absolute path to relative path for client
                if file_info['path'].startswith(directory_toserve):
                    file_info['path'] = os.path.relpath(file_info['path'], directory_toserve)
                    if not file_info['path'] or file_info['path'] == '.':
                        file_info['path'] = ''
                contents.append(file_info)
        
        # Sort contents: directories first, then files, both alphabetically
        contents.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
        
        # Convert paths to relative for client
        relative_path = os.path.relpath(path, directory_toserve) if path != directory_toserve else ""
        if relative_path == '.':
            relative_path = ""
        
        parent_path = None
        if path != directory_toserve:
            parent_abs = os.path.dirname(path)
            if parent_abs != directory_toserve:
                parent_path = os.path.relpath(parent_abs, directory_toserve)
                if parent_path == '.':
                    parent_path = ""
            else:
                parent_path = ""
        
        return jsonify({
            "path": relative_path,
            "parent": parent_path,
            "root_path": "",  # Always empty for client
            "contents": contents,
            "total_items": len(contents)
        })
        
    except Exception as e:
        logger.error(f"Error in get_directory_contents: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/file', methods=['GET'])
def get_file_contents():
    """Get contents of a file (for text files)"""
    try:
        relative_path = request.args.get('path')
        if not relative_path:
            return jsonify({"error": "Path parameter required"}), 400
        
        # Convert relative path back to absolute for server operations
        if relative_path:
            path = os.path.join(directory_toserve, relative_path)
        else:
            path = directory_toserve
        
        # Security check
        if not is_safe_path(directory_toserve, path):
            return jsonify({"error": "Access denied"}), 403
        
        if not os.path.exists(path):
            return jsonify({"error": "File does not exist"}), 404
        
        if os.path.isdir(path):
            return jsonify({"error": "Path is a directory"}), 400
        
        # Check if file is readable
        if not os.access(path, os.R_OK):
            return jsonify({"error": "Permission denied"}), 403
        
        # Get file info
        file_info = get_file_info(path)
        if not file_info:
            return jsonify({"error": "Cannot access file"}), 500
        
        # For small text files, return content
        max_size = 1024 * 1024  # 1MB limit
        if file_info['size'] and file_info['size'] > max_size:
            return jsonify({
                "error": "File too large to display",
                "file_info": file_info
            }), 413
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({
                "file_info": file_info,
                "content": content
            })
        except UnicodeDecodeError:
            return jsonify({
                "error": "File is not a text file",
                "file_info": file_info
            }), 400
        
    except Exception as e:
        logger.error(f"Error in get_file_contents: {e}")
        return jsonify({"error": "Internal server error"}), 500



@app.route('/api/slideshow', methods=['GET'])
def get_slideshow_images():
    """Get all JPG images in a directory for slideshow"""
    try:
        relative_path = request.args.get('path')
        if relative_path is None:
            return jsonify({"error": "Path parameter required"}), 400
        
        # Convert relative path back to absolute for server operations
        if relative_path:
            path = os.path.join(directory_toserve, relative_path)
        else:
            path = directory_toserve
        
        if not is_safe_path(directory_toserve, path):
            return jsonify({"error": "Access denied"}), 403
        
        if not os.path.exists(path) or not os.path.isdir(path):
            return jsonify({"error": "Directory does not exist"}), 404
        
        # Find all image files in the directory
        image_files = []
        allowed_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif')
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    # Check if file is an image (case insensitive)
                    if item.lower().endswith(allowed_extensions):
                        file_info = get_file_info(item_path)
                        if file_info:
                            # Convert absolute path to relative path for client
                            if file_info['path'].startswith(directory_toserve):
                                file_info['path'] = os.path.relpath(file_info['path'], directory_toserve)
                                if not file_info['path'] or file_info['path'] == '.':
                                    file_info['path'] = ''
                            image_files.append(file_info)
        except PermissionError:
            return jsonify({"error": "Permission denied"}), 403
        
        # Sort files by name
        image_files.sort(key=lambda x: x['name'].lower())
        
        # Convert path to relative for client
        relative_path = os.path.relpath(path, directory_toserve) if path != directory_toserve else ""
        if relative_path == '.':
            relative_path = ""
        
        return jsonify({
            "path": relative_path,
            "images": image_files,
            "total_images": len(image_files)
        })
        
    except Exception as e:
        logger.error(f"Error in get_slideshow_images: {e}")
        return jsonify({"error": "Internal server error"}), 500



@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'directory_client.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint with server status"""
    try:
        with request_lock:
            active_count = len(active_requests)
            oldest_request = min(request_times.values()) if request_times else None
            oldest_age = time.time() - oldest_request if oldest_request else 0
        
        return jsonify({
            "status": "healthy",
            "active_requests": active_count,
            "oldest_request_age": f"{oldest_age:.2f}s" if oldest_age else None,
            "server_uptime": f"{time.time() - app.start_time:.2f}s" if hasattr(app, 'start_time') else "unknown"
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/debug/requests')
def debug_requests():
    """Debug endpoint to show active requests"""
    try:
        with request_lock:
            active_requests_list = list(active_requests)
            request_details = []
            for req_id in active_requests_list:
                start_time = request_times.get(req_id, 0)
                age = time.time() - start_time
                request_details.append({
                    "id": req_id,
                    "age": f"{age:.2f}s"
                })
        
        return jsonify({
            "active_requests": request_details,
            "total_active": len(active_requests_list)
        })
    except Exception as e:
        logger.error(f"Debug requests error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/image/<path:filepath>')
def serve_image(filepath):
    """Serve image files for slideshow"""
    try:
        # The filepath is already relative from the server root
        # Convert relative path back to absolute for server operations
        if filepath:
            full_path = os.path.join(directory_toserve, filepath)
        else:
            full_path = directory_toserve
        
        logger.debug(f"Serving image: {filepath} -> {full_path}")
        
        # Security check
        if not is_safe_path(directory_toserve, full_path):
            logger.warning(f"Access denied for image: {full_path}")
            return jsonify({"error": "Access denied"}), 403
        
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            logger.warning(f"Image file not found: {full_path}")
            return jsonify({"error": "File does not exist"}), 404
        
        # Check if file is readable
        if not os.access(full_path, os.R_OK):
            logger.warning(f"Permission denied for image: {full_path}")
            return jsonify({"error": "Permission denied"}), 403
        
        # Check if it's an image file
        allowed_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif')
        if not filepath.lower().endswith(allowed_extensions):
            logger.warning(f"Not an image file: {filepath} (allowed: {allowed_extensions})")
            return jsonify({"error": f"Not an image file. Allowed extensions: {', '.join(allowed_extensions)}"}), 400
        
        # Get file size for logging
        try:
            file_size = os.path.getsize(full_path)
            logger.debug(f"Serving image: {filepath} ({file_size} bytes)")
        except OSError:
            file_size = "unknown"
        
        # Get directory and filename for send_from_directory
        directory_path = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        # Add more detailed logging for debugging
        logger.info(f"Successfully serving image: {filename} from {directory_path}")
        
        return send_from_directory(directory_path, filename)
        
    except Exception as e:
        logger.error(f"Error serving image {filepath}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/video')
def serve_video():
    """Serve video files for playback"""
    try:
        relative_path = request.args.get('path')
        if not relative_path:
            return jsonify({"error": "Path parameter required"}), 400
        
        # Convert relative path back to absolute for server operations
        if relative_path:
            path = os.path.join(directory_toserve, relative_path)
        else:
            path = directory_toserve
        
        # Security check
        if not is_safe_path(directory_toserve, path):
            logger.warning(f"Access denied for video: {path}")
            return jsonify({"error": "Access denied"}), 403
        
        if not os.path.exists(path) or not os.path.isfile(path):
            logger.warning(f"Video file not found: {path}")
            return jsonify({"error": "File does not exist"}), 404
        
        # Check if file is readable
        if not os.access(path, os.R_OK):
            logger.warning(f"Permission denied for video: {path}")
            return jsonify({"error": "Permission denied"}), 403
        
        # Check if it's a video file
        allowed_extensions = ('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.ogv')
        if not path.lower().endswith(allowed_extensions):
            logger.warning(f"Not a video file: {path} (allowed: {allowed_extensions})")
            return jsonify({"error": f"Not a video file. Allowed extensions: {', '.join(allowed_extensions)}"}), 400
        
        # Get directory and filename
        directory_path = os.path.dirname(path)
        filename = os.path.basename(path)
        
        # Get file size for logging
        try:
            file_size = os.path.getsize(path)
            logger.debug(f"Serving video: {filename} ({file_size} bytes)")
        except OSError:
            file_size = "unknown"
        
        logger.info(f"Successfully serving video: {filename} from {directory_path}")
        
        return send_from_directory(directory_path, filename)
        
    except Exception as e:
        logger.error(f"Error serving video: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.route('/api/download-favorites', methods=['POST'])
def download_favorites():
    """Download multiple files as a ZIP archive"""
    try:
        data = request.get_json()
        if not data or 'files' not in data:
            return jsonify({"error": "Files list required"}), 400
        
        files = data['files']
        if not isinstance(files, list) or len(files) == 0:
            return jsonify({"error": "At least one file required"}), 400
        
        # Convert relative paths back to absolute for server operations
        absolute_files = []
        for file_path in files:
            if file_path:
                absolute_path = os.path.join(directory_toserve, file_path)
            else:
                absolute_path = directory_toserve
            
            # Security check - ensure all files are within allowed directory
            if not is_safe_path(directory_toserve, absolute_path):
                logger.warning(f"Access denied for file in favorites download: {absolute_path}")
                return jsonify({"error": "Access denied: File outside allowed directory"}), 403
            
            absolute_files.append(absolute_path)
        
        # Create temporary ZIP file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.zip')
        os.close(temp_fd)
        
        try:
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                file_mapping = {}
                file_counter = 1
                
                for file_path in absolute_files:
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        # Get relative path from server root
                        rel_path = os.path.relpath(file_path, directory_toserve)
                        
                        # Create new filename with 4-digit counter
                        file_extension = os.path.splitext(rel_path)[1]
                        new_filename = f"{file_counter:04d}{file_extension}"
                        
                        # Add file to ZIP with new name
                        zip_file.write(file_path, new_filename)
                        
                        # Store mapping
                        file_mapping[new_filename] = {
                            "original_path": rel_path,
                            "original_name": os.path.basename(rel_path),
                            "file_number": file_counter
                        }
                        
                        logger.info(f"Added to ZIP: {rel_path} -> {new_filename}")
                        file_counter += 1
                    else:
                        logger.warning(f"File not found or not accessible: {file_path}")
                
                # Add JSON mapping file to ZIP
                mapping_json = json.dumps(file_mapping, indent=2)
                zip_file.writestr("file_mapping.json", mapping_json)
                logger.info("Added file_mapping.json to ZIP")
            
            # Send the ZIP file
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=f'favorites-{datetime.now().strftime("%Y%m%d-%H%M%S")}.zip',
                mimetype='application/zip'
            )
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except OSError:
                pass
                
    except Exception as e:
        logger.error(f"Error in download_favorites: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':

    # Set server start time for monitoring
    app.start_time = time.time()
    
    logger.info(f"Starting directory server with root path: {directory_toserve}")
    logger.info("Debug endpoints available:")
    logger.info("  - GET /api/health - Server health check")
    logger.info("  - GET /api/debug/requests - Show active requests")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=flask_debug_mode, threaded=True)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise 
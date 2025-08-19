#!/usr/bin/env python3
"""
Script to check which files in a directory might cause 400 errors
"""

import os
import sys

def check_directory_images(directory_path):
    """Check all files in a directory for potential 400 errors"""
    allowed_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif')
    
    print(f"Checking directory: {directory_path}")
    print(f"Allowed extensions: {', '.join(allowed_extensions)}")
    print("-" * 60)
    
    if not os.path.exists(directory_path):
        print(f"❌ Directory does not exist: {directory_path}")
        return
    
    if not os.path.isdir(directory_path):
        print(f"❌ Path is not a directory: {directory_path}")
        return
    
    try:
        files = os.listdir(directory_path)
    except PermissionError:
        print(f"❌ Permission denied accessing: {directory_path}")
        return
    
    image_files = []
    non_image_files = []
    error_files = []
    
    for item in files:
        item_path = os.path.join(directory_path, item)
        
        if os.path.isfile(item_path):
            # Check if it's an image file
            if item.lower().endswith(allowed_extensions):
                # Check if file is readable
                if os.access(item_path, os.R_OK):
                    try:
                        file_size = os.path.getsize(item_path)
                        image_files.append((item, file_size))
                    except OSError:
                        error_files.append((item, "Cannot get file size"))
                else:
                    error_files.append((item, "Permission denied"))
            else:
                non_image_files.append(item)
    
    print(f"✅ Valid image files ({len(image_files)}):")
    for filename, size in image_files:
        print(f"  📸 {filename} ({size:,} bytes)")
    
    if non_image_files:
        print(f"\n⚠️  Non-image files ({len(non_image_files)}):")
        for filename in non_image_files:
            print(f"  📄 {filename}")
    
    if error_files:
        print(f"\n❌ Files with errors ({len(error_files)}):")
        for filename, error in error_files:
            print(f"  🚫 {filename} - {error}")
    
    print(f"\n📊 Summary:")
    print(f"  Total files: {len(files)}")
    print(f"  Valid images: {len(image_files)}")
    print(f"  Non-images: {len(non_image_files)}")
    print(f"  Errors: {len(error_files)}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 check_images.py <directory_path>")
        print("Example: python3 check_images.py '/mnt/nassys/\$SystemRestore/\$bin/temp/SystemCache/GLAM/Betty T - Gypsy Want 2'")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    check_directory_images(directory_path)

if __name__ == '__main__':
    main() 
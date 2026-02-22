#!/usr/bin/env python3
"""
install_osquery - openclaw-os-activity
Install osquery for OpenClaw
"""
import requests
import sys
import os
import shutil
import tarfile
import zipfile
import subprocess
from pathlib import Path

# Find the user's os
OS = sys.platform
if OS.startswith("win"):
    OS = "windows"
elif OS.startswith("linux"):
    OS = "linux"
elif OS.startswith("darwin"):
    OS = "darwin"
else:
    print(f"Unsupported OS: {OS}")
    sys.exit(1)

# Version
VERSION = "5.21.0"

# Base URL for osquery releases
BASE_URL = f"https://github.com/osquery/osquery/releases/download/{VERSION}"

def get_download_url():
    """Get the download URL based on the OS"""
    if OS == "windows":
        return [
            (f"{BASE_URL}/osquery-{VERSION}.windows_x86_64.zip", "osquery.zip"),
        ]
    elif OS == "linux":
        return [
            (f"{BASE_URL}/osquery-{VERSION}_1.linux_x86_64.tar.gz", "osquery.tar.gz"),
        ]
    elif OS == "darwin":
        # Try ARM64 first, then x86_64
        return [
            (f"{BASE_URL}/osquery-{VERSION}_1.macos_arm64.tar.gz", "osquery.tar.gz"),
            (f"{BASE_URL}/osquery-{VERSION}_1.macos_x86_64.tar.gz", "osquery.tar.gz"),
        ]
    else:
        raise ValueError(f"Unsupported OS: {OS}")

def download_file(url, filepath, filename):
    """Download a file with progress bar"""
    print(f"Downloading from {url}...")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to download from {url}: {e}")
        return False
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filepath, 'wb') as f:
        if total_size > 0:
            try:
                import tqdm
                with tqdm.tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            except ImportError:
                # tqdm not available, fall back to simple download
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        else:
            f.write(response.content)
    
    print(f"Downloaded to {filepath}")
    return True

def extract_archive(archive_path, target_dir):
    """Extract archive based on file type"""
    if archive_path.endswith('.tar.gz'):
        print(f"Extracting tar.gz to {target_dir}...")
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(target_dir)
            return True
    elif archive_path.endswith('.zip'):
        print(f"Extracting zip to {target_dir}...")
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        return True
    else:
        return False

def find_osqueryi_in_dir(search_dir):
    """Find osqueryi binary in the directory"""
    for root, dirs, files in os.walk(search_dir):
        for file in files:
            if file == "osqueryi" or file == "osqueryi.exe":
                return os.path.join(root, file)
    return None

def create_symlink(link_path, target_path):
    """Create a symlink from link_path to target_path"""
    link_path = Path(link_path)
    target_path = Path(target_path)
    
    # Remove existing symlink or file
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    
    try:
        if OS == "windows":
            # On Windows, create a junction or hard link
            # Try to create a symlink with admin privileges
            try:
                os.symlink(target_path, link_path)
                print(f"✓ Created symlink: {link_path} -> {target_path}")
                return True
            except OSError as e:
                if "privilege" in str(e).lower():
                    print(f"Note: Symlink creation requires admin privileges on Windows")
                    print(f"Trying to copy file instead...")
                    shutil.copy2(target_path, link_path)
                    print(f"✓ Copied file: {link_path}")
                    return True
                raise
        else:
            # On Unix-like systems
            os.symlink(target_path, link_path)
            print(f"✓ Created symlink: {link_path} -> {target_path}")
            return True
    except Exception as e:
        print(f"✗ Failed to create symlink: {e}")
        return False

def install_windows(temp_dir, target_dir):
    """Install osquery for Windows"""
    print("Installing osquery for Windows...")
    
    # Look for the osquery directory structure
    # Expected: osquery-5.21.0.windows_x86_64/Program Files/osquery
    for root, dirs, files in os.walk(temp_dir):
        if "Program Files" in dirs:
            program_files_dir = os.path.join(root, "Program Files")
            if os.path.exists(os.path.join(program_files_dir, "osquery")):
                osquery_src = os.path.join(program_files_dir, "osquery")
                print(f"Found osquery directory at: {osquery_src}")
                
                # Remove existing target directory if it exists
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                
                # Copy the entire osquery directory to target
                try:
                    shutil.copytree(osquery_src, str(target_dir))
                    print(f"✓ Copied osquery directory to {target_dir}")
                    
                    # Verify osqueryi.exe exists
                    osqueryi_path = target_dir / "osqueryi.exe"
                    if osqueryi_path.exists():
                        print(f"✓ osqueryi.exe found at: {osqueryi_path}")
                        return True
                    else:
                        print(f"✗ osqueryi.exe not found in {target_dir}")
                        return False
                except Exception as e:
                    print(f"✗ Failed to copy osquery directory: {e}")
                    return False
    
    print(f"✗ osquery directory not found in {temp_dir}")
    return False

def install_linux_macos(temp_dir, target_dir, archive_path):
    """Install osquery for Linux/macOS"""
    print(f"Installing osquery for {OS.upper()}...")
    
    # Look for osqueryd in the extracted directory
    # Expected path: opt/osquery/bin/osqueryd
    osqueryd_path = None
    for root, dirs, files in os.walk(temp_dir):
        if "osqueryd" in files:
            candidate_path = os.path.join(root, "osqueryd")
            # Prefer the one in opt/osquery/bin
            if "bin" in root and "osquery" in root:
                osqueryd_path = candidate_path
                break
            elif osqueryd_path is None:
                osqueryd_path = candidate_path
    
    if not osqueryd_path:
        print(f"✗ osqueryd binary not found in {temp_dir}")
        return False
    
    print(f"Found osqueryd at: {osqueryd_path}")
    
    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy osqueryd to target as osqueryi
    try:
        target_file = target_dir / "osqueryi"
        shutil.copy2(osqueryd_path, str(target_file))
        # Make it executable
        os.chmod(str(target_file), 0o755)
        print(f"✓ Copied osqueryd to {target_file}")
        print(f"✓ osqueryi has been made executable")
        return True
    except Exception as e:
        print(f"✗ Failed to copy osqueryd: {e}")
        return False

def main():
    # Create target directory
    home_dir = Path.home()
    target_dir = home_dir / ".openclaw" / "tools" / "os-activity" / "osquery"
    
    print(f"Target directory: {target_dir}")
    
    # Create directories if they don't exist
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Get download URLs
    download_urls = get_download_url()
    
    # Download file
    temp_dir = Path.home() / ".openclaw" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    success = False
    for download_url, filename in download_urls:
        archive_path = temp_dir / filename
        extract_dir = temp_dir / "osquery_extract"
        
        try:
            if not download_file(download_url, str(archive_path), filename):
                continue
            
            # Create extract directory
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract the archive
            if not extract_archive(str(archive_path), str(extract_dir)):
                continue
            
            # Install based on OS
            if OS == "windows":
                success = install_windows(extract_dir, target_dir)
            else:
                success = install_linux_macos(extract_dir, target_dir, archive_path)
            
            if success:
                break
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
        finally:
            # Clean up extract directory
            if extract_dir.exists():
                shutil.rmtree(extract_dir, ignore_errors=True)
            # Clean up archive
            if archive_path.exists():
                archive_path.unlink()
    
    if success:
        print(f"✓ Successfully installed osquery")
        return 0
    else:
        print(f"✗ Failed to install osquery")
        return 1


if __name__ == "__main__":
    sys.exit(main())
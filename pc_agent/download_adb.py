"""
Download ADB for Windows and prepare portable build
"""
import os
import urllib.request
import zipfile

def download_adb():
    print("=" * 60)
    print("Downloading ADB Platform Tools...")
    print("=" * 60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Download URL
    url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
    zip_path = os.path.join(script_dir, "platform-tools.zip")
    
    print("\n[1/3] Downloading from Google...")
    try:
        urllib.request.urlretrieve(url, zip_path)
        print("✓ Downloaded!")
    except Exception as e:
        print(f"✗ Download failed: {e}")
        return False
    
    print("\n[2/3] Extracting...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(script_dir)
        print("✓ Extracted!")
    except Exception as e:
        print(f"✗ Extract failed: {e}")
        return False
    
    print("\n[3/3] Copying ADB files...")
    platform_tools = os.path.join(script_dir, "platform-tools")
    
    files_to_copy = ["adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll"]
    for file in files_to_copy:
        src = os.path.join(platform_tools, file)
        dst = os.path.join(script_dir, file)
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, dst)
            print(f"  ✓ {file}")
    
    # Cleanup
    os.remove(zip_path)
    print("\n✓ ADB files ready!")
    print("\nFiles copied:")
    for file in files_to_copy:
        if os.path.exists(os.path.join(script_dir, file)):
            print(f"  • {file}")
    
    print("\n" + "=" * 60)
    print("Now run: build_portable.bat")
    print("=" * 60)
    return True

if __name__ == "__main__":
    download_adb()

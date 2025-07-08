#!/usr/bin/env python3
"""
DuxNet Cross-Platform Launcher
Runs on both Windows and Linux without compilation
"""

import subprocess
import sys
import os
import time
import platform

def print_banner():
    print("=" * 60)
    print("🚀 DuxNet All-in-One Launcher")
    print("=" * 60)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print("=" * 60)

def start_service(module_path, args):
    try:
        cmd = [sys.executable, "-m", module_path] + args
        print(f"Starting: {' '.join(cmd)}")
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"❌ Failed to start {module_path}: {e}")
        return None

def main():
    print_banner()
    
    # Change to the project root directory (parent of scripts/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    print(f"📁 Working directory: {os.getcwd()}")
    
    # List of (module_path, args) for each service - updated for new structure
    SERVICES = [
        ("backend.duxnet_store.main", ["--config", os.path.join("backend", "duxnet_store", "config.yaml")]),
        ("backend.duxos_escrow.escrow_service", []),
    ]

    DESKTOP_GUI = ("frontend.duxnet_desktop.desktop_manager", [])
    
    procs = []
    print("\n🔧 Starting DuxNet core services...")
    
    for module_path, args in SERVICES:
        # Check if the module directory exists (cross-platform)
        module_dir = os.path.join(*module_path.split("."))
        if not os.path.exists(module_dir):
            print(f"⚠️  Warning: {module_dir} not found (checked: {os.path.abspath(module_dir)}), skipping.")
            continue
        
        # Check if the main file exists (cross-platform)
        main_file = os.path.join(module_dir, module_path.split(".")[-1] + ".py")
        if not os.path.exists(main_file):
            print(f"⚠️  Warning: {main_file} not found (checked: {os.path.abspath(main_file)}), skipping.")
            continue
            
        print(f"✅ Found: {main_file}")
        proc = start_service(module_path, args)
        if proc:
            procs.append(proc)
            time.sleep(2)

    # Start the Desktop GUI
    desktop_file = os.path.join("frontend", "duxnet_desktop", "desktop_manager.py")
    if os.path.exists(desktop_file):
        print(f"\n🖥️  Launching Desktop GUI...")
        print(f"✅ Found: {desktop_file}")
        gui_proc = start_service(DESKTOP_GUI[0], DESKTOP_GUI[1])
        if gui_proc:
            procs.append(gui_proc)
    else:
        print(f"⚠️  Desktop GUI not found: {desktop_file} (checked: {os.path.abspath(desktop_file)})")

    print(f"\n✅ All services started! ({len(procs)} processes running)")
    print("📋 Services:")
    for i, proc in enumerate(procs):
        print(f"   {i+1}. Process {proc.pid}")
    
    print("\n🛑 Press Ctrl+C to stop all services")
    print("=" * 60)
    
    try:
        while True:
            time.sleep(1)
            for i, proc in enumerate(procs[:]):
                if proc.poll() is not None:
                    print(f"⚠️  Process {proc.pid} has stopped")
                    stdout, stderr = proc.communicate()
                    if stderr:
                        print(f"   Error: {stderr.decode()[:200]}...")
                    procs.remove(proc)
            
            if not procs:
                print("❌ All processes have stopped")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all DuxNet services...")
        for proc in procs:
            try:
                proc.terminate()
                print(f"   Stopping process {proc.pid}...")
            except:
                pass
        
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   Force killing process {proc.pid}...")
                proc.kill()
        
        print("✅ All services stopped.")
        print("=" * 60)

if __name__ == "__main__":
    main() 
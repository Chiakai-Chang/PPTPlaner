#!/usr/bin/env python
"""Video Pipeline Environment Checker.

Detects GPU, Docker, and required services for Phase 2 video pipeline.
"""

import json
import subprocess
import sys
from pathlib import Path


def check_gpu() -> dict:
    """Check NVIDIA GPU availability and specs."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            return {
                "available": True,
                "name": parts[0].strip(),
                "total_vram_mb": int(parts[1].replace("MiB", "").strip()),
                "used_vram_mb": int(parts[2].replace("MiB", "").strip()),
                "free_vram_mb": int(parts[3].replace("MiB", "").strip()),
                "utilization": int(parts[4].replace("%", "").strip()),
            }
    except FileNotFoundError:
        pass
    return {"available": False, "name": "N/A"}


def check_docker() -> dict:
    """Check Docker availability and status."""
    try:
        version = subprocess.run(
            ["docker", "--version"], capture_output=True, text=True, timeout=5
        )
        if version.returncode == 0:
            # Check if daemon is running
            info = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, timeout=10
            )
            daemon_running = info.returncode == 0
            return {
                "available": True,
                "version": version.stdout.strip().split()[-1] if version.stdout else "unknown",
                "daemon_running": daemon_running,
            }
    except FileNotFoundError:
        pass
    return {"available": False, "version": "N/A", "daemon_running": False}


def check_ffmpeg() -> dict:
    """Check FFmpeg availability."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.splitlines()[0].split()[-1] if result.stdout else "unknown"
            return {"available": True, "version": version}
    except FileNotFoundError:
        pass
    return {"available": False}


def check_python_packages() -> dict:
    """Check required Python packages."""
    required = [
        "edge-tts", "Pillow", "Jinja2", "pytest"
    ]
    phase2 = [
        "httpx", "torch", "transformers"
    ]
    
    installed = {}
    for pkg in required + phase2:
        try:
            import importlib
            importlib.import_module(pkg.replace("-", "_"))
            installed[pkg] = True
        except ImportError:
            installed[pkg] = False
    
    return {
        "phase1": all(installed[p] for p in required),
        "phase2": all(installed[p] for p in phase2),
        "details": installed
    }


def main():
    """Run all environment checks and report."""
    results = {
        "gpu": check_gpu(),
        "docker": check_docker(),
        "ffmpeg": check_ffmpeg(),
        "python": check_python_packages(),
    }
    
    # Print summary
    print("\n" + "=" * 60)
    print("  PPTPlaner Video Pipeline - Environment Check")
    print("=" * 60)
    
    print("\n🖥️  GPU:")
    gpu = results["gpu"]
    if gpu["available"]:
        print(f"  ✓ {gpu['name']}")
        print(f"  VRAM: {gpu['total_vram_mb']} MB total, {gpu['free_vram_mb']} MB free")
        print(f"  使用率: {gpu['utilization']}%")
    else:
        print("  ✗ No NVIDIA GPU detected")
    
    print("\n🐳 Docker:")
    docker = results["docker"]
    if docker["available"]:
        print(f"  ✓ Version: {docker['version']}")
        print(f"  Daemon: {'✓ Running' if docker['daemon_running'] else '✗ Not running'}")
    else:
        print("  ✗ Docker not installed")
    
    print("\n🎬 FFmpeg:")
    ffmpeg = results["ffmpeg"]
    if ffmpeg["available"]:
        print(f"  ✓ Version: {ffmpeg['version']}")
    else:
        print("  ✗ FFmpeg not found in PATH")
    
    print("\n🐍 Python Packages:")
    python = results["python"]
    phase1_ok = "✓" if python["phase1"] else "✗"
    print(f"  Phase 1: {phase1_ok}")
    
    # Recommendations
    print("\n" + "-" * 60)
    print("📋 Recommendations:")
    
    if not gpu["available"]:
        print("  ⚠️  No GPU: AI image generation not available")
        print("  → Use RunningHub API or text overlay only")
    
    if not docker["available"]:
        print("  ⚠️  Docker not installed: Fish Speech requires Docker")
        print("  → Install Docker Desktop or use Edge-TTS only")
    elif not docker["daemon_running"]:
        print("  ⚠️  Docker daemon not running")
        print("  → Start Docker Desktop before running video pipeline")
    
    if not ffmpeg["available"]:
        print("  ⚠️  FFmpeg required for video generation")
        print("  → Install from https://ffmpeg.org/download.html")
    
    # Output JSON for automation
    output_path = Path("video_env_check.json")
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n📄 Full report saved to: {output_path}")
    
    # Exit with appropriate code
    all_ok = gpu["available"] and docker["available"] and docker["daemon_running"] and ffmpeg["available"]
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

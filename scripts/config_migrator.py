#!/usr/bin/env python3
"""Configuration migration tool for PPTPlaner updates.

Checks if config.yaml needs updates and applies migrations automatically.
"""
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.yaml"
EXAMPLE = ROOT / "config.yaml.example"

def load_yaml(path):
    """Load YAML file safely."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load {path}: {e}")
        return {}

def migrate():
    """Run all migrations."""
    if not CONFIG.exists():
        print("No config.yaml found. Please run the launcher first.")
        return 1
    
    current = load_yaml(CONFIG)
    example = load_yaml(EXAMPLE)
    
    migrations = []
    
    # Migration 1: Add video section if missing
    if "video" not in current and "video" in example:
        print("[Migrate] Adding video configuration...")
        current["video"] = example["video"]
        migrations.append("Added video section")
    
    # Migration 2: Update video.subtitles if structure changed
    if "video" in current:
        video = current["video"]
        example_video = example.get("video", {})
        
        # Add missing subtitle options
        if "subtitles" in example_video and "subtitles" not in video:
            print("[Migrate] Adding subtitles configuration...")
            video["subtitles"] = example_video["subtitles"]
            migrations.append("Added subtitles config")
    
    # Migration 3: Add agent defaults if missing
    if "agents" not in current and "agents" in example:
        print("[Migrate] Adding agents configuration...")
        current["agents"] = example["agents"]
        migrations.append("Added agents section")
    
    # Apply changes if any
    if migrations:
        try:
            with open(CONFIG, 'w', encoding='utf-8') as f:
                yaml.dump(current, f, default_flow_style=False, allow_unicode=True)
            
            print(f"[Migrate] Applied {len(migrations)} migration(s):")
            for m in migrations:
                print(f"  - {m}")
            return 0
        except Exception as e:
            print(f"[ERROR] Failed to apply migrations: {e}")
            return 1
    else:
        print("[Migrate] No migrations needed.")
        return 0

if __name__ == "__main__":
    sys.exit(migrate())

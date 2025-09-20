#!/usr/bin/env python3
"""
Setup script for Strava Assistant
Installs dependencies and configures the system.
"""

import os
import subprocess
import sys
from pathlib import Path

def check_command_exists(command):
    """Check if a command exists in PATH."""
    try:
        subprocess.run([command, '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_dependencies():
    """Install Python dependencies using virtual environment."""
    print("📦 Setting up virtual environment and installing dependencies...")
    
    venv_path = Path.cwd() / 'venv'
    
    try:
        # Create virtual environment
        print("🔧 Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)
        
        # Determine pip path
        if sys.platform == 'win32':
            pip_path = venv_path / 'Scripts' / 'pip'
        else:
            pip_path = venv_path / 'bin' / 'pip'
        
        # Install dependencies
        print("📥 Installing dependencies...")
        subprocess.run([str(pip_path), 'install', '-r', 'requirements.txt'], check=True)
        
        print("✅ Virtual environment and dependencies installed successfully")
        print(f"💡 To activate: source {venv_path}/bin/activate")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try manually: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
        return False

def check_exiftool():
    """Check if exiftool is installed."""
    print("🔧 Checking for exiftool...")
    
    if check_command_exists('exiftool'):
        print("✅ exiftool found")
        return True
    else:
        print("❌ exiftool not found")
        print("📥 Installing exiftool via Homebrew...")
        
        try:
            subprocess.run(['brew', 'install', 'exiftool'], check=True)
            print("✅ exiftool installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install exiftool")
            print("💡 Please install manually: brew install exiftool")
            return False

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    dirs = [
        Path.home() / 'strava-assistant',
        Path.home() / 'strava-processed',
        Path.home() / 'strava-assistant' / 'pending',
        Path.home() / 'strava-assistant' / 'processed',
        Path.home() / 'strava-assistant' / 'sessions'
    ]
    
    for directory in dirs:
        directory.mkdir(exist_ok=True)
        print(f"✅ Created: {directory}")

def setup_claude_config():
    """Help user set up Claude configuration for Strava MCP."""
    print("\n🔧 Claude Configuration Setup")
    print("=" * 50)
    
    strava_mcp_path = Path.cwd() / 'strava-mcp' / 'dist' / 'server.js'
    
    config = {
        "mcpServers": {
            "strava-mcp-local": {
                "command": "node",
                "args": [str(strava_mcp_path)]
            }
        }
    }
    
    print("Add this to your Claude Desktop configuration:")
    print(f"Location: ~/.claude/claude_desktop_config.json")
    print()
    print("Configuration to add:")
    print(json.dumps(config, indent=2))
    print()
    print("After adding this configuration:")
    print("1. Complete Strava authentication: cd strava-mcp && npx tsx scripts/setup-auth.ts")
    print("2. Restart Claude Desktop")
    print("3. Verify MCP connection in Claude")

def main():
    """Main setup function."""
    print("🚀 Strava Assistant Setup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path('strava_assistant.py').exists():
        print("❌ Please run this script from the strava-assistant directory")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Check/install exiftool
    if not check_exiftool():
        print("⚠️ exiftool installation failed, some features may not work")
    
    # Create directories
    create_directories()
    
    # Setup information
    setup_claude_config()
    
    print("\n✅ Setup complete!")
    print("\n📖 Next steps:")
    print("1. Set up Strava API credentials (see README)")
    print("2. Configure Claude Desktop MCP (see above)")
    print("3. Test with: python strava_assistant.py --help")
    print("\n🏃‍♂️ Happy running!")

if __name__ == '__main__':
    import json  # Import here to avoid issues if not available initially
    main()
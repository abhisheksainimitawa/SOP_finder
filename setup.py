"""
Setup script for Local SOP Finder
Run this to verify your environment and prepare for first use
"""

import sys
import subprocess
import os


def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. You have {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_dependencies():
    """Install required packages"""
    print("\nInstalling dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def verify_imports():
    """Verify key imports work"""
    print("\nVerifying imports...")
    
    try:
        import numpy
        print("✅ numpy")
        
        import sentence_transformers
        print("✅ sentence-transformers")
        
        import rank_bm25
        print("✅ rank-bm25")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def download_model():
    """Download the sentence transformer model"""
    print("\nDownloading sentence transformer model...")
    print("(This is a one-time download of ~80MB)")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='./models')
        print("✅ Model downloaded and cached")
        return True
    except Exception as e:
        print(f"❌ Model download failed: {e}")
        return False


def check_sop_file():
    """Check if SOP file exists"""
    print("\nChecking for SOP file...")
    
    sop_path = './data/structured_sops.txt'
    
    if os.path.exists(sop_path):
        print(f"✅ SOP file found at {sop_path}")
        return True
    else:
        print(f"⚠️  SOP file not found at {sop_path}")
        print("   You'll need to specify the correct path when building the index")
        return False


def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    print("✅ Directories created")
    return True


def run_tests():
    """Run basic tests"""
    print("\nRunning basic tests...")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pytest', 'tests/test_identifier.py::TestSOPParsing::test_parse_sops', '-v'
        ])
        print("✅ Tests passed")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Some tests failed (this may be okay for initial setup)")
        return True  # Don't fail setup if tests fail
    except Exception as e:
        print(f"⚠️  Could not run tests: {e}")
        return True


def main():
    """Main setup process"""
    print("=" * 60)
    print("Local SOP Finder - Setup")
    print("=" * 60)
    
    steps = [
        ("Python version", check_python_version),
        ("Dependencies", install_dependencies),
        ("Imports", verify_imports),
        ("Directories", create_directories),
        ("Model download", download_model),
        ("SOP file", check_sop_file),
    ]
    
    results = []
    
    for step_name, step_func in steps:
        result = step_func()
        results.append((step_name, result))
        
        if not result and step_name in ["Python version", "Dependencies"]:
            print(f"\n❌ Critical step '{step_name}' failed. Cannot continue.")
            return False
    
    print("\n" + "=" * 60)
    print("Setup Summary")
    print("=" * 60)
    
    for step_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {step_name}")
    
    all_passed = all(r for _, r in results[:5])  # First 5 are critical
    
    if all_passed:
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python main.py")
        print("2. Or import: from src.local_sop_identifier import LocalSOPIdentifier")
        print("\nSee README.md for more information.")
    else:
        print("\n⚠️  Setup completed with warnings.")
        print("Review the errors above and try to fix them.")
    
    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

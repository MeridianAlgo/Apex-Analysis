import sys
import os
from pathlib import Path

def main():
    try:
        project_root = str(Path(__file__).parent.absolute())
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from src.ui import run_cli
        
        print("\n" + "="*50)
        print("Welcome to Apex Analysis (Educational Use Only)".center(50))
        print("="*50 + "\n")
        
        run_cli()
        
    except ImportError as e:
        print(f"\nError: Failed to import required module - {str(e)}")
        print("Please ensure all dependencies are installed by running:")
        print("pip install -r requirements.txt\n")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

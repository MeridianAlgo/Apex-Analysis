"""
Main entry point for the Apex Analysis package.
Run with: python -m src
"""

def main():
    """Run the Apex Analysis CLI."""
    from src.ui import run_cli
    print("Welcome to Apex Analysis (Educational Use Only)")
    run_cli()

if __name__ == "__main__":
    main()

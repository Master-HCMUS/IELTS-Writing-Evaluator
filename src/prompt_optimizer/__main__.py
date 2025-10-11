"""
Make prompt_optimizer runnable as a module.

Usage:
    python -m prompt_optimizer optimize --samples 50
    python -m prompt_optimizer evaluate my_prompt.txt
    python -m prompt_optimizer compare prompt1.txt prompt2.txt
"""

from .cli import main

if __name__ == "__main__":
    main()

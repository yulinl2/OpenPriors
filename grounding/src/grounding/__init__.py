"""OpenPriors grounding (Iteration 5): the prose->dgroup front end.

A sub-agent lifts prose into predicate-calculus description groups; a deterministic
grounding check gates the extraction; the analogy engine then solves by structure mapping.
Makes the whole OpenPriors loop run end-to-end on raw text.
"""

from .load import load_riddles
from .solve import solve
from .verify import check_riddles, check_section

__version__ = "0.1.0"
__all__ = ["load_riddles", "solve", "check_riddles", "check_section"]

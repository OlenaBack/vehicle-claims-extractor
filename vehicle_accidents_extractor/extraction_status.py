"""Status values shared by extraction outcomes and persisted run records."""

from typing import Literal


ExtractionStatus = Literal["valid", "repaired", "failed"]

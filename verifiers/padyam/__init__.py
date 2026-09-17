"""Telugu padyam verifier."""
from .verifier import (
    METERS, CONSTRAINT_CLASS, load_profiles, normalize, scan, verify,
    locate_first_violation, paada_sizes, segment_paadas,
)

# models/chord.py
from __future__ import annotations
from typing import Any

class Chord:
    """
    Represents a guitar chord structure, containing fretting positions, 
    barre definitions, visual constraints, and metadata categories.
    """
    def __init__(
        self, 
        name: str, 
        frets: list[int] | None = None, 
        barres: list[tuple[int, int, int]] | None = None, 
        base_fret: int = 1, 
        category: str = 'Other'
    ):
        """
        Initializes a Chord instance with explicit structural layout maps.

        :param name: The display name of the chord (e.g., "Cmaj7", "Am").
        :param frets: An array of 6 integers representing strings from low E to high e:
                      [E, A, D, G, B, e]
                      -1 = Muted/unplayed string (X)
                       0 = Open string (O)
                       n = Absolute fret position number
        :param barres: A list of tuples describing barre chord points:
                       (fret_number, start_string_index, end_string_index)
                       e.g., (1, 1, 6) means a barre on the 1st fret spanning from low E to high e.
        :param base_fret: The first visible vertical fret row displayed on the diagram canvas.
        :param category: The group classification name for organizational layout binding.
        """
        self.name = name
        self.frets = frets or [0, 0, 0, 0, 0, 0]
        self.barres = barres or []
        self.base_fret = max(1, base_fret)
        self.category = category
    
    def to_dict(self) -> dict[str, Any]:
        """
        Serializes the Chord instance configuration into a standard data dictionary 
        compatible with JSON storage structures.
        
        :return: A dictionary mapping property strings to raw attribute configurations.
        """
        return {
            "name": self.name,
            "frets": self.frets,
            "barres": self.barres,
            "base_fret": self.base_fret,
            "category": self.category
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Chord:
        """
        Factory method that instantiates a valid Chord object from structured dictionary inputs.

        :param data: A source data dictionary containing raw chord attributes.
        :return: A fully configured Chord model instance.
        """
        raw_barres = data.get('barres', [])
        
        # Ensure array values extracted from JSON streams are explicitly handled as immutable tuples
        converted_barres = [tuple(b) for b in raw_barres]

        return cls(
            name=data.get('name', ''),
            frets=data.get('frets', [0, 0, 0, 0, 0, 0]),
            barres=converted_barres,
            base_fret=data.get('base_fret', 1),
            category=data.get('category', 'Other')
        )
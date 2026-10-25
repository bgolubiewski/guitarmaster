# services/chord_service.py
import json
from pathlib import Path
from typing import Any
from models.chord import Chord

class ChordService:
    """
    Data service responsible for managing chords and categories in memory,
    handling persistent JSON database operations, and maintaining drag-and-drop hierarchy.
    """
    def __init__(self) -> None:
        self.chords: list[Chord] = []
        self.categories: list[str] = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'Other']

        # Determine database paths relative to this service file location
        services_dir = Path(__file__).resolve().parent
        database_dir = services_dir / "database"
        
        database_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = database_dir / "chords.json"

        self.load_data_from_database()

    def add_category(self, category_name: str) -> None:
        """
        Appends a unique new category name into the tracked collection and commits to disk.
        """
        category_name = category_name.strip()
        if category_name and category_name not in self.categories:
            self.categories.append(category_name)
            self.save_data_to_database()

    def rename_category(self, old_name: str, new_name: str) -> None:
        """
        Renames an existing category tracking slot while maintaining its absolute order index,
        then updates all associated child chords to reflect the change.
        """
        old_name = old_name.strip()
        new_name = new_name.strip()

        if not new_name or old_name == new_name:
            return
        
        if old_name not in self.categories:
            self.add_category(new_name)
            return
        
        idx = self.categories.index(old_name)
        self.categories[idx] = new_name

        for chord in self.chords:
            if chord.category == old_name:
                chord.category = new_name
                
        self.save_data_to_database()

    def delete_category(self, category_name: str) -> None:
        """
        Removes a category segment from the collection and cascades deletion to all assigned chords.
        """
        category_name = category_name.strip()
        if category_name in self.categories:
            self.categories.remove(category_name)
        
        self.chords = [c for c in self.chords if c.category != category_name]
        self.save_data_to_database()

    def reorder_categories(self, new_order: list[str]) -> None:
        """
        Updates the sorting order configuration for categories and shifts the underlying memory arrays
        to match the layout requested via drag-and-drop interface triggers.
        """
        self.categories = [c for c in new_order if c in self.categories or c]
        self.save_data_to_database()

    def add_chord(self, chord: Chord) -> None:
        """
        Appends a configured Chord model instance into database records.
        """
        self.chords.append(chord)
        if chord.category not in self.categories:
            self.categories.append(chord.category)
        self.save_data_to_database()

    def delete_chord(self, chord_name: str) -> None:
        """
        Removes a specific chord entry from records matching by its exact name identifier string.
        """
        self.chords = [c for c in self.chords if c.name != chord_name]
        self.save_data_to_database()

    def get_all_chords(self) -> list[Chord]:
        """
        Retrieves the flat collection of all loaded Chord data models.
        """
        return self.chords
    
    def get_chord_by_name(self, name: str) -> Chord | None:
        """
        Queries the current memory records to find a Chord matching the target identifier name.

        :param name: Unique lookup name string.
        :return: Matching Chord instance, or None if no result can be found.
        """
        return next((c for c in self.chords if c.name == name), None)
    
    def update_chord(self, old_name: str, updated_chord: Chord) -> bool:
        """
        Replaces properties of an existing chord target matching a key name with a new payload model.

        :param old_name: The previous identifier name of the targeted chord object.
        :param updated_chord: Modified Chord instance containing new payload fields.
        :return: True if substitution was completed successfully, False otherwise.
        """
        for i, chord in enumerate(self.chords):
            if chord.name == old_name:
                self.chords[i] = updated_chord
                if updated_chord.category not in self.categories:
                    self.categories.append(updated_chord.category)
                self.save_data_to_database()
                return True
        return False
    
    def get_chords_grouped_by_category(self) -> dict[str, list[Chord]]:
        """
        Groups current chord collections into an associative dictionary mapped by category strings.
        Ensures that even empty categories are returned with an empty initialized list.
        """
        for chord in self.chords:
            if chord.category not in self.categories:
                self.categories.append(chord.category)

        grouped = {cat: [] for cat in self.categories}
        for chord in self.chords:
            grouped[chord.category].append(chord)

        return grouped
    
    def move_chord_position(self, chord: Chord, target_category: str, target_index: int) -> None:
        """
        Updates a chord's category alignment and repositions its sequence index 
        to ensure drag-and-drop structural shifts remain persistent between user sessions.
        """
        self.chords = [c for c in self.chords if c.name != chord.name]
        chord.category = target_category

        grouped = self.get_chords_grouped_by_category()
        if target_category in grouped:
            grouped[target_category] = [c for c in grouped[target_category] if c.name != chord.name]
            grouped[target_category].insert(target_index, chord)
        else:
            grouped[target_category] = [chord]

        new_flat_chords = []
        for cat in self.categories:
            if cat in grouped:
                new_flat_chords.extend(grouped[cat])

        for cat, chords_in_cat in grouped.items():
            if cat not in self.categories:
                new_flat_chords.extend(chords_in_cat)

        self.chords = new_flat_chords
        self.save_data_to_database()

    # ------------------------------------------------------------------------
    # Database handling
    # ------------------------------------------------------------------------

    def save_data_to_database(self) -> None:
        """
        Serializes current structured states and commits the payload configuration to a JSON file.
        """
        data = {
            "categories": self.categories,
            "chords": [chord.to_dict() for chord in self.chords]
        }
        
        with open(self.file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)

    def load_data_from_database(self) -> None:
        """
        Parses saved JSON assets into runtime properties. Includes backward 
        compatibility mapping for old flat array configurations.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

                if isinstance(data, dict):
                    self.categories = data.get("categories", ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'Other'])
                    chords_data = data.get("chords", [])
                    self.chords = [Chord.from_dict(chord_data) for chord_data in chords_data]
                elif isinstance(data, list):
                    self.chords = [Chord.from_dict(chord_data) for chord_data in data]
                    self.categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'Other']
                    
                    for chord in self.chords:
                        if chord.category not in self.categories:
                            self.categories.append(chord.category)
        except FileNotFoundError:
            self.chords = []
            self.categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'Other']
            self.save_data_to_database()
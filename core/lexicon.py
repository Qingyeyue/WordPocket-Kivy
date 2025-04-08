# core/lexicon.py
import json
import os
from typing import List, Dict, Optional, Any, Tuple # Added typing for clarity

class Lexicon:
    """
    Manages lexicon files, including a main 'defaults.json' list
    and other lexicon files containing indices into 'defaults.json'.
    """
    def __init__(self, lexicon_dir: str = 'lexicons'):
        """
        Initializes the Lexicon manager.

        Args:
            lexicon_dir: The directory where lexicon JSON files are stored.
                         Defaults to 'lexicons'.
        """
        # Ensure the base directory for lexicons exists
        # Get the directory containing this lexicon.py file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the lexicon directory relative to this file's parent
        self.lexicon_dir = os.path.abspath(os.path.join(base_dir, '..', lexicon_dir))

        if not os.path.exists(self.lexicon_dir):
            try:
                os.makedirs(self.lexicon_dir)
                print(f"Created lexicon directory: {self.lexicon_dir}")
            except OSError as e:
                print(f"Error creating lexicon directory {self.lexicon_dir}: {e}")
                # Handle error appropriately, maybe raise exception or exit
                self.lexicon_dir = None # Indicate failure

        # Load the main defaults list, handling potential errors
        self.defaults: List[Dict[str, Any]] = self._load_lexicon_internal('defaults')
        if not self.defaults:
             print("Warning: 'defaults.json' could not be loaded or is empty.")
             # Consider loading a backup or handling this state in the app


    def _get_lexicon_path(self, name: str) -> str:
        """Constructs the full path for a given lexicon name."""
        if not self.lexicon_dir:
             # Handle case where directory couldn't be created/found
             raise FileNotFoundError("Lexicon directory path is not set or invalid.")
        return os.path.join(self.lexicon_dir, f'{name}.json')

    def _load_lexicon_internal(self, name: str) -> List[Any]:
        """Internal helper to load any lexicon file (defaults or index list)."""
        path = self._get_lexicon_path(name)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Basic validation: ensure it's a list
                    if isinstance(data, list):
                        return data
                    else:
                        print(f"Warning: Lexicon file '{name}.json' does not contain a JSON list. Returning empty.")
                        return []
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON from {path}. Returning empty.")
                return []
            except IOError as e:
                print(f"Error reading file {path}: {e}. Returning empty.")
                return []
            except Exception as e:
                 print(f"An unexpected error occurred loading '{name}.json': {e}. Returning empty.")
                 return []
        else:
            # If defaults.json is missing on first load, return empty, don't print error yet
            if name != 'defaults':
                 print(f"Info: Lexicon file '{name}.json' not found. Returning empty.")
            return []

    def load_lexicon(self, name: str) -> List[int]:
        """
        Loads a lexicon file containing a list of integer indices.
        Ensures returned values are integers.
        """
        data = self._load_lexicon_internal(name)
        # Ensure all items in the list are valid integers
        indices = []
        for item in data:
            try:
                indices.append(int(item))
            except (ValueError, TypeError):
                print(f"Warning: Non-integer value '{item}' found in '{name}.json'. Skipping.")
        return indices

    def save_lexicon(self, name: str, data: List[Any]) -> bool:
        """
        Saves data (either list of entries or list of indices) to a lexicon file.

        Returns:
            True if successful, False otherwise.
        """
        path = self._get_lexicon_path(name)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                # Use indent for readability, ensure_ascii=False for unicode
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"Error writing to file {path}: {e}")
            return False
        except Exception as e:
             print(f"An unexpected error occurred saving '{name}.json': {e}")
             return False

    def create_lexicon(self, name: str) -> bool:
        """Creates a new, empty lexicon file (list of indices)."""
        path = self._get_lexicon_path(name)
        if not os.path.exists(path):
            # Create with an empty list
            return self.save_lexicon(name, [])
        else:
            print(f"Info: Lexicon '{name}' already exists.")
            return False # Indicate it wasn't newly created because it exists

    def rename_lexicon(self, old_name: str, new_name: str) -> bool:
        """Renames a lexicon file."""
        # Avoid renaming defaults
        if old_name == 'defaults' or new_name == 'defaults':
            print("Error: Cannot rename the 'defaults' lexicon.")
            return False
        old_path = self._get_lexicon_path(old_name)
        new_path = self._get_lexicon_path(new_name)
        if os.path.exists(old_path) and not os.path.exists(new_path):
            try:
                os.rename(old_path, new_path)
                return True
            except OSError as e:
                print(f"Error renaming lexicon {old_name} to {new_name}: {e}")
                return False
        elif not os.path.exists(old_path):
             print(f"Error: Source lexicon '{old_name}' not found.")
             return False
        else: # new_path exists
             print(f"Error: Target lexicon name '{new_name}' already exists.")
             return False

    def delete_lexicon(self, name: str) -> bool:
        """Deletes a lexicon file."""
         # Avoid deleting defaults
        if name == 'defaults':
            print("Error: Cannot delete the 'defaults' lexicon.")
            return False
        path = self._get_lexicon_path(name)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except OSError as e:
                print(f"Error deleting lexicon {name}: {e}")
                return False
        else:
            print(f"Info: Lexicon '{name}' not found, cannot delete.")
            return False # It wasn't there to delete

    def get_lexicon_list(self) -> List[str]:
        """Gets list of lexicon names, excluding 'defaults'."""
        if not self.lexicon_dir or not os.path.isdir(self.lexicon_dir):
            return []
        try:
            files = os.listdir(self.lexicon_dir)
            lexicon_names = [
                os.path.splitext(f)[0]
                for f in files
                if f.endswith('.json') and os.path.splitext(f)[0] != 'defaults'
            ]
            return sorted(lexicon_names)
        except OSError as e:
            print(f"Error reading lexicon directory {self.lexicon_dir}: {e}")
            return []

    def find_entry_index(self, entry_to_find: Dict[str, Any]) -> Optional[int]:
        """
        Finds the index (position) of a given entry dictionary within the
        `self.defaults` list. Matching is based on 'chinese' and 'english' fields.

        Returns:
            The integer index if found, otherwise None.
        """
        if not self.defaults: # Ensure defaults list is loaded and not empty
             # Attempt to reload if empty? Or just return None.
             # print("Warning: Trying to find entry index but defaults list is empty.")
             return None

        # Extract keys for matching to handle potential missing keys in entry_to_find
        target_chinese = entry_to_find.get('chinese')
        target_english = entry_to_find.get('english')

        if target_chinese is None or target_english is None:
            print("Warning: Entry to find is missing 'chinese' or 'english' field.")
            return None

        for i, default_entry in enumerate(self.defaults):
            # Check if the default entry also has the keys before comparing
            if default_entry.get('chinese') == target_chinese and \
               default_entry.get('english') == target_english:
                return i  # Return the index (position in the list)
        return None # Not found

    def add_entry_to_lexicon(self, entry: Dict[str, Any], lexicon_name: str) -> Tuple[bool, str]:
        """
        Adds an entry's index to a specific lexicon's index list.

        Args:
            entry: The dictionary representing the word entry.
            lexicon_name: The name of the target lexicon (without .json).

        Returns:
            A tuple (success_boolean, message_string).
        """
        entry_index = self.find_entry_index(entry)

        if entry_index is None:
            return False, '条目未在主词库(defaults)中找到' # Entry must exist in defaults

        # Load the target lexicon's list of indices
        lexicon_indices = self.load_lexicon(lexicon_name)

        if entry_index in lexicon_indices:
            return False, '该条目已存在于此词库中'
        else:
            lexicon_indices.append(entry_index)
            success = self.save_lexicon(lexicon_name, lexicon_indices)
            if success:
                return True, '添加成功'
            else:
                return False, '添加失败 (无法保存词库文件)'

    def update_entry_in_defaults(self, updated_entry: Dict[str, Any]) -> bool:
        """
        Updates an existing entry within the `self.defaults` list and saves
        the entire list back to `defaults.json`.
        Finds the entry based on 'chinese' and 'english' match.

        Returns:
            True if the entry was found and the save was successful, False otherwise.
        """
        entry_index = self.find_entry_index(updated_entry)

        if entry_index is not None:
            # Make sure the index is valid before updating
            if 0 <= entry_index < len(self.defaults):
                # Update the entry at the found index
                # Important: Ensure all necessary fields are present in updated_entry
                # or merge carefully if only partial updates are intended.
                # This replaces the whole dict at that position:
                self.defaults[entry_index] = updated_entry
                # Save the entire updated list back to defaults.json
                return self.save_lexicon('defaults', self.defaults)
            else:
                 print(f"Error: Found index {entry_index} for update, but it's out of bounds for defaults list (len={len(self.defaults)}).")
                 return False
        else:
            # Original code appended if not found. Decide if this is desired.
            # If you only want to *update*, return False here.
            print(f"Info: Entry not found in defaults for update: {updated_entry.get('english')}")
            # To keep original behavior (append if not found):
            # self.defaults.append(updated_entry)
            # return self.save_lexicon('defaults', self.defaults)
            return False # Indicate update failed because entry wasn't found


    def remove_entry_from_lexicon(self, entry: Dict[str, Any], lexicon_name: str) -> Tuple[bool, str]:
        """
        Removes an entry's index from a specific lexicon's index list.

        Args:
            entry: The dictionary representing the word entry to remove.
            lexicon_name: The name of the lexicon from which to remove the index.

        Returns:
            A tuple (success_boolean, message_string).
        """
        entry_index = self.find_entry_index(entry)

        if entry_index is None:
            # Should not happen if entry came from the lexicon, but safeguard
            return False, '条目未在主词库(defaults)中找到'

        lexicon_indices = self.load_lexicon(lexicon_name)

        if entry_index in lexicon_indices:
            lexicon_indices.remove(entry_index)
            success = self.save_lexicon(lexicon_name, lexicon_indices)
            if success:
                return True, '条目已移出词库'
            else:
                # Should attempt to restore the index list? Maybe not.
                return False, '移除失败 (无法保存词库文件)'
        else:
            return False, '条目不在此词库中'

    def get_lexicon_entries(self, lexicon_name: str) -> List[Dict[str, Any]]:
        """
        Retrieves the full entry dictionaries for a given lexicon name
        by mapping its indices to the `self.defaults` list.
        """
        indices = self.load_lexicon(lexicon_name)
        entries = []
        if not self.defaults:
            print(f"Warning: Cannot get entries for '{lexicon_name}', defaults list is not loaded.")
            return []

        for i in indices:
            # Check if index is valid for the current defaults list
            if isinstance(i, int) and 0 <= i < len(self.defaults):
                # Append a copy to avoid external modification? Optional.
                # entries.append(self.defaults[i].copy())
                entries.append(self.defaults[i])
            else:
                print(f"Warning: Invalid index '{i}' found in '{lexicon_name}.json' ignored (defaults length: {len(self.defaults)}).")
        return entries

    def get_entry_indices(self, entries: List[Dict[str, Any]]) -> List[int]:
        """
        Converts a list of entry dictionaries back into a list of their
        corresponding indices in the `self.defaults` list.
        """
        indices = []
        for entry in entries:
            index = self.find_entry_index(entry)
            if index is not None:
                indices.append(index)
            else:
                # Log if an entry couldn't be mapped back?
                print(f"Warning: Could not find index for entry: {entry.get('english')}")
        return indices
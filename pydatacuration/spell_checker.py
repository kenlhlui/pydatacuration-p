"""Spell checker module for text data curation."""
import re
from pathlib import Path
from typing import Union

from spellchecker import SpellChecker

RES_DIR = Path('res')

class SpellCheckerCustomized:
    """A class for spell checking and cleaning text."""
    def __init__(self) -> None:
        """Initialize the SpellCheckerCustomized class."""
        self.spell = SpellChecker()
        self.spell.word_frequency.load_text_file('./res/spellcheck_exclusions.txt') # Load the list of words to exclude from the spell check.
    # TODO: Add a function/amend clean_text function to remove the html tags, if appeared.
    # TODO: Error handling if the input is not a string/list.

    def _clean_text(self, text: Union[str, list]) -> list:
        """Clean the text by removing special characters, numbers, and stop words.

        Args:
            text (str | list): The text to clean.

        Returns:
            list: The cleaned text, speared word by word.
        """
        # Join the list of words across items if the input is a list.
        if isinstance(text, list):
            text = ' '.join(text)

        # Split the text according to the punctuation [.,!;] and remove the spaces.
        text = re.split(r'(?<=[.!?;])\s+', text)

        cleaned_sentences = []
        for sentence in text:
            # Split each sentence into words
            words = sentence.split()

            # Keep the first word (even if it starts with a capital letter) and filter out other capitalized words, and append them to cleaned_sentences
            cleaned_words = [words[0]] + [word for word in words[1:] if not word[0].isupper()]
            # Extend the cleaned_words to cleaned_sentences
            cleaned_sentences.extend(cleaned_words)

        # Remove words containing special characters and numbers
        pattern = r'^[a-zA-Z]+$'  # Only allow letters from a-z and A-Z
        cleaned_sentences = [word for word in cleaned_sentences if re.match(pattern, word)]

        return cleaned_sentences

    def check_spelling(self, list_of_words: Union[str, list]) -> tuple:
        """Check the spelling of the text.

        Args:
            list_of_words (str | list): The string or list of words to check the spelling.

        Returns:
            tuple: A tuple containing the misspelled words in list and a boolean value indicating if there are misspelled words.
        """
        list_of_words = self._clean_text(list_of_words)
        misspelled_words = self.spell.unknown(list_of_words)  # Returns a set of misspelled words.

        return list(misspelled_words), bool(misspelled_words)

# pylint: disable=C0301
import os
import re
import string
from typing import Union
from spellchecker import SpellChecker

class SpellCheckerCustomized():
    def __init__(self):
        self.spell = SpellChecker()
    #TODO: Add a function/amend clean_text function to remove the html tags, if appeared.
    #TODO: Error handling if the input is not a string/list.

    def _clean_text(self, text: Union[str, list]) -> list:
        """
        Clean the text by removing special characters, numbers, and stop words.

        Args:
            text (text | list): The text to clean.
        
        Returns:
            list: The cleaned text, sperated word by word.
        """
        # Join the list of words acorrss items if the input is a list.
        if isinstance(text, list):
            text = ' '.join(text)


        # Split the text according to the punctuation [.,!;] and remove the spaces.
        text = re.split(r'(?<=[.!?;])\s+', text)

        cleaned_sentences = []
        for sentence in text:
            # Split each sentence into words
            words = sentence.split()

            # Keep the first word (even if it starts with a capital letter) and filter out other capitalized words, and append them to cleaned_sentences
            cleaned_words = [words[0]] + [word for word in words[1:] if not (word[0].isupper())]

            # Extend the cleaned_words to cleaned_sentences
            cleaned_sentences.extend(cleaned_words)

        # Remove punctuation
        cleaned_sentences = [word.translate(str.maketrans('', '', string.punctuation)) for word in cleaned_sentences]

        # Remove words starting with special characters
        cleaned_sentences = [word for word in cleaned_sentences if not word.startswith(('#', '@', '$', '%', '&', '*'))]

        # Remove numbers
        cleaned_sentences = [word for word in cleaned_sentences if not word.isdigit()]

        return cleaned_sentences

    def check_spelling(self, list_of_words: Union[str, list]) -> tuple:
        """
        Check the spelling of the text.
        
        Args:
            list_of_words (str | list): The string or list of words to check the spelling.
        
        Returns:
            tuple: A tuple containing the misspelled words in set and a boolean value indicating if there are misspelled words.
        """
        list_of_words = self._clean_text(list_of_words)
        misspelled_words = self.spell.unknown(list_of_words)

        return misspelled_words, bool(misspelled_words)

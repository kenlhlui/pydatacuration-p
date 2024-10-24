import string
from spellchecker import SpellChecker
import nltk

class SpellCheckerCustomized():
    def __init__(self):
        self.spell = SpellChecker()

    def clean_text(self, text):
        """
        Clean the text by removing special characters, numbers, and stop words.

        Args:
            text (str): The text to clean.
        
        Returns:
            list: The cleaned text.
        """

        # Trun text in to list
        translator = str.maketrans('', '', string.punctuation)
        text = text.translate(translator)
        
        text = text.split()

        # Remove the words in Capital letters
        text = [word for word in text if not word.isupper()]

        # Remove words starting with special characters
        text = [word for word in text if not word.startswith(('#', '@', '$', '%', '&', '*'))]

        # Remove words starts with Capital letter
        text = [word for word in text if not word.istitle()]

        # Remove numbers
        text = [word for word in text if not word.isdigit()]

        # Load stop words
        stop_words = nltk.corpus.stopwords.words('english')

        # Remove stop words
        text_filtered = [word for word in text if word.lower() not in stop_words]

        return text_filtered

    def check_spelling(self, list_of_words):
        """
        Check the spelling of the text.
        
        Args:
            list_of_words (list): The text to check.
        
        Returns:
            bool: True if there are misspelled words, False otherwise.
        """
        misspelled_words = self.spell.unknown(list_of_words)

        print(misspelled_words)
        return misspelled_words, bool(misspelled_words)

    def main(self, list_of_words: list):
        """
        Check the spelling of the text.
        
        Args:
            text (str): The text to check.
        
        Returns:
            bool: True if there are misspelled words, False otherwise.
        """
        list_of_words = self.clean_text(list_of_words)
        return self.check_spelling(list_of_words)


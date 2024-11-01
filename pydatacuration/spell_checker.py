import os
import string
from spellchecker import SpellChecker
import nltk

class SpellCheckerCustomized():
    def __init__(self):
        self.spell = SpellChecker()
    #TODO: Add a function/amend clean_text function to remove the html tags, if appeared.
    #TODO: Error handling if the input is not a string/list.

    def _get_stop_words(self):
        """
        Get the stop words from the nltk library.

        Returns:
            list: The stop words.
        """
        current_path = os.getcwd()
        nltk_stopwords_path = os.path.join(current_path, 'res', 'nltk_data')
        if not os.path.exists(nltk_stopwords_path):
            os.mkdir(nltk_stopwords_path)
            nltk.download('stopwords', download_dir=nltk_stopwords_path, quiet=True)
            nltk.data.path.append(nltk_stopwords_path)

        else:
            nltk.data.path.append(nltk_stopwords_path)

    def _clean_text(self, text):
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

        # Get and load the stop words
        self._get_stop_words()

        # Load stop words
        stop_words = nltk.corpus.stopwords.words('english')

        # Remove stop words
        text_filtered = [word for word in text if word.lower() not in stop_words]

        return text_filtered

    def check_spelling(self, list_of_words: list):
        """
        Check the spelling of the text.
        
        Args:
            list_of_words (list): The text to check.
        
        Returns:
            bool: True if there are misspelled words, False otherwise.
        """
        misspelled_words = self.spell.unknown(list_of_words)

        return misspelled_words, bool(misspelled_words)

    def spell_checker(self, list_of_words: list):
        """
        Check the spelling of the text.
        
        Args:
            text (str): The text to check.
        
        Returns:
            bool: True if there are misspelled words, False otherwise.
        """
        list_of_words = self._clean_text(list_of_words)
        return self.check_spelling(list_of_words)


import utils
import re

def process(text):
    for conditonal_marker in utils.conditional_marks:
        # Replace at start of sentence
        text = re.sub('. ' + conditonal_marker, '. If', text, 100000, flags=re.IGNORECASE)
        # Replace at other occurrences
        text = re.sub(conditonal_marker, 'if', text, 100000)
        pass
    return text.replace(', otherwise', '. Otherwise')

import utils
import re

def process(text):
    for conditonal_marker in utils.conditional_marks:
        # Replace at start of sentence
        text = re.sub('\. ' + conditonal_marker, '. If', text, 100000, flags=re.IGNORECASE)
        # Replace at the begging of line
        text = re.sub('\n' + conditonal_marker, 'If', text, 100000, flags=re.IGNORECASE)
        # Replace 'Sometimes' at the beginning of a sentence with "If"
        text = re.sub('. Sometimes ', '. If ', text)
        # Replace empty new lines
        text = re.sub('\n\n', '\n', text)
        # Replace new lines with space
        text = re.sub('.\n', '. ', text)
        # Replace "re-" verbs: SpaCy seems to create new verbs from it
        text = re.sub('re-', 're', text)
        # Replace "back-" verbs: SpaCy seems to create new verbs from it
        text = re.sub('back-', 'back', text)
        # Replace at other occurrences of conditional markers
        text = re.sub(conditonal_marker, 'if', text, 100000)
    return text.replace(', otherwise', '. Otherwise')

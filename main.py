import spacy
from spacy import displacy

nlp = spacy.load('en_core_web_sm')
doc = nlp('Sometimes there is still confusion in the message, then I must ask the Department again')

for token in doc:
    print(token.text, token.pos_)

# displacy.serve(doc, style="dep")

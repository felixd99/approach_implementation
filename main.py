import spacy, coreferee
from spacy import displacy

text = open("Texts/Model3-1.txt").read()

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("merge_entities")
nlp.add_pipe("merge_noun_chunks")
# nlp.add_pipe('coreferee')
doc = nlp(text)


# print(doc[15:28])
# doc._.coref_chains.print()
# displacy.serve(doc.sents[0], style="dep")

# subjects = list(filter(lambda token: token.dep_ == "nsubj" or token.dep_ == "nsubjpass", doc))
# print(list(subjects))


class Action:
  def __init__(self, actor, action_token, *objects):
    self.actor = actor
    self.action_token = action_token
    self.objects = objects

def get_direct_ancestors(head_token, doc_):
  ancestors = []
  for token in doc_:
    if token.head == head_token:
      ancestors.append(token)
  return ancestors


def get_main_sentence(sent):
  root_token = next(filter(lambda token: token.dep_ == 'ROOT', sent))
  conjuncts = list(filter(lambda token: token.dep_ == 'conj', sent))
  conjuncts = list(map(lambda token: token.text, conjuncts))
  main_sent = []

  for token in sent:
    if (token.head == root_token
        or token.head.text in conjuncts):
      # remove adpositions and adverbs
      if token.pos_ == 'ADP' or token.pos_ == 'ADV':
        continue

      # remove punctuation
      if  token.pos_ == 'PUNCT':
        continue

      # remove adverbial clause modifiers for now
      if token.dep_ == 'advcl':
        continue

      # remove empty sentences
      if token.dep_ == 'ROOT' and token.tag_ == '_SP':
        continue

      # qualified for main sentence, add
      main_sent.append(token)


  return main_sent


# Extract actions from the text
previous_action = None
actions = []

for sent in doc.sents:

  main_sent = get_main_sentence(sent)
  actor = None
  action = None
  objects = []

  for token in main_sent:
    # filter out only main sentences
    # print(token.text, end=" ")
    if token.dep_ == 'nsubj':
      actor = token

    if token.dep_ == 'ROOT':
      action = token

    if token.dep_ == 'dobj' and token.head == action:
      objects.append(token)

    print(
      token.text + '(' + token.dep_ + ', ' + token.head.text + ')',
      end=" ")
  print('')
  # print('----')

  if actor is None and isinstance(previous_action, Action):
    actor = previous_action.actor

  current_action = Action(actor, action, objects)

  actions.append(current_action)

  previous_action = current_action

# print out all
for action in actions:
  if action.actor:
    print('Action for ' + action.actor.text + ': ' + action.action_token.lemma_, action.objects)


# get similarity
def similarity(subjects):
  for subject1Index in range(len(subjects)):
    subject1 = subjects[subject1Index]

    for subject2Index in range(subject1Index + 1, len(subjects)):
      subject2 = subjects[subject2Index]
      similarity = subject1.similarity(subject2)

      print(
          'Similarity for ' + subject1.text + ' and ' + subject2.text + ': ' + str(
              similarity))

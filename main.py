import spacy, coreferee
from spacy import displacy
from spacy.tokens import Token

import utils
from utils import Action, ParticipantStory

text = open("Texts/Model3-1.txt").read()

nlp = spacy.load("en_core_web_lg")
nlp.add_pipe("merge_entities")
nlp.add_pipe("merge_noun_chunks")
nlp.add_pipe('coreferee')
# doc = nlp('The MPOO registers at the GO.')
doc = nlp(text)

# print(doc[15:28])
doc._.coref_chains.print()
# displacy.serve(doc, style="ent")

# Extract actions from the text
previous_action = None
actions = []

for sent in doc.sents:

    # Skip sentences that have less than 2 words
    if len(sent) < 2:
        continue

    action = None

    conjunctions = []

    for token in sent:
        # Only get the main action of the sentence. Conjunctions will be
        # handled later
        if token.dep_ == 'ROOT':
            action = utils.get_action(token, doc, previous_action)

        # List the conjunctions to identify actions that are in a clause
        # connected by the conjunction
        if token.dep_ == 'conj' and token.pos_ == 'VERB':
            conjunctions.append(token)


        print(
            token.text + '(' + token.dep_ + ', ' + token.head.text + ')',
            end=" ")
    print('')

    if action.actor is None:
        if previous_action:
            action.actor = previous_action.actor
        else:
            action.actor = nlp('Unknown actor')

    actions.append(action)

    previous_action = action

    # Loop through all conjunctions and create actions from them
    for conjunction in conjunctions:
        conjunction_action = utils.get_action(conjunction, doc, previous_action)

        # Define actor if none is found
        if conjunction_action.actor is None:
            if previous_action:
                conjunction_action.actor = previous_action.actor
            else:
                action.actor = nlp('Unknown actor')

        actions.append(conjunction_action)
        previous_action = conjunction_action

print('')

actions_to_insert = []

for index, main_action in enumerate(actions):
    for child in main_action.action_token.children:
        if child.dep_ == 'advcl' and child.pos_ == 'VERB' \
         and not utils.has_marker_in_children(child):
            action = utils.get_action(child, doc, main_action, True)

            if action.actor is None:
                action.actor = main_action.actor

            actions_to_insert.append({
                "index": index + len(actions_to_insert),
                "action": action
            })


for action_to_insert in actions_to_insert:
    actions.insert(action_to_insert["index"], action_to_insert["action"])

# Remove the pipe that merges some phrases. This is needed to compare the actors
# by removing some stop words
nlp.remove_pipe('merge_entities')
nlp.remove_pipe('merge_noun_chunks')

utils.merge_actors(actions, nlp)

participant_stories = utils.generate_participant_stores(actions, nlp)

utils.print_participant_stories(participant_stories)
utils.print_actions_for_sketch_miner(actions, nlp)

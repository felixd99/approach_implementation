import spacy, coreferee
from spacy import displacy
from spacy.tokens import Token

import utils
from utils import Action, ParticipantStory

text = open("Texts/Model3-1.txt").read()

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("merge_entities")
nlp.add_pipe("merge_noun_chunks")
nlp.add_pipe('coreferee')
# doc = nlp('The person starts the game, walks away and I get killed by person.')
doc = nlp(text)

# Register custom attributes on the Token object
# 'indirect_object' will help us identify if an action has been sent to
# another actor
Token.set_extension('indirect_object', default=False)


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

    actor = None
    action = None
    objects = []

    conjunctions = []

    for token in sent:
        head_token = token.head

        # Only get the main actor of the sentence
        if token.dep_ == 'nsubj' and head_token.dep_ == 'ROOT':
            actor = token

        # Only get the main action of the sentence. Conjunctions will be
        # handled later
        if token.dep_ == 'ROOT':
            action = token

        # Get objects directly related to the main action
        if token.dep_ == 'dobj' and head_token == action:
            objects.append(token)

        # Get objects that are affected indirectly
        if token.dep_ == 'pobj' and head_token.text == 'to' \
            and head_token.head == action:
            # mark token as indirect object
            token._.indirect_object = True
            objects.append(token)

        # Check if sentence is passive and set passive object as actor
        if head_token.dep_ == 'agent' \
            and head_token.head == action and action.tag_ == 'VBN':
            actor = token

        # Add passive subject to objects
        if token.dep_ == 'nsubjpass' and head_token.dep_ == 'ROOT':
            objects.append(token)

        # List the conjunctions to identify actions that are in a clause
        # connected by the conjunction
        if token.dep_ == 'conj' and token.pos_ == 'VERB':
            conjunctions.append(token)


        print(
            token.text + '(' + token.dep_ + ', ' + token.head.text + ')',
            end=" ")
    print('')

    if actor is None and isinstance(previous_action, Action):
        actor = previous_action.actor

    current_action = Action(actor, action, objects)

    actions.append(current_action)

    previous_action = current_action

    # Loop through all conjunctions and create actions from them
    for conjunction in conjunctions:
        conjunction_action = conjunction
        conjunction_objects = []

        for token in sent:
            # Only get words related to the conjunction
            if token.head == conjunction_action:
                # Get subject of the conjunction
                if token.dep_ == 'nsubj':
                    actor = token

                # Get direct object of the conjunction
                if token.dep_ == 'dobj':
                    conjunction_objects.append(token)

                # Add passive subject to actors
                if token.dep_ == 'nsubjpass' and token.head == conjunction:
                    conjunction_objects.append(token)

                # Check if sentence is passive and set passive object as actor
                if head_token.dep_ == 'agent' \
                    and head_token.head == action and action.tag_ == 'VBN':
                    actor = token

        current_action = Action(actor, conjunction_action, conjunction_objects)
        actions.append(current_action)
        previous_action = current_action

print('')

# Remove the pipe that merges some phrases. This is needed to compare the actors
# by removing some stop words
nlp.remove_pipe('merge_entities')
nlp.remove_pipe('merge_noun_chunks')

utils.merge_actors(actions, nlp)

participant_stories = utils.generate_participant_stores(actions, nlp)



utils.print_participant_stories(participant_stories)
utils.print_actions_for_sketch_miner(actions, nlp)
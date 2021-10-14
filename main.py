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
# doc = nlp('Whenever a company makes the decision to go public, its first task is to select the underwriters.')
doc = nlp(text)

# print(doc[15:28])
doc._.coref_chains.print()
# displacy.serve(doc, style="dep")

# Extract actions from the text
previous_action = None
actions = []

for sent in doc.sents:

    # Skip sentences that have less than 2 words
    if len(sent) < 2:
        continue

    actor = None
    action = None
    direct_object = None
    indirect_objects = []

    conjunctions = []

    for token in sent:
        head_token = token.head

        # Only get the main actor of the sentence
        if token.dep_ == 'nsubj' and head_token.dep_ == 'ROOT':
            coref_actor = doc._.coref_chains.resolve(token)
            if coref_actor and len(coref_actor) > 0:
                actor = coref_actor[0]
            else:
                actor = token

            # If token is still a pronoun, choose previous actor
            if actor.pos_ == 'PRON' and previous_action:
                actor = previous_action.actor

        # Only get the main action of the sentence. Conjunctions will be
        # handled later
        if token.dep_ == 'ROOT':
            action = token

        # Get objects directly related to the main action
        if token.dep_ == 'dobj' and head_token == action:
            direct_object = token
            # See if the direct object is a co-reference
            coref_object = doc._.coref_chains.resolve(token)
            if coref_object and len(coref_object) > 0:
                direct_object = coref_object[0]

        # Get objects that are affected indirectly
        if token.dep_ == 'pobj' \
            and head_token.head == action:
            # mark token as indirect object
            indirect_objects.append(token)

        # Check if sentence is passive and set passive object as actor
        if head_token.dep_ == 'agent' \
            and head_token.head == action and action.tag_ == 'VBN':
            actor = token

        # Add passive subject to objects
        if token.dep_ == 'nsubjpass' and head_token.dep_ == 'ROOT':
            direct_object = token

        # List the conjunctions to identify actions that are in a clause
        # connected by the conjunction
        if token.dep_ == 'conj' and token.pos_ == 'VERB':
            conjunctions.append(token)


        print(
            token.text + '(' + token.dep_ + ', ' + token.head.text + ')',
            end=" ")
    print('')

    if actor is None:
        if previous_action:
            actor = previous_action.actor
        else:
            actor = nlp('Unknown actor')

    # Skip if no actor and action has been found (i.e. NLP failed)
    # if not actor or not action:
    #     continue

    current_action = Action(actor, action, direct_object, indirect_objects)

    actions.append(current_action)

    previous_action = current_action

    # Loop through all conjunctions and create actions from them
    for conjunction in conjunctions:
        conjunction_action = conjunction
        conjunction_object = None
        conjunction_indirect_objects = []

        for token in sent:
            # Only get words related to the conjunction
            if token.head == conjunction_action:
                # Get subject of the conjunction
                if token.dep_ == 'nsubj':
                    coref_actor = doc._.coref_chains.resolve(token)
                    if coref_actor and len(coref_actor) > 0:
                        actor = coref_actor[0]
                    else:
                        actor = token

                # Get direct object of the conjunction
                if token.dep_ == 'dobj':
                    conjunction_object = token
                    # See if the direct object is a co-reference
                    coref_object = doc._.coref_chains.resolve(token)
                    if coref_object and len(coref_object) > 0:
                        conjunction_object = coref_object[0]

                # Add passive subject to actors
                if token.dep_ == 'nsubjpass' and token.head == conjunction:
                    conjunction_object = token

                # Check if sentence is passive and set passive object as actor
                if token.head.dep_ == 'agent' \
                    and token.head.head == action and action.tag_ == 'VBN':
                    actor = token

            # Get objects that are affected indirectly
            if token.dep_ == 'pobj' and \
                token.head.head == conjunction_action:
                # mark token as indirect object
                conjunction_indirect_objects.append(token)

        current_action = Action(actor, conjunction_action, conjunction_object, conjunction_indirect_objects)
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
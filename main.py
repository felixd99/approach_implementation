import spacy, coreferee
from spacy import displacy
from spacy.tokens import Token

import utils

text = open("Texts/Model10-12.txt").read()

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
# doc._.coref_chains.print()
displacy.serve(doc, style="ent")

class Action:
    def __init__(self, actor, action_token, objects, *next):
        self.actor = actor
        self.action_token = action_token
        self.objects = objects
        self.next = next


class ParticipantStory:
    def __init__(self, actor, actions):
        self.actor = actor
        self.actions = actions


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
        if token.dep_ == 'conj':
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

participant_stories = []

for action in actions:
    actor = nlp(action.actor.text)

    # Check if the actor is a valid actor. If not (e.g. 'the process' or
    # 'the workflow', just ignore those actions
    if not utils.is_valid_actor(actor, nlp):
        print('---')
        print('Invalid actor: ', actor)
        print('---')
        continue

    participant_story = utils.find_participant_story_for_actor(actor, participant_stories)
    action = utils.build_action_name(action)

    # Check if there is already a participant story for the actor, if so just
    # add the action to it
    if participant_story:
        participant_story.actions.append(action)
    else:
        participant_story = ParticipantStory(actor, [action])
        participant_stories.append(participant_story)

    # print(action.actor, action.action_token)
    # if action.actor and action.action_token:
    #     print(
    #         'Action for ' + action.actor.text + ': ' + action.action_token.lemma_,
    #         action.objects[0])

for participant_story in participant_stories:
    print('--- ' + participant_story.actor.text + ' ---')

    for (number, participant_action) in enumerate(participant_story.actions):
        print(str(number + 1) + '. ' + participant_action)

    print('')
    print('')
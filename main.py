import copy

import spacy, coreferee
from spacy import displacy
from spacy.tokens import Token

import nlp_utils
import utils
import print_utils
from utils import Action, ConditionAction, ParticipantStory

text = open("Texts/Model3-6.txt").read()

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

# Iterative over every sentence of the text
for number, sent in enumerate(doc.sents):

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

        if number == 2:
            print(
                token.text + '(' + token.dep_ + ', ' + token.head.text + ', ' +
                    token.pos_ + ')',
                end=" ")
            print('')
            # displacy.serve(sent, style="dep")

    if action.actor is None:
        if previous_action:
            action.actor = previous_action.actor
        else:
            action.actor = nlp('Unknown actor')

    actions.append(action)

    previous_action = action

    print('Conjunctions for:', action.action_token, action.action_token.conjuncts)

    # Loop through all conjunctions and create actions from them
    for conjunction in action.action_token.conjuncts:
        if not conjunction.pos_ == 'VERB':
            continue
        conjunction_action = utils.get_action(conjunction, doc, previous_action)

        # Define actor if none is found
        if conjunction_action.actor is None:
            if previous_action:
                conjunction_action.actor = previous_action.actor
            else:
                action.actor = nlp('Unknown actor')

        # Check if it's a "regular" conjunction or a conditional statement
        cc = nlp_utils.get_connecting_conjunction(doc, action.action_token, conjunction_action.action_token)
        if cc.text == 'and':
            actions.append(conjunction_action)
            previous_action = conjunction_action
        elif cc.text == 'or':
            main_action_index = actions.index(action)
            if main_action_index > 0:
                # remove action (since it will be in the conditions list)
                previous_main_action = actions[main_action_index - 1]
                del actions[main_action_index]
                # Insert new ConditionAction instead
                condition_action = ConditionAction(None, [action], [conjunction_action])

                # if previous_main_action.condition:
                #     previous_action = previous_main_action
                # else:
                previous_main_action.condition = condition_action
                previous_action = previous_main_action
        # actions.append(conjunction_action)
        # previous_action = conjunction_action

print('')

actions_to_insert = []
actions_to_remove = []

# Get actions from subclauses
for index, main_action in enumerate(actions):
    print('Checking action', main_action.action_token)
    # Storing index for later usage
    main_action_index = actions.index(main_action)
    # Loop through all children to detect subclauses
    for child in main_action.action_token.children:
        if child.dep_ == 'advcl' and child.pos_ in ['VERB', 'AUX', 'PART']:
            # If it indicates a condition, insert it as such
            condition_marker = utils.get_marker_in_children(child)

            if condition_marker:
                subclause = nlp_utils.get_subclause_from_conditional_marker(condition_marker, doc)
                if main_action_index > 0:
                    # remove action (since it will be in the conditions list)
                    previous_main_action = actions[main_action_index - 1]
                    del actions[main_action_index]
                    # Insert new ConditionAction instead
                    condition_action = ConditionAction(subclause, [main_action], [])
                    if previous_main_action.condition:
                        copied_action = copy.copy(previous_main_action)
                        copied_action.is_a_copy = True
                        copied_action.condition = condition_action
                        actions.insert(main_action_index, copied_action)
                    else:
                        previous_main_action.condition = condition_action
                        previous_action = previous_main_action
            else:
                # Check if is passive, then it's an action => print for SketchMiner
                is_action = child.tag_ == 'VBN' or child.lemma_ == 'be'
                # Build the action from the verb
                action = utils.get_action(child, doc, main_action, is_action)
                # Check if subclause is before or after main clause
                is_right = action.action_token in main_action.action_token.rights

                # Set main action's actor if none was found
                if action.actor is None:
                    action.actor = main_action.actor
                else:
                    # If the main action's actor is a pronoun, we can resolve it
                    if main_action.actor.pos_ == 'PRON':
                        main_action.actor = action.actor

                # If the main action's direct_object is a pronoun, we can resolve it
                if main_action.direct_object and main_action.direct_object.pos_ == 'PRON':
                    main_action.direct_object = action.direct_object

                actions_to_insert.append({
                    "index": index + len(actions_to_insert) + (1 if is_right else 0),
                    "action": action
                })
    # See if we have any 'Otherwise' or 'Else' sentences. If so, add them to the
    # previous condition
    else_condition_marker = utils.get_else_marker_in_children(main_action.action_token)
    if else_condition_marker:
        # remove action (since it will be in the conditions list) and merge all
        # actions in between
        previous_condition = utils.merge_previous_condition(actions, main_action)
        if previous_condition:
            previous_condition.condition.right_actions.append(main_action)
            del actions[actions.index(main_action)]


for action_to_insert in actions_to_insert:
    actions.insert(action_to_insert["index"], action_to_insert["action"])

# Remove the pipe that merges some phrases. This is needed to compare the actors
# by removing some stop words
nlp.remove_pipe('merge_entities')
nlp.remove_pipe('merge_noun_chunks')

utils.merge_actors(actions, nlp)

participant_stories = print_utils.generate_participant_stores(actions, nlp, doc)

# print_utils.print_participant_stories(participant_stories)
print_utils.print_actions_for_sketch_miner(actions, nlp, len(participant_stories), doc)

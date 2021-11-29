import copy

import spacy, coreferee
from spacy import displacy
from spacy.tokens import Token

import nlp_utils
import text_preprocessor
import utils
import print_utils
import pyinflect
from utils import Action, ConditionAction, ParticipantStory

nlp = spacy.load("en_core_web_lg")


def transform_text(path, print_numerical, print_agile, print_sketch, print_help):

    text = open(path).read()

    processed_text = text_preprocessor.process(text)

    nlp.add_pipe("merge_entities")
    nlp.add_pipe("merge_noun_chunks")
    if not nlp.has_pipe("coreferee"):
        nlp.add_pipe('coreferee')
    # doc = nlp('The MPOO registers at the GO.')
    doc = nlp(processed_text)

    # print(doc[15:28])
    if print_help:
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

        # In case it is not a valid sentence (e.g. SPACE is the root token), we skip
        ignore_sentence = False

        for token in sent:
            # Only get the main action of the sentence. Conjunctions will be
            # handled later
            if token.dep_ == 'ROOT':
                if token.pos_ in ['SPACE', 'X'] or token.tag_ == 'LS':
                    ignore_sentence = True
                action = utils.get_action(token, doc, previous_action)

            if number == 0 and print_help:
                print(
                    token.text + '(' + token.dep_ + ', ' + token.head.text + ')',
                    end=" ")
                print('')
                # displacy.serve(sent, style="dep")

        if ignore_sentence:
            continue

        if action.actor is None:
            if previous_action:
                action.actor = previous_action.actor
            else:
                action.actor = nlp('Unknown actor')[0]

        actions.append(action)

        previous_action = action

        if print_help:
            print('')

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
                    action.actor = nlp('Unknown actor')[0]

            # Check if it's a "regular" conjunction or a conditional statement
            cc = nlp_utils.get_connecting_conjunction(doc, action.action_token, conjunction_action.action_token)
            if cc and cc.text == 'and':
                actions.append(conjunction_action)
                previous_action = conjunction_action
            elif cc and (cc.text == 'or' or cc.text == 'but'):
                if action in actions:
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
            else:
                actions.append(conjunction_action)
                previous_action = conjunction_action

    if print_help:
        print('')

    actions_to_insert = []
    actions_to_remove = []


    # Get actions from subclauses
    for index, main_action in enumerate(actions):
        # Storing index for later usage
        main_action_index = actions.index(main_action)

        # If we find a previous action in the subclauses, we set it otherwise just
        # the next action
        previous_action_was_set = False

        # Loop through all children to detect subclauses
        for child in main_action.action_token.children:

            if child.dep_ == 'advcl' and child.pos_ in ['VERB', 'AUX', 'PART']:
                # If it indicates a condition, insert it as such
                condition_marker = utils.get_marker_in_children(child)

                if condition_marker:
                    subclause = nlp_utils.get_subclause_from_token_on(condition_marker, doc)
                    if main_action_index > 0:
                        # remove action (since it will be in the conditions list)
                        previous_main_action = actions[main_action_index - 1]
                        actions_to_remove.append(actions[main_action_index])
                        # Insert new ConditionAction instead
                        condition_action = ConditionAction(subclause, [main_action], [])

                        if not previous_action.is_a_copy:
                            if previous_action.condition:
                                copied_action = copy.copy(previous_action)
                                copied_action.is_a_copy = True
                                copied_action.condition = condition_action

                                actions.insert(main_action_index, copied_action)
                                previous_action = copied_action
                                previous_action_was_set = True
                                # actions_to_insert.append({
                                #     "index": main_action_index,
                                #     "action": copied_action
                                # })
                            else:
                                previous_main_action.condition = condition_action
                                previous_action = previous_main_action
                                previous_action_was_set = True
                        else:
                            previous_action = main_action
                            previous_action_was_set = True
                    else:
                        # The first action is a condition
                        # condition_action = ConditionAction(subclause, [main_action], [])
                        # copied_action = copy.copy(main_action)
                        # copied_action.is_a_copy = True
                        # copied_action.condition = condition_action
                        # previous_action = main_action
                        # actions.insert(0, copied_action)
                        pass

                else:
                    event_text = None
                    # If it indicates a condition, insert it as such
                    event_marker = utils.get_event_marker_in_children(child)

                    # Get event text if it's an event
                    if event_marker:
                        event_text = nlp_utils.get_subclause_from_token_on(
                            event_marker, doc)

                    # Build the action from the verb
                    action = utils.get_action(child, doc, main_action, event_text)

                    # Check if subclause is before or after main clause
                    is_right = action.action_token in main_action.action_token.rights

                    # Set main action's actor if none was found
                    if action.actor is None:
                        action.actor = main_action.actor
                    else:
                        # If the main action's actor is a pronoun, we can resolve it
                        if main_action.actor.pos_ == 'PRON' \
                          or main_action.actor.text == 'Unknown actor':
                            main_action.actor = action.actor

                    # If the main action's direct_object is a pronoun, we can resolve it
                    if main_action.direct_object and main_action.direct_object.pos_ == 'PRON':
                        main_action.direct_object = action.direct_object

                    action_index = actions.index(main_action)

                    actions_to_insert.append({
                        "index": action_index + len(actions_to_insert) + (1 if is_right else 0),
                        "action": action
                    })
            elif child.dep_ == 'pobj':
                # Get relative clause modifiers
                for rel_child in child.children:
                    if rel_child.dep_ == 'relcl':
                        # Build the action from the verb
                        action = utils.get_action(rel_child, doc, main_action,
                                                  None)

                        # Actor is the direct object
                        action.actor = child

                        action_index = actions.index(main_action)

                        actions_to_insert.append({
                            "index": action_index + len(actions_to_insert) + 1,
                            "action": action
                        })

        if not previous_action_was_set:
            previous_action = main_action

        # See if we have any 'Otherwise' or 'Else' sentences. If so, add them to the
        # previous condition
        else_condition_marker = utils.get_else_marker_in_children(main_action.action_token)
        if else_condition_marker:
            # remove action (since it will be in the conditions list) and merge all
            # actions in between
            previous_condition = utils.merge_previous_condition(actions, main_action, actions_to_remove)
            if previous_condition:
                previous_condition.condition.right_actions.append(main_action)
                actions_to_remove.append(main_action)
                # del actions[actions.index(main_action)]


    # We need to insert/remove the actions after the
    for action_to_insert in actions_to_insert:
        insert_index = action_to_insert["index"]
        insert_action = action_to_insert["action"]
        if insert_index > 0:
            previous_action = actions[insert_index - 1]
            if previous_action.condition:
                insert_action.condition = previous_action.condition
                previous_action.condition = None
        actions.insert(insert_index, insert_action)

    for action_to_remove in actions_to_remove:
        if action_to_remove in actions:
            ac = actions.index(action_to_remove)
            del actions[actions.index(action_to_remove)]

    # Remove the pipe that merges some phrases. This is needed to compare the actors
    # by removing some stop words
    nlp.remove_pipe('merge_entities')
    nlp.remove_pipe('merge_noun_chunks')

    utils.merge_actors(actions, nlp)

    participant_stories = print_utils.generate_participant_stores(actions, nlp, doc)

    if print_numerical:
        print_utils.print_participant_stories(participant_stories, doc)

    if print_agile:
        print_utils.print_user_stories_for_agile_methods(participant_stories, actions, doc)

    if print_sketch:
        print_utils.print_actions_for_sketch_miner(actions, nlp, len(participant_stories), doc)

    return {
        "actions": actions,
        "participant_stories": participant_stories
    }


# transform_text("Texts/Model7-1.txt", False, False, True, True)
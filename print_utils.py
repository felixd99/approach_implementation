import nlp_utils
import utils
from utils import Action, ParticipantStory

already_printed_action = {}
condition_actions = {}


def build_action_name(action, for_sketch_miner, for_participant_stories, doc):
    action_name = ''
    # Check if the action is an event and passive
    if action.event_text:
        if for_sketch_miner:
            action_name = '(' + action.event_text
        else:
            action_name = 'Event: ' + action.event_text
    else:
        # Print special events in sketch miner
        if for_sketch_miner and action.verb.lemma_ in special_event_indicators:
            action_name = build_sketch_miner_event_name(action, doc)
        else:
            # Print special tokens (e.g. xcomp, ccomp or "to be" sentence)
            special_tokens = get_special_action_tokens(action, doc)

            if special_tokens:
                action_name += special_tokens
            else:
                # If we have participant story, we need to print the verb in past
                # tense
                if for_participant_stories:
                    action_name = action.verb._.inflect("VBD")
                    # If inflection is not possible, use the lemma
                    action_name = action.verb.lemma_ \
                        if action_name is None else action_name
                else:
                    action_name = action.verb.lemma_
                action_name += ' ' + action.direct_object.text \
                    if action.direct_object else ''

    if not action.event_text:
        action_name += get_indirect_objects(action)

    if (action.event_text or action.verb.lemma_ in special_event_indicators) \
        and for_sketch_miner:
        action_name += ')'

    if action.is_a_copy:
        action_name = '()'

    return action_name


def get_indirect_objects(action):
    appended_objects = ''
    for indirect_object in action.indirect_objects:
        # Skip objects that don't provide any value e.g. "after that"
        if indirect_object.text.lower() in objects_to_ignore:
            continue

        # Skip objects that indicate the passive actor
        if action.verb.tag_ == 'VBN' and \
            (indirect_object.head.dep_ == 'agent' or
             indirect_object.head.text == 'by'):
            continue

        preposition = ' '
        # If the object has a preposition (or dative), then we also print this
        if indirect_object.head.dep_ == 'prep' \
            or indirect_object.head.dep_ == 'dative':
            preposition = ' ' + indirect_object.head.text + ' '

        appended_objects += preposition + indirect_object.text

    return appended_objects


def build_sketch_miner_event_name(action, doc):
    action_name = ''

    # Set subject as direct_object if it's a form of 'be'
    # (e.g. "Once all files are ready"), otherwise use the direct object
    direct_object = None
    if action.verb.lemma_ == 'be':
        direct_object = action.actor
    elif action.direct_object:
        direct_object = action.direct_object

        if action.verb.lemma_ in special_event_indicators:
            action_name = '(' + action.verb.lemma_
            action_name += ' ' + direct_object.text
        else:
            action_name = '(' + direct_object.text
            action_name += ' ' + get_special_action_tokens(action, doc)

    return action_name


# If the action is a special word such as "be" or "need", we need to print all
# subsequent elements
def get_special_action_tokens(action, doc):
    action_name = None
    comp_child_token = nlp_utils.get_xcomp_ccomp_in_children(action)
    has_multiple_dobjs = nlp_utils.has_mulitple_direct_objects(action.verb)
    if action.verb.lemma_ == 'be' or action.verb.dep_ == 'advcl' \
        or comp_child_token is not None or has_multiple_dobjs:

        action_name = action.verb.text \
            if action.verb.lemma_ == 'be' else action.verb.lemma_
        subclause = get_subclause(action.verb, doc)

        for token_right in subclause:
            action_name += ' ' + utils.resolve_coreferences(token_right, doc).text

    return action_name


def get_subclause(action, doc):
    punct_token = None
    # Get the next punctation (most likely indicating that the subclause ennded)
    # OR the next connecting conjunction which is related
    for right_action in action.rights:
        if right_action.tag_ == '.' \
         or (right_action.dep_ == 'cc' and right_action.head == action):
            punct_token = right_action
            break

    # In case nothing was found, use the head's rights
    if punct_token is None:
        for head_right_action in action.head.rights:
            if head_right_action.tag_ == '.':
                punct_token = head_right_action
                break

    # In case still nothing was found, just use rights (should not be the case)
    if punct_token is None:
        return action.rights

    subclause_tokens = []

    for subclause_token in doc[action.i + 1:punct_token.i]:
        # Only add the word if it's in the subtree (== subclause)
        # print('Subclause token', subclause_token, subclause_token in action.subtree)
        if subclause_token in action.subtree:
            if subclause_token.text.lower() in utils.conditional_marks:
                # Do not include the conditional sentences
                break
            else:
                subclause_tokens.append(subclause_token)

    return subclause_tokens


def print_sketch_miner_line(number_of_actors, actor, action_name, condition_id):
    global already_printed_action
    global condition_actions
    sketch_miner_line = ''

    # only print actor if we have valid ones
    print_actor = number_of_actors > 1 or \
                  (number_of_actors == 1 and not actor.text == 'Unknown actor')
    if print_actor:
        sketch_miner_line = actor.text + ': ' + action_name
    else:
        sketch_miner_line = action_name

    is_wrong_action_condition = sketch_miner_line in condition_actions and \
                       condition_id != condition_actions[sketch_miner_line]

    is_correct_action_condition = sketch_miner_line in condition_actions and \
                        condition_id == condition_actions[sketch_miner_line]

    # if the line was already printed for this actor, we need to change it
    # as otherwise the SketchMiner will make a loop out of it
    if is_wrong_action_condition and not action_name == '()':
        map_variable_name = actor.text + action_name
        amount = already_printed_action[map_variable_name] if (
                map_variable_name in
                already_printed_action) else 0

        if amount != 0:
            sketch_miner_line += ' (' + str(amount) + ')'
        # Increase the counter
        already_printed_action[map_variable_name] = amount + 1
    else:
        map_variable_name = actor.text + action_name
        if is_correct_action_condition:
            amount = already_printed_action[map_variable_name]
            already_printed_action[map_variable_name] = amount + 1
        else:
            already_printed_action[map_variable_name] = 1

    # Add the action to used actions for this condition
    condition_actions[sketch_miner_line] = condition_id

    # Print the line
    print(sketch_miner_line)


def print_actions_for_sketch_miner(actions, nlp, number_of_actors, doc):
    condition_loop_id = 0
    next_action_condition_id = None
    for action in actions:
        current_condition_id = condition_loop_id
        actor = nlp(action.actor.text)

        # Check if the actor is a valid actor. If not (e.g. 'the process' or
        # 'the workflow', just ignore those actions
        if not utils.is_valid_actor(actor, nlp) and not action.event_text:
            continue

        action_name = build_action_name(action, True, False, doc)
        condition_action = action.condition

        if condition_action:
            # Get the id of the condition to serialize it
            current_condition_id = id(condition_action)

            # Get next action if available (needed for Sketch Miner)
            next_action_index = actions.index(action) + 1
            next_action = None

            if next_action_index < len(actions):
                next_action = actions[next_action_index]
                next_action_name = build_action_name(next_action, True, False, doc)

                next_action_condition_id = id(next_action.condition) \
                    if next_action.condition else condition_loop_id + 1

            # Print left side
            print_sketch_miner_line(number_of_actors, actor, action_name,
                                    current_condition_id)

            # Print "If" condition if there is one
            if condition_action.condition_phrase:
                print(condition_action.condition_phrase + '?')
                print('True')

            for left_action in condition_action.left_actions:
                left_action_name = build_action_name(left_action, True, False, doc)
                print_sketch_miner_line(number_of_actors, left_action.actor,
                                        left_action_name, current_condition_id * 2)

            # Print next action if available, otherwise just end
            if next_action:
                print_sketch_miner_line(number_of_actors, next_action.actor,
                                        next_action_name,
                                        next_action_condition_id)
                print('...')

            # Print right side
            print('')
            print('...')
            print_sketch_miner_line(number_of_actors, actor, action_name,
                                    current_condition_id)

            # Print else condition if there is one
            if condition_action.condition_phrase:
                print(condition_action.condition_phrase + '?')
                print('False')

            for right_action in condition_action.right_actions:
                right_action_name = build_action_name(right_action, True, False, doc)
                print_sketch_miner_line(number_of_actors, right_action.actor,
                                        right_action_name, current_condition_id * 2)

            # Print next action if available, otherwise just end
            if next_action:
                print_sketch_miner_line(number_of_actors, next_action.actor,
                                        next_action_name,
                                        next_action_condition_id)
                print('...')
                print('')
                print('...')

        else:
            print_sketch_miner_line(number_of_actors, actor, action_name, next_action_condition_id if next_action_condition_id else current_condition_id)
            condition_loop_id = condition_loop_id + 1

    # Reset variables
    global already_printed_action
    global condition_actions
    already_printed_action = {}
    condition_actions = {}


def print_participant_stories(participant_stories, doc):
    for participant_story in participant_stories:
        print('--- ' + participant_story.actor.text + ' ---')

        number = 1

        for participant_action in participant_story.actions:
            if participant_action["action"].condition:
                condition = participant_action["action"].condition
                # First print action, then condition
                # Also, skip placeholder actions
                if participant_action["action_name"] != '()':
                    print(str(number) + '. ' + participant_action["action_name"])
                    number = number + 1

                if condition.condition_phrase:
                    # It's an if condition
                    # Print condition
                    print('If ' + condition.condition_phrase)

                    # Only print indices for the actions if there are more than 1
                    print_left_action = len(condition.left_actions) > 1
                    print_right_action = len(condition.right_actions) > 1

                    # Print left side first
                    for left_index, left_action in enumerate(condition.left_actions):
                        left_action_name = build_action_name(left_action, False, False, doc)
                        left_action_index = '.' + str(left_index + 1) if print_left_action \
                                                else ')'
                        print('\t' + str(number) + 'a' + left_action_index + ' ' + left_action_name)

                    if len(condition.right_actions) > 0:
                        print('Else')

                    # Print right side
                    for right_index, right_action in enumerate(condition.right_actions):
                        right_action_name = build_action_name(right_action, False, False, doc)
                        right_action_index = '.' + str(right_index + 1) if print_right_action \
                                                else ')'
                        print('\t' + str(number) + 'b' + right_action_index + ' ' + right_action_name)
                else:
                    # It's an exclusive condition
                    # Print left side first
                    for left_action in condition.left_actions:
                        left_action_name = build_action_name(left_action, False, False, doc)
                        print(str(number) + 'a)' + ' ' + left_action_name)

                    # Print right side
                    for right_action in condition.right_actions:
                        right_action_name = build_action_name(right_action, False, False, doc)
                        print(str(number) + 'b)' + ' ' + right_action_name)
            else:
                print(str(number) + '. ' + participant_action["action_name"])

            # Increase counter
            number = number + 1

        print('')
        print('')


def generate_participant_stores(actions, nlp, doc):
    participant_stories = []
    for action in actions:
        actor = nlp(action.actor.text)

        # Check if the actor is a valid actor. If not (e.g. 'the process' or
        # 'the workflow', just ignore those actions
        if not utils.is_valid_actor(actor, nlp) and not action.event_text:
            continue

        participant_story = utils.find_participant_story_for_actor(actor, participant_stories)
        action_name = build_action_name(action, False, False, doc)

        # Check if there is already a participant story for the actor, if so
        # just add the action to it
        if participant_story:
            participant_story.actions.append({
                "action": action,
                "action_name": action_name
            })
        else:
            participant_story = ParticipantStory(actor, [{
                "action": action,
                "action_name": action_name
            }])
            participant_stories.append(participant_story)

    return participant_stories


def print_user_stories_for_agile_methods(participant_stories, all_actions, doc):
    for participant_story in participant_stories:
        # Iterate through all users
        actor_name = participant_story.actor.text

        for participant_action in participant_story.actions:
            action = participant_action["action"]
            # If the action is an event, we don't print it but instead if a
            # previous action is an event, we include it
            if action.event_text:
                continue

            previous_action = utils.get_previous_action(action, all_actions)

            if not action.is_a_copy:
                print('AS ' + actor_name)
                print('I WANT TO ' + participant_action["action_name"])
                # Print previous action if there is one
                if previous_action and not previous_action.is_a_copy:
                    # If it's an event,
                    if previous_action.event_text:
                        print('WHEN ' + previous_action.event_text)
                    else:
                        previous_action_name = build_action_name(previous_action, False, True, doc)
                        actor_text = 'I' if previous_action.actor.text.lower() == participant_story.actor.text.lower() \
                                         else previous_action.actor.text
                        print('AFTER ' + actor_text + ' ' + previous_action_name)
                print('')

            # Print the condition if there is one
            if action.condition:
                print('AS ' + actor_name)

                condition_action = action.condition

                if condition_action.condition_phrase:
                    # We have an if-(else) condition
                    print('I WANT TO', end=' ')
                    for index, left_action in enumerate(condition_action.left_actions):
                        if index != 0:
                            print('\t AND', end=' ')
                        print(build_action_name(left_action, False, False, doc))
                    # Print condition phrase
                    print('IF ' + condition_action.condition_phrase)

                    # Print else actions if there are
                    for index, right_action in enumerate(condition_action.right_actions):
                        if index == 0:
                            print('OTHERWISE', end=' ')
                        else:
                            print('\t AND', end=' ')
                        print(build_action_name(right_action, False, False, doc))
                else:
                    # We most likely have a simple either-or structure
                    print('I WANT TO', end=' ')
                    has_right_actions = len(condition_action.right_actions) > 0
                    if has_right_actions:
                        print('EITHER', end=' ')
                    print(build_action_name(condition_action.left_actions[0], False, False, doc))
                    if has_right_actions:
                        print('OR ' + build_action_name(condition_action.right_actions[0], False, False, doc))

                print('')

        print('----')
        print('')


special_event_indicators = [
    'receive',
    'send'
]


objects_to_ignore = [
    'that',
    'this',
    'addition',
    'each'
]
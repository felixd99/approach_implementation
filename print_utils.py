import nlp_utils
import utils
from utils import Action, ParticipantStory


def build_action_name(action, for_sketch_miner, doc):
    action_name = ''
    # Check if the action is an event and passive
    if action.is_event:
        if for_sketch_miner:
            action_name = build_sketch_miner_event_name(action, doc)
        else:
            # Get auxiliary for the passive verb
            aux_pass = get_aux_pass(action.action_token)

            # Set subject as direct_object if it's a form of 'be'
            # (e.g. "Once all files are ready"), otherwise use the direct object
            direct_object = None
            if action.action_token.lemma_ == 'be':
                direct_object = action.actor
            elif action.direct_object:
                direct_object = action.direct_object

            action_name = 'Event: '

            # Print special tokens (e.g. xcomp, ccomp or "to be" sentence)
            special_tokens = get_special_action_tokens(action, doc)

            if special_tokens:
                action_name += special_tokens
            else:
                action_name += direct_object.text if direct_object else ''
                action_name += (' ' + aux_pass.text) if aux_pass else ''
                action_name += ' ' + action.action_token.lemma_
    else:
        # Print special events in sketch miner
        if for_sketch_miner and action.action_token.lemma_ in special_event_indicators:
            action_name = build_sketch_miner_event_name(action, doc)
        else:
            # Print special tokens (e.g. xcomp, ccomp or "to be" sentence)
            special_tokens = get_special_action_tokens(action, doc)

            if special_tokens:
                action_name += special_tokens
            else:
                action_name = action.action_token.lemma_
                action_name += ' ' + action.direct_object.text \
                    if action.direct_object else ''

    action_name += get_indirect_objects(action)

    if (action.is_event or action.action_token.lemma_ in special_event_indicators) \
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
        if action.action_token.tag_ == 'VBN' and \
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
    if action.action_token.lemma_ == 'be':
        direct_object = action.actor
    elif action.direct_object:
        direct_object = action.direct_object

    if action.action_token.lemma_ in special_event_indicators:
        action_name = '(' + action.action_token.lemma_
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
    has_multiple_dobjs = nlp_utils.has_mulitple_direct_objects(action.action_token)
    if action.action_token.lemma_ == 'be' or action.action_token.dep_ == 'advcl' \
        or comp_child_token is not None or has_multiple_dobjs:

        action_name = action.action_token.text \
            if action.action_token.lemma_ == 'be' else action.action_token.lemma_
        subclause = get_subclause(action.action_token, doc)

        for token_right in subclause:
            action_name += ' ' + utils.resolve_coreferences(token_right, doc).text

    return action_name


def get_aux_pass(action):
    for token in action.children:
        if token.dep_ == 'auxpass':
            return token
    return None


def get_subclause(action, doc):
    punct_token = None
    # Get the next punctation (most likely indicating that the subclause ennded)
    for right_action in action.rights:
        if right_action.tag_ == '.':
            punct_token = right_action
            break

    # In case nothing was found, just return the rights (should not be the case)
    if punct_token is None:
        return action.rights

    subclause_tokens = []

    for subclause_token in doc[action.i + 1:punct_token.i]:
        # Only add the word if it's in the subtree (== subclause)
        # print('Subclause token', subclause_token, subclause_token in action.subtree)
        if subclause_token in action.subtree:
            subclause_tokens.append(subclause_token)

    return subclause_tokens

def is_conditional_mark(token):
    pass


def print_participant_stories(participant_stories):
    for participant_story in participant_stories:
        print('--- ' + participant_story.actor.text + ' ---')

        for (number, participant_action) in enumerate(
            participant_story.actions):
            if participant_action.condition:
                print('TOKNE:', participant_action)
            else:
                print(str(number + 1) + '. ' + participant_action)

        print('')
        print('')


def print_actions_for_sketch_miner(actions, nlp, number_of_actors, doc):
    for action in actions:
        actor = nlp(action.actor.text)

        # Check if the actor is a valid actor. If not (e.g. 'the process' or
        # 'the workflow', just ignore those actions
        if not utils.is_valid_actor(actor, nlp) and not action.is_event:
            continue

        action_name = build_action_name(action, True, doc)
        condition_action = action.condition

        if condition_action:
            # Get next action if available (needed for Sketch Miner)
            next_action_index = actions.index(action) + 1
            next_action = None

            if next_action_index < len(actions):
                next_action = actions[next_action_index]
                next_action_name = build_action_name(next_action, True, doc)

            # Print left side
            print_sketch_miner_line(number_of_actors, actor, action_name)

            # Print "If" condition if there is one
            if condition_action.condition_phrase:
                print(condition_action.condition_phrase + '?')
                print('True')

            for left_action in condition_action.left_actions:
                left_action_name = build_action_name(left_action, True, doc)
                print_sketch_miner_line(number_of_actors, left_action.actor,
                                        left_action_name)

            # Print next action if available, otherwise just end
            if next_action:
                print_sketch_miner_line(number_of_actors, next_action.actor,
                                        next_action_name)
                print('...')

            # Print right side
            print('')
            print('...')
            print_sketch_miner_line(number_of_actors, actor, action_name)

            # Print else condition if there is one
            if condition_action.condition_phrase:
                print(condition_action.condition_phrase + '?')
                print('False')

            for right_action in condition_action.right_actions:
                right_action_name = build_action_name(right_action, True, doc)
                print_sketch_miner_line(number_of_actors, right_action.actor,
                                        right_action_name)

            # Print next action if available, otherwise just end
            if next_action:
                print_sketch_miner_line(number_of_actors, next_action.actor,
                                        next_action_name)
                print('...')
                print('')
                print('...')
        else:
            print_sketch_miner_line(number_of_actors, actor, action_name)


def print_sketch_miner_line(number_of_actors, actor, action_name):
    # only print actor if we have valid ones
    print_actor = number_of_actors > 1 or \
                  (number_of_actors == 1 and not actor.text == 'Unknown actor')
    if print_actor:
        print(actor.text + ': ' + action_name)
    else:
        print(action_name)

def generate_participant_stores(actions, nlp, doc):
    participant_stories = []
    for action in actions:
        actor = nlp(action.actor.text)

        # Check if the actor is a valid actor. If not (e.g. 'the process' or
        # 'the workflow', just ignore those actions
        if not utils.is_valid_actor(actor, nlp) and not action.is_event:
            continue

        participant_story = utils.find_participant_story_for_actor(actor, participant_stories)
        action = build_action_name(action, False, doc)

        # Check if there is already a participant story for the actor, if so
        # just add the action to it
        if participant_story:
            participant_story.actions.append(action)
        else:
            participant_story = ParticipantStory(actor, [action])
            participant_stories.append(participant_story)

    return participant_stories


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
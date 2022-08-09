import sql

import actions
from actions import message

import random


def make_a_decision( data ):
    events = [
        [
            get_chance_of_random_conjoined_messages(),
            actions.message.send_random_conjoined_messages
        ],
        [
            get_chance_of_random_message_with_similar_word(),
            actions.message.send_random_message_with_similar_word
        ],
        [
            get_chance_of_similar_message(),
            actions.message.send_similar_message
        ],
        [
            get_chance_of_response_message(),
            actions.message.send_response_message
        ],
        [
            get_chance_of_poll(),
            actions.message.send_poll
        ],
        [
            get_chance_of_meme(),
            actions.message.send_random_meme
        ],
        [
            get_chance_of_meme_with_similar_message(),
            actions.message.send_random_meme_with_similar_message
        ],
        [
            get_chance_of_photo_distortion(),
            actions.message.send_photo_distortion
        ],
        [
            get_chance_of_hokku(),
            actions.message.send_hokku
        ],
        [
            get_chance_of_consonant_removal(),
            actions.message.send_consonant_removal
        ],
        [
            get_chance_of_uppercase_mockery(),
            actions.message.send_uppercase_mockery
        ],
        [
            get_chance_of_thanks(),
            actions.message.send_thanks
        ],
        [
            get_chance_of_sticker(),
            actions.message.send_sticker
        ]
    ]

    chances = []
    for event in events:
        chances.append( event[0] )
    
    choice = random.choices( events, weights = chances )
    choice = choice[0]

    is_action_succeeded = choice[1]( data )

    if( not is_action_succeeded ):
        #TODO: Fallback in case action is not succeeded
        pass


def get_chance_of_random_conjoined_messages():
    return 0.0


def get_chance_of_random_message_with_similar_word():
    return 0.0


def get_chance_of_similar_message():
    return 0.0


def get_chance_of_response_message():
    return 0.0


def get_chance_of_poll():
    return 1.0


def get_chance_of_meme():
    return 0.0


def get_chance_of_meme_with_similar_message():
    return 0.0


def get_chance_of_photo_distortion():
    return 0.0


def get_chance_of_hokku():
    return 0.0


def get_chance_of_consonant_removal():
    return 0.0


def get_chance_of_uppercase_mockery():
    return 0.0


def get_chance_of_thanks():
    return 0.0


def get_chance_of_sticker():
    return 0.0

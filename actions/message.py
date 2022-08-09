import sql

import actions
from actions import vk

import re

class Message:
    def __init__( self, text ):
        self.original_text = text
        self.cleared_text = self.get_clean_text( self.original_text )
        self.no_punctuation_text = self.get_no_punctuation_text( self.cleared_text )

        self.words = self.cleared_text.split()
        self.words_no_punctuation = self.no_punctuation_text.split()

        self.word_count = len( self.words )

    def get_clean_text( self, text ):
        cleaned_text = re.sub(
            r'''
                (?:@\w{2,})(?:\*\w{2,}(?=\s))?|
                (?:\[.+?\|.+?\])
            '''
            , ''
            , text
            , flags = re.M | re.I | re.X
        )
        
        # Collapsing unwanted whitespace
        cleaned_text = re.sub( ' +', ' ', cleaned_text )
        cleaned_text = cleaned_text.strip()

        return cleaned_text

    def get_no_punctuation_text( self, text ):
        no_punctuation_text = re.sub(
            r'''
                [^\s\w\-\/]
            '''
            , ''
            , text
            , flags = re.M | re.I | re.X
        )

        return no_punctuation_text


def send_random_conjoined_messages( data ):
    random_text_1 = sql.get_random_text( data )
    random_message_1 = Message( random_text_1 )
    last_word = random_message_1.words_no_punctuation[-1]
    random_text_2 = sql.get_random_text( data, begins_with = last_word )
    if( random_text_2 ):
        # Removing the last word
        random_conjoined_text = ' '.join( random_message_1.words[:-1] )
        random_conjoined_text += ' ' + random_text_2
        random_message = Message( random_conjoined_text )
        if( random_message.cleared_text ):
            actions.vk.send_message( data['peer_id'], random_message.cleared_text )
            return True
    return False


def send_random_message_with_similar_word( data ):
    message = Message( data['text'] )
    last_word = message.words_no_punctuation[-1]
    random_text = sql.get_random_text( data, begins_with = last_word )
    if( random_text ):
        random_message = Message( random_text )
        if( random_message.cleared_text ):
            actions.vk.send_message( data['peer_id'], random_message.cleared_text )
            return True
    return False


def send_similar_message( data ):
    message = Message( data['text'] )
    if( message.word_count <= 5 ):
        similar_text = sql.get_random_similar_text( data, message.original_text )
        if( similar_text ):
            similar_message = Message( similar_text )
            if( similar_message.cleared_text ):
                actions.vk.send_message( data['peer_id'], similar_message.cleared_text )
                return True
    return False


def send_response_message( data ):
    contains = [
        'he',
        'her',
        'hers',
        'his',
        'she',
        'their',
        'theirs',
        'they',
        'u',
        'you',
        'yours',
        'вам',
        'вами',
        'вас',
        'вы',
        'ее'
        'ей',
        'её',
        'ими',
        'меня',
        'мне',
        'мной',
        'мною',
        'нами',
        'нас',
        'него',
        'нее',
        'ней',
        'нем',
        'неё',
        'нём',
        'твое',
        'твой',
        'твоё',
        'тебе',
        'тебя',
        'тобой',
        'тобою',
        'ты',
        'я',
    ]
    random_text = sql.get_random_response( data, contains )
    if( random_text ):
        random_message = Message( random_text )
        if( random_message.cleared_text ):
            actions.vk.send_message( data['peer_id'], random_message.cleared_text )
            return True
    return False


def send_poll( data ):
    random_answers =  sql.get_random_poll_answers( data )
    random_question = sql.get_random_text( data, is_question = True, max_length = 80 )
    if ( random_answers and random_question ):
        random_question_message = Message( random_question )
        if( random_question_message.cleared_text ):
            actions.vk.send_poll( data['peer_id'], random_question_message.cleared_text, random_answers, 457254241 )
    return False


def send_random_meme( data ):
    pass


def send_random_meme_with_similar_message( data ):
    pass


def send_photo_distortion( data ):
    pass


def send_hokku( data ):
    pass


def send_consonant_removal( data ):
    pass


def send_uppercase_mockery( data ):
    pass


def send_owo( data ):
    pass


def send_thanks( data ):
    pass


def send_sticker( data ):
    pass
import json
import sql

import random
import vk_api


vk_group_session = vk_api.VkApi( token = sql.get_setting( 'VK_API_TOKEN' ) )
vk_user_session = vk_api.VkApi( token = sql.get_setting( 'VK_ACCESS_TOKEN' ) )

vk_group = vk_group_session.get_api()
vk_user = vk_user_session.get_api()


def get_randint():
    return random.randint( 0, 100000 )


def get_clean_and_complete_data( data ):
    data = data['object']['message']

    if( 'is_cropped' in data ):
        # VK sometimes crops away attachments from Callback API events so let's specifically get the complete message info
        complete_data = vk.messages.getByConversationMessageId(
            peer_id = data['peer_id'],
            conversation_message_ids = data['conversation_message_id'],
            extended = True
        )

        data['attachments'] = complete_data['items'][0]['attachments']

    return data


def detect_photos_presence( data ):
    are_photos_present = False

    if( data['attachments'] ):
        for attachment in data['attachments']:
            if( attachment['type'] == 'photo' ):
                are_photos_present = True

    return are_photos_present


def detect_responses_presence( data ):
    are_responses_present = False

    if( data['fwd_messages'] or 'reply_message' in data ):
        are_responses_present = True

    return are_responses_present


def send_message( _peer_id, _message ):
    vk_group.messages.send(
        peer_id = _peer_id,
        message = _message,
        random_id = get_randint()
    )

    return True


def send_poll( _peer_id, _question, _add_answers, _photo_id ):
    _add_answers = json.dumps( _add_answers )

    poll = vk_user.polls.create(
        question = _question,
        add_answers = _add_answers,
        photo_id = _photo_id
    )

    poll = 'poll' + str( poll['owner_id'] ) + '_' + poll['embed_hash']

    vk_group.messages.send(
        peer_id = _peer_id,
        random_id = get_randint(),
        attachment = poll
    )

    return True



def send_sticker( _peer_id, _sticker_id ):
    vk_group.messages.send(
        peer_id = _peer_id,
        sticker_id = _sticker_id,
        random_id = get_randint()
    )
    
    return True
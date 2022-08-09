import sql

import actions
from actions import vk, general, decision

import flask
from flask import Flask, request
app = Flask('tomato')

import inspect


# |||| #
# INIT #
# |||| #

sql.init_db()

print( 'Starting Tomatobot ' + sql.get_setting( 'VERSION' ) )

sql.set_setting( 'STARTUP_TIME', actions.general.get_unix_time() )

# ||||||||| #
# FUNCTIONS #
# ||||||||| #

def get_message_parts( data ):
    commands_message = '''
        ❗ Команды
        t i — (I)нформация <t i k — только команды, t i s — только статус>
        t s — (S)пать 30 минут <t sleep, t shut, t stfu>
        t w ­— (W)ake апнуться <t wake, t unshut, t unstfu>

        t d * — (D)елиться контентом с другими чатами (разрешить или запретить) <t d t — (T)екст, t d k — (K)артинки, t d o — (O)просы>
        t p * — (P)олучать контент от других чатов (разрешить или запретить) <t d t — (T)екст, t d k — (K)артинки, t d o — (O)просы>
        
        t m ­— (M)эсседж <t m L — длинный мэсседж>
        t k — (K)артинка
        t o — (O)прос
        t j — (J)морбнуть картинку
        t t — (T)aро <t t 999 — можно указать кол-во карт, максимум 10>
    '''

    status_message = '''
        ❓ Статус
        Сохранено сообщений
        • {messages_count}
        
        Сохранено картинок
        • {photos_count}
            
        Делиться текстом с другими чатами
        • {text_sharing}
        
        Принимать текст от других чатов
        • {text_recieving}
            
        Делиться картинками с другими чатами
        • {photos_sharing}
        
        Принимать картинки от других чатов
        • {photos_recieving}

        Делиться опросами с другими чатами
        • {poll_sharing}
        
        Принимать опросы от других чатов
        • {poll_recieving}
    '''.format(
            messages_count = sql.get_messages_count( data ),
            photos_count = sql.get_photos_count( data ),
            
            text_sharing = 'Разрешено ⚠️' if sql.get_chat_setting( data, 'is_sharing_text' ) else 'Запрещено',
            text_recieving = 'Разрешено ⚠️' if sql.get_chat_setting( data, 'is_recieving_text' ) else 'Запрещено',
            
            photos_sharing = 'Разрешено ⚠️' if sql.get_chat_setting( data, 'is_sharing_photos' ) else 'Запрещено',
            photos_recieving = 'Разрешено ⚠️' if sql.get_chat_setting( data, 'is_recieving_photos' ) else 'Запрещено',

            poll_sharing = 'Разрешено ⚠️' if sql.get_chat_setting( data, 'is_sharing_poll_answers' ) else 'Запрещено',
            poll_recieving = 'Разрешено ⚠️' if sql.get_chat_setting( data, 'is_recieving_poll_answers' ) else 'Запрещено'
        )

    return ( commands_message, status_message )


def switch_sharing_recieving_setting( data, setting, string ):
    message = ''

    new_setting = not sql.get_chat_setting( data, setting )

    sql.set_chat_setting( data, setting, new_setting )
    
    if( new_setting == True ):
        message = '''
            ⚠️ Теперь я буду {}. 
        '''.format( string )
    else:
        message = '''
            Теперь я больше НЕ буду {}.
        '''.format( string )

    return message


def advance_time( data ):
    time_of_last_message = int( sql.get_chat_setting( data, 'time_of_last_message' ) )
    time_of_current_message = actions.general.get_unix_time()
    time_delta = time_of_current_message - time_of_last_message

    time_of_pause_left = sql.get_chat_setting( data, 'time_of_pause_left' )
    time_of_pause_left = time_of_pause_left - time_delta
    time_of_pause_left = max( 0, time_of_pause_left )

    sql.set_chat_setting( data, 'time_of_pause_left', time_of_pause_left )
    sql.set_chat_setting( data, 'time_of_last_message', time_of_current_message )

    time_delta = actions.general.sigmoid( time_delta, 0, 30 ) / 30
    time_delta = round( time_delta, 2 )

    sql.set_chat_setting( data, 'chance_multiplier', time_delta )


# |||||||||||||||||||||||| #
# VK CALLBACK API ENDPOINT #
# |||||||||||||||||||||||| #

@app.route ( '/', methods = ['POST'] )
def endpoint():
    if request.method == 'POST':
        data = request.get_json( silent = True )
        
        if(
            data['secret'] != sql.get_setting('VK_SECRET') or
            data is None
        ):
            return 'Scram!', 406

        # VK CALLBACK API CONFIRMATION
        # type: confirmation
        if(
            data['type'] == 'confirmation' and 
            str( data['group_id'] ) == sql.get_setting( 'VK_CONFIRMATION_GROUP_ID' )
        ):
            return sql.get_setting( 'VK_CONFIRMATION_CODE' ), 200
        
        # A NEW MESSAGE IS SENT
        # type: message_new
        if(
            data['type'] == 'message_new'
        ):
            data = actions.vk.get_clean_and_complete_data( data )
            
            is_blocklisted = sql.get_chat_setting( data, 'is_blocklisted' )
            
            sql.init_chat_settings( data )

            #if( is_blocklisted is None ):
            #    sql.init_chat_settings( data )
                
            if( not is_blocklisted ):
                is_event_fresh = False 
                if( data['date'] > int( sql.get_setting( 'STARTUP_TIME' ) ) ):
                    is_event_fresh = True

                is_command_handled = False
                if( is_event_fresh ):
                    is_command_handled = handle_command( data )

                if( not is_command_handled ):
                    save_content( data )
                    if( is_event_fresh ):
                        advance_time( data )
                        actions.decision.make_a_decision( data )
            elif( is_blocklisted ):
                print( 'Chat ' + str( data['peer_id'] ) + ' is blocklisted. Ignoring.' )
            
        return 'ok', 200


def save_content( data ):
    are_photos_present = actions.vk.detect_photos_presence( data )
    are_responses_present = actions.vk.detect_responses_presence( data )

    if( are_photos_present or are_responses_present ):
        parent_message_id = sql.save_message( data )
        sql.save_photos( data, parent_message_id )
        sql.save_responses( data, parent_message_id )
    elif( data['text'] ):
        sql.save_message( data, are_non_unique_refused = True )

    sql.save_poll_answers( data )


def handle_command( data ):
    text = data['text']

    text = text.lower()
    text = text.split()
    text = ''.join( text )

    match text:
        case 'ti':
            commands_message, status_message = get_message_parts( data ) 

            message = '''
                🍅 Томатобот версии {version}

                {commands}
                {status}
            '''.format(
                    version = sql.get_setting( 'VERSION' ),
                    commands = commands_message,
                    status = status_message
                )

            message = inspect.cleandoc( message )

            return actions.vk.send_message( data['peer_id'], message )
        case 'tik':
            commands_message, status_message = get_message_parts( data ) 

            message = '''
                🍅 Томатобот версии {version}

                {commands}
            '''.format(
                    version = sql.get_setting( 'VERSION' ),
                    commands = commands_message
                )

            message = inspect.cleandoc( message )
        
            return actions.vk.send_message( data['peer_id'], message )
        case 'tis':
            commands_message, status_message = get_message_parts( data ) 

            message = '''
                🍅 Томатобот версии {version}

                {status}
            '''.format(
                    version = sql.get_setting( 'VERSION' ),
                    status = status_message
                )

            message = inspect.cleandoc( message )

            return actions.vk.send_message( data['peer_id'], message )
        case 'ts' | 'tsleep' | 'tshut' | 'tstfu':
            sql.set_chat_setting( data, 'time_of_pause_left', 1800 )
            message = 'soory'
            return actions.vk.send_message( data['peer_id'], message )
        case 'tsilencethot':
            sql.set_chat_setting( data, 'time_of_pause_left', 1800 )
            message = '* starts twerking *'
            return actions.vk.send_message( data['peer_id'], message )
        case 'tw' | 'twake' | 'tunshut' | 'tunstfu':
            sql.set_chat_setting( data, 'time_of_pause_left', 0 )
            message = 'owO'
            return actions.vk.send_message( data['peer_id'], message )
        case 'tdt':
            message = switch_sharing_recieving_setting( data, 'is_sharing_text', 'делиться текстом из этого чата с другими чатами' )
            return actions.vk.send_message( data['peer_id'], message )
        case 'tdk':
            message = switch_sharing_recieving_setting( data, 'is_sharing_photos', 'делиться картинками из этого чата с другими чатами' )
            return actions.vk.send_message( data['peer_id'], message )
        case 'tdo':
            message = switch_sharing_recieving_setting( data, 'is_sharing_poll_answers', 'делиться опросами из этого чата с другими чатами' )
            return actions.vk.send_message( data['peer_id'], message )
        case 'tpt':
            message = switch_sharing_recieving_setting( data, 'is_recieving_text', 'получать текст из других чатов' )
            return actions.vk.send_message( data['peer_id'], message )
        case 'tpk':
            message = switch_sharing_recieving_setting( data, 'is_recieving_photos', 'получать картинки из других чатов' )
            return actions.vk.send_message( data['peer_id'], message )
        case 'tpo':
            message = switch_sharing_recieving_setting( data, 'is_recieving_poll_answers', 'получать опросы из других чатов' )
            return actions.vk.send_message( data['peer_id'], message )
        case 'ty':
            return actions.vk.send_message( data['peer_id'], 'y w' )
        case 'tf':
            return actions.vk.send_sticker( data['peer_id'], 5419 )
        case 'tpat':
            return actions.vk.send_sticker( data['peer_id'], 5444 )
        case 'tsmack':
            return actions.vk.send_message( data['peer_id'], 'SMACK MY ASS LIKE A DRUM 😩' )

        case 'tq'|'te'|'tr'|'tu'| \
             'tp'|'ta'|'td'|'tz'| \
             'tg'|'th'|'tl'|'tb'| \
             'tx'|'tc'|'tv'|'tm'| \
             'tn':
            # Reserved combinations
            return True
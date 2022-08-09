import json
import pathlib
import random
import random
import sqlite3
import traceback

import actions
from actions import general


# |||||||||||||||||||||||||||||| #
# VARIABLES AND DEFAULT SETTINGS #
# |||||||||||||||||||||||||||||| #

DATABASE_LOCATION = 'data.db'

DEFAULT_SETTINGS = {
    'VERSION' : '3.0',
    'STARTUP_TIME': 0,
    
    # CONFIDENTIAL
    'VK_CONFIRMATION_CODE' : 'abc',
    'VK_CONFIRMATION_GROUP_ID' : 199416984,
    'VK_API_TOKEN' : '78d01e8af922cfcd9951661fa27594f3bcd60ddb1081af7a75568b101d9462dc03f5794944f95945c676d',
    'VK_ACCESS_TOKEN' : 'vk1.a.HHKYwTciaIXQ8CdEA4HFEsQ3lfD6NKULFlOmCdqI5MUZeNeVOMTDU__XeQwAkT9xUQ5SzpOLKCd9VBGGRaM0g8j64-2KECKULlCLJmadZTQwwbZpiuDghs5No4Zh3yRL4ma9LbxtBSkVS0zrCqQZr4tJgftuX8gxBfWylEyaptL5Nj6J6Tq0Dij6iK7bsXKQ',
    'VK_SECRET': 'epicPIPIS',

    'CHANCE_OF_USING_SHARED_CONTENT': 0.5,

    'CHANCE_OF_RANDOM_CONJOINED_MESSAGES': 0,
    'CHANCE_OF_RANDOM_MESSAGE_WITH_SIMILAR_WORD': 0,
    'CHANCE_OF_SIMILAR_MESSAGE': 0,
    'CHANCE_OF_RESPONSE_MESSAGE': 0,
    'CHANCE_OF_POLL': 0,
    'CHANCE_OF_MEME': 0,
    'CHANCE_OF_MEME_WITH_SIMILAR_MESSAGE': 0,
    'CHANCE_OF_PHOTO_DISTORTION': 0,
    'CHANCE_OF_HOKKU': 0,
    'CHANCE_OF_CONSONANT_REMOVAL': 0,
    'CHANCE_OF_UPPERCASE_MOCKERY': 0,
    'CHANCE_OF_OWO': 0,
    'CHANCE_OF_THANKS': 0,
    'CHANCE_OF_STICKER': 0
}

# ||||||||| #
# FUNCTIONS #
# ||||||||| #

def sql_connect():
    sql_connection = sqlite3.connect( DATABASE_LOCATION )
    sql_cursor = sql_connection.cursor()

    return ( sql_connection, sql_cursor )


def init_db():
    sql_connection, sql_cursor = sql_connect()
    
    sql_cursor.executescript(
        '''
            CREATE TABLE IF NOT EXISTS
                Settings (
                    id      INTEGER PRIMARY KEY,
                    setting TEXT    NOT NULL,
                    value   TEXT    NOT NULL,
                    
                    UNIQUE( setting )
                );
           
            CREATE TABLE IF NOT EXISTS
                ChatSettings (
                    id      INTEGER PRIMARY KEY,
                    peer_id INTEGER NOT NULL,
                    json    TEXT    NOT NULL,
                    
                    UNIQUE( peer_id )
                ); 
                
            CREATE TABLE IF NOT EXISTS
                Messages (
                    id                      INTEGER PRIMARY KEY,
                    text                    TEXT    NOT NULL,
                    date                    INTEGER NOT NULL,
                    conversation_message_id INTEGER NOT NULL,
                    from_id                 INTEGER NOT NULL,
                    peer_id                 TEXT    NOT NULL,
                    
                    is_personal             INTEGER NOT NULL
                );
            
            CREATE TABLE IF NOT EXISTS
                Responses (
                    id                      INTEGER PRIMARY KEY,
                    text                    TEXT    NOT NULL,
                    date                    INTEGER NOT NULL,
                    conversation_message_id INTEGER NOT NULL,
                    from_id                 INTEGER NOT NULL,

                    parent_message_id       INTEGER,

                    FOREIGN KEY( parent_message_id ) REFERENCES Messages( id )
                );

            CREATE TABLE IF NOT EXISTS
                PollAnswers (
                    id      INTEGER PRIMARY KEY,
                    text    TEXT    NOT NULL,
                    peer_id INTEGER NOR NULL,

                    UNIQUE( text )
                );

            CREATE TABLE IF NOT EXISTS
                Photos (
                    id                INTEGER PRIMARY KEY,
                    photo_id          INTEGER NOT NULL,
                    url               TEXT    NOT NULL,
                    
                    parent_message_id INTEGER,
                    
                    FOREIGN KEY( parent_message_id ) REFERENCES Messages( id )
                );
        '''
    )
    
    # Inserting default settings
    for setting, value in DEFAULT_SETTINGS.items():
        sql_cursor.execute(
            '''
                INSERT OR IGNORE INTO
                    Settings( setting, value )
                VALUES( ?, ? )
            '''
            , (
                setting, value
            )
        )
    
    # Removing non-existent settings
    sql_cursor.execute(
        '''
            SELECT
                setting
            FROM
                Settings
        '''
    )

    settings = sql_cursor.fetchall()

    for setting in settings:
        setting = setting[0]
        if( setting not in DEFAULT_SETTINGS ):
            sql_cursor.execute(
                '''
                    DELETE FROM
                        Settings
                    WHERE
                        setting = ?
                '''
                , (
                    setting,
                )
            )

    sql_connection.commit()
    sql_connection.close()


def save_message( data, are_non_unique_refused = False ):
    # To be returned in the end
    lastrowid = False

    # Unlinking the passed reference so that we can modify data freely
    data = data.copy()

    sql_connection, sql_cursor = sql_connect()

    try:
        sql_cursor.execute(
            '''
                SELECT
                    COUNT( * )
                FROM
                    Messages
                WHERE( text = ? AND peer_id = ? )
            '''
            , (
                data['text'],
                data['peer_id']
            )
        )
        
        if( sql_cursor.fetchone()[0] != 0 ):
            if( are_non_unique_refused ):
                raise Exception( 'Message is not unique and also no attachments were provided. Ignoring.' )
        
            # Removing non-uniqie texts
            data['text'] = ''
            
        sql_cursor.execute(
            '''
                INSERT INTO
                    Messages(
                        text,
                        date,
                        conversation_message_id,
                        from_id,
                        peer_id,
                        is_personal
                    )
                VALUES( ?, ?, ?, ?, ?, ? )
            '''
            , (
                data['text'],
                data['date'],
                data['conversation_message_id'],
                data['from_id'],
                data['peer_id'],
                True if data['id'] > 0 else False # If message has an ID, it is sent to Tomatobot personally
            )
        )
                       
        sql_connection.commit()
        
        lastrowid = sql_cursor.lastrowid
        
    except Exception as error:
        print( traceback.format_exc() )

    sql_connection.close()

    return lastrowid  


def get_random_text( data, begins_with = '', is_question = False, max_length = False ):
    # To be returned in the end
    result = False

    sql_connection, sql_cursor = sql_connect()
    
    sql_connection.create_function("LOWER", 1, sqlite_lower)

    try:
        # Here we choose where to get random messages from
        peer_ids = [ data['peer_id'] ]
        if(
            get_chat_setting( data, 'is_recieving_text' ) and
            random.random() >= float( get_setting( 'CHANCE_OF_USING_SHARED_CONTENT' ) )
        ):
            # If recieving text, let's grab messages from other chats (with a chance)
            peer_ids = get_chats_which_share_data( 'is_sharing_text', exception = data['peer_id'] )

        question_condition = ''
        max_length_condition = ''
        if( is_question ):
            question_condition = 'AND ( text LIKE \'%?\' )'
        if( max_length ):
            length_condition = 'AND ( LENGTH( text ) <= ' + str( max_length ) + ' )'

        sql_cursor.execute(
            '''
                SELECT
                    text
                FROM
                    Messages
                WHERE
                    peer_id IN ({}) AND
                    ( LOWER( text ) LIKE LOWER( ? ) )
                    {}
                    {}
                ORDER BY
                    RANDOM()
                LIMIT
                    1
            '''.format(
                ', '.join( '?' * len( peer_ids ) ),
                question_condition,
                max_length_condition
            )
            , (
                *peer_ids,
                begins_with + '%',
            )
        )
        
        sql_connection.commit()

        result = sql_cursor.fetchone()[0]

    except Exception as error:
        print( traceback.format_exc() )
    
    sql_connection.close()

    return result


def save_photos( data, parent_message_id ):
    sql_connection, sql_cursor = sql_connect()
    
    try:
        if( data['attachments'] ):
            for attachment in data['attachments']:
                if( attachment['type'] != 'photo' ):
                    continue

                sql_cursor.execute(
                            '''
                                INSERT INTO
                                    Photos( photo_id, url, parent_message_id )
                                VALUES( ?, ?, ? )
                            '''
                            , (
                                attachment['photo']['id'],
                                attachment['photo']['sizes'][-1]['url'],
                                parent_message_id,
                            )
                        )

                sql_connection.commit()
        
    except Exception as error:
        print( traceback.format_exc() )
        
    sql_connection.close()
    

def get_random_photo():
    sql_connection, sql_cursor = sql_connect()
    
    
    sql_connection.close()


def set_setting( setting, value ):
    sql_connection, sql_cursor = sql_connect()
    
    try:
        sql_cursor.execute(
            '''
                INSERT OR REPLACE INTO
                    Settings( setting, value )
                VALUES( ?, ? )
            '''
            , (
                setting,
                value
            )
        )

        sql_connection.commit()
        
    except Exception as error:
        print( traceback.format_exc() )

    sql_connection.close()


def get_setting( setting ):
    # To be returned in the end
    result = False

    sql_connection, sql_cursor = sql_connect()
    
    try:
        sql_cursor.execute(
            '''
                SELECT
                    value
                FROM
                    Settings
                WHERE
                    setting = ?
            '''
            , (
                setting,
            )
        )

        sql_connection.commit()
        
        result = sql_cursor.fetchone()[0]
        
    except Exception as error:
        print( traceback.format_exc() )

    sql_connection.close()
    
    return result
    

def init_chat_settings( data ):
    sql_connection, sql_cursor = sql_connect()
    
    json_init = json.dumps(
        {
            'is_blocklisted' : False,
            
            'is_sharing_text': False,
            'is_recieving_text': False,
            'is_sharing_photos': False,
            'is_recieving_photos': False,
            'is_sharing_poll_answers': False,
            'is_recieving_poll_answers': True,
            
            'time_of_last_message': actions.general.get_unix_time(),
            'time_of_pause_left': 0,
            'chance_multiplier': 1
        }
    )

    # To be used later
    init_settings = json.loads( json_init )
    
    try:
        sql_cursor.execute(
            '''
                INSERT OR IGNORE INTO
                    ChatSettings( peer_id, json )
                VALUES( ?, ? )
            '''
            , (
                data['peer_id'],
                json_init
            )
        )

        # Updating with new settings
        sql_cursor.execute(
            '''
                SELECT
                    json
                FROM
                    ChatSettings
                WHERE
                    peer_id = ?
            '''
            , (
                data['peer_id'],
            )
        )

        settings = sql_cursor.fetchone()[0]
        settings = json.loads( settings )

        are_there_non_existent_settings = False

        for init_setting, value in init_settings.items():
            if( init_setting not in settings ):
                settings[init_setting] = value
                are_there_non_existent_settings = True
        settings = json.dumps( settings )

        if( are_there_non_existent_settings ):
            sql_cursor.execute(
                '''
                    UPDATE
                        ChatSettings
                    SET
                        json = ?
                    WHERE
                        peer_id = ?
                '''
                , (
                    settings,
                    data['peer_id']
                )
            )

        # Removing non-existent settings
        sql_cursor.execute(
            '''
                SELECT
                    json
                FROM
                    ChatSettings
                WHERE
                    peer_id = ?
            '''
            , (
                data['peer_id'],
            )
        )

        are_there_redundant_settings = False

        settings = sql_cursor.fetchone()[0]
        settings = json.loads( settings )

        for setting in list( settings ):
            if( setting not in init_settings ):
                del settings[setting]
                are_there_redundant_settings = True
                
        settings = json.dumps( settings )

        if( are_there_redundant_settings ):
            sql_cursor.execute(
                '''
                    UPDATE
                        ChatSettings
                    SET
                        json = ?
                    WHERE
                        peer_id = ?
                '''
                , (
                    settings,
                    data['peer_id']
                )
            )

        sql_connection.commit()
        
    except Exception as error:
        print( traceback.format_exc() )
    
    sql_connection.close()
    
    
def set_chat_setting( data, setting, value ):
    sql_connection, sql_cursor = sql_connect()
    
    try:
        sql_cursor.execute(
            '''
                SELECT
                    json
                FROM
                    ChatSettings
                WHERE
                    peer_id = ?
            '''
            , (
                data['peer_id'],
            )
        )
        
        result = sql_cursor.fetchone()[0]
        result = json.loads( result )
        result[setting] = value
        result = json.dumps( result )

        sql_cursor.execute(
            '''
                UPDATE
                    ChatSettings
                SET
                    json = ?
                WHERE
                    peer_id = ?
            '''
            , (
                result,
                data['peer_id'] 
            )
        )
        
        sql_connection.commit()
        
    except Exception as error:
        print( traceback.format_exc() )
    
    sql_connection.close()


def get_chat_setting( data, setting ):
    # To be returned in the end
    result = False
    
    sql_connection, sql_cursor = sql_connect()
    
    try:
        sql_cursor.execute(
            '''
                SELECT
                    json
                FROM
                    ChatSettings
                WHERE
                    peer_id = ?
            '''
            , (
                data['peer_id'],
            )
        )

        sql_connection.commit()
        
        result = sql_cursor.fetchone()
        
        if( result is not None ):
            result = result[0]
            result = json.loads( result )
            result = result[setting]
        
    except Exception as error:
        print( traceback.format_exc() )
    
    sql_connection.close()
    
    return result


def save_responses( data, parent_message_id ):
    sql_connection, sql_cursor = sql_connect()
    
    try:
        if( data['fwd_messages'] ):
            for response in data['fwd_messages']:
                sql_cursor.execute(
                    '''
                        INSERT INTO
                            Responses(
                                text,
                                date,
                                conversation_message_id,
                                from_id,
                                parent_message_id
                            )
                        VALUES( ?, ?, ?, ?, ? )
                    '''
                    , (
                        response['text'],
                        response['date'],
                        response['conversation_message_id'],
                        response['from_id'],
                        parent_message_id
                    )
                )
        
        if( 'reply_message' in data ):
            response = data['reply_message']

            sql_cursor.execute(
                '''
                    INSERT INTO
                        Responses(
                            text,
                            date,
                            conversation_message_id,
                            from_id,
                            parent_message_id
                        )
                    VALUES( ?, ?, ?, ?, ? )
                '''
                , (
                    response['text'],
                    response['date'],
                    response['conversation_message_id'],
                    response['from_id'],
                    parent_message_id
                )
            )
                    
        sql_connection.commit()
        
    except Exception as error:
        print( traceback.format_exc() )
    
    sql_connection.close()


def get_random_response( data, contains = ['я']):
    # To be returned in the end
    result = False

    sql_connection, sql_cursor = sql_connect()

    sql_connection.create_function("LOWER", 1, sqlite_lower)

    try:
        # Formatting for the SQL LIKE
        for i, word in enumerate( contains ):
            contains[i] = '%' + word + '%'

        sql_cursor.execute(
            '''
                SELECT
                    Messages.text
                FROM
                    Messages,
                    Responses
                WHERE
                    Responses.from_id = ? AND
                    Messages.id = Responses.parent_message_id AND
                    Messages.peer_id = ?
                    {}
                ORDER BY
                    RANDOM()
                LIMIT
                    1
            '''.format( 'AND ( ' + ' or '.join( 'LOWER( Messages.text ) LIKE ?' for _ in contains ) + ' )')
            , (
                data['from_id'],
                data['peer_id'],
                *contains
            )
        )

        sql_connection.commit()
        
        result = sql_cursor.fetchone()[0]

    except Exception as error:
        print( traceback.format_exc() )
    
    sql_connection.close()

    return result


def save_poll_answers( data ):
    sql_connection, sql_cursor = sql_connect()
    
    try:
        if( data['attachments'] ):
            for attachment in data['attachments']:
                if( attachment['type'] == 'poll' ):
                    for answer in attachment['poll']['answers']:
                        sql_cursor.execute(
                            '''
                                INSERT INTO
                                    PollAnswers( text, peer_id )
                                VALUES( ?, ? )
                            '''
                            , (
                                answer['text'],
                                data['peer_id']
                            )
                        )
                    
                    sql_connection.commit()
        
    except Exception as error:
        print( traceback.format_exc() )
    
    sql_connection.close()


def get_random_poll_answers( data ):
    # To be returned in the end
    result = []

    sql_connection, sql_cursor = sql_connect()

    try:
        # Here we choose where to get random messages from
        peer_ids = [ data['peer_id'] ]
        if(
            get_chat_setting( data, 'is_recieving_poll_answers' ) and
            random.random() >= float( get_setting( 'CHANCE_OF_USING_SHARED_CONTENT' ) )
        ):
            # If recieving data, let's grab messages from other chats (with a chance)
            peer_ids = get_chats_which_share_data( 'is_sharing_poll_answers', exception = data['peer_id'] )

        sql_cursor.execute(
            '''
                SELECT
                    text
                FROM
                    PollAnswers
                WHERE
                    peer_id IN ({})
                ORDER BY
                    RANDOM()
                LIMIT
                    6
            '''.format( ', '.join( '?' * len( peer_ids ) ) )
            , (
                *peer_ids,
            )
        )

        sql_connection.commit()

        result = sql_cursor.fetchall()
        for i, text in enumerate( result ):
            # Unpacking unwanted tuples
            result[i] = text[0]
        
    except Exception as error:
        print( traceback.format_exc() )
    
    sql_connection.close()
    
    return result
    

def get_random_similar_text( data, text ):
    # To be returned in the end
    result = []

    sql_connection, sql_cursor = sql_connect()
    
    sql_connection.enable_load_extension( True )
    path = str( pathlib.Path('./assets/distlib.so').resolve() )
    sql_connection.load_extension( path )

    try:
        # Here we choose where to get random messages from
        peer_ids = [ data['peer_id'] ]
        if(
            get_chat_setting( data, 'is_recieving_text' ) and
            random.random() >= float( get_setting( 'CHANCE_OF_USING_SHARED_CONTENT' ) )
        ):
            # If recieving data, let's grab messages from other chats (with a chance)
            peer_ids = get_chats_which_share_text( exception = data['peer_id'] )

        sql_cursor.execute(
            '''
                SELECT
                    text,
                    jwsim( text, ? ) AS similarity
                FROM
                    Messages
                WHERE
                    peer_id IN ({}) AND
                    similarity > 0.7 AND
                    similarity != 1.0
                ORDER BY
                    similarity DESC
                LIMIT
                    4
            '''.format( ', '.join( '?' * len( peer_ids ) ) )
            , (
                text,
                *peer_ids
            )
        )

        sql_connection.commit()

        result = sql_cursor.fetchall()
        if( result ):
            random.shuffle( result )
            result = result[0][0]

        
    except Exception as error:
        print( traceback.format_exc() )
    
    sql_connection.close()

    return result

    
# ||||||||||||||||||||||| #
# MISCELLANEOUS FUNCTIONS #
# ||||||||||||||||||||||| #

def get_messages_count( data ):
    # To be returned in the end
    result = 0
    
    sql_connection, sql_cursor = sql_connect()
    
    try:
        sql_cursor.execute(
            '''
                SELECT
                    COUNT(*)
                FROM
                    Messages
                WHERE(
                    peer_id = ? AND
                    text != ''
                );
            '''
            , (
                data['peer_id'],
            )
        )

        sql_connection.commit()
        
        result = sql_cursor.fetchone()[0]
        
    except Exception as error:
        print( traceback.format_exc() )
    
    sql_connection.close()
    
    return result
    
    
def get_photos_count( data ):
    # To be returned in the end
    result = 0
    
    sql_connection, sql_cursor = sql_connect()
    
    try:
        sql_cursor.execute(
            '''
                SELECT
                    COUNT( * )
                FROM
                    Messages,
                    Photos
                WHERE(
                    Messages.peer_id = ? AND
                    Messages.id = Photos.parent_message_id
                );
            '''
            , (
                data['peer_id'],
            )
        )

        sql_connection.commit()
        
        result = sql_cursor.fetchone()[0]
        
    except Exception as error:
        print( traceback.format_exc() )
    
    sql_connection.close()
    
    return result


def get_chats_which_share_data( which_data, exception ):
    # To be returned in the end
    result = False

    sql_connection, sql_cursor = sql_connect()

    which_data = '$.' + which_data

    try:
        sql_cursor.execute(
            '''
                SELECT
                    peer_id
                FROM
                    ChatSettings
                WHERE
                    JSON_EXTRACT( json, ? ) = 1
                    {}
            '''.format( 'AND peer_id !=' + str( exception ) if exception else '' )
            , (
                which_data,
            )
        )

        sql_connection.commit()
        
        result = sql_cursor.fetchall()
        for i, peer_id in enumerate( result ):
            # Unpacking unwanted tuples
            result[i] = peer_id[0]
        
    except Exception as error:
        print( traceback.format_exc() )
    
    sql_connection.close()
    
    return result


# Making SQLite sensitive to the UNICODE
def sqlite_lower( value ):
    return value.lower()
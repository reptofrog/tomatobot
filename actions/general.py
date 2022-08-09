import time


def sigmoid( x, min, max ):
    return min + ( max - min ) * ( lambda t: ( 1 + 200 ** ( -t + 0.5 ) ) ** ( -1 ) ) ( ( x - min ) / ( max - min ) )


def get_unix_time():
    return round( time.time() )
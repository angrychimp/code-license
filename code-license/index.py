"""
code-license.index

Serves a license template for a user
"""

import os.path
import json
import re
import logging
from License import License, LicenseError

DEFAULT_LOG_LEVEL = 'error'

logger = logging.getLogger()
levels = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'warn': logging.WARN,
    'error': logging.ERROR
}
level = levels[os.environ['LOG_LEVEL']] \
    if 'LOG_LEVEL' in os.environ and os.environ['LOG_LEVEL'] in levels \
    else levels[DEFAULT_LOG_LEVEL]
logger.setLevel(level)

def respond(statusCode=400, body=None, headers=None):
    if not headers:
        body = json.dumps(body)
        headers = {
            'Content-Type': 'application/json'
        }
    return {
        'statusCode': statusCode,
        'body': str(body),
        'headers': headers
    }

def handler(event={}, context={}): 
    
    logger.info("Event: %s", event)

    # Shortcut to a theme
    if re.match(r"^/themes/", event['path']):
        theme = event['path'].split('/')[-1]
        if os.path.isfile("themes/" + theme):
            content = open("themes/" + theme, 'r').read()
            return respond(200, content, {'Content-Type': 'text/css'})
        else:
            return respond(404, {"error": {"messageString": "Theme not found"}})

    parameters = event['pathParameters']['proxy'] if 'pathParameters' in event \
        and event['pathParameters'] and 'proxy' in event['pathParameters'] \
        else event['path']
    license = License(
        Host=event['headers']['Host'],
        Parameters=parameters
    )
    try:
        license.build()
        return respond(200, license, {'Content-Type': license.get_format()})
    except LicenseError as e:
        return respond(e.statusCode, {"error": {"messageString": e.message}})

if __name__ == "__main__":
    import sys
    # Read in JSON test doc from command line
    event = json.loads(open(sys.argv[1], 'r').read())
    print(handler(event))

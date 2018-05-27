"""
Class License

Based on supplied user data, returns branded license content
"""

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from boto3.dynamodb.types import TypeDeserializer
from hashlib import md5
from datetime import datetime
from collections import deque
import boto3
import re
import os
import errno
import logging
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEFAULT_LICENSE = os.environ['DEFAULT_LICENSE'] if 'DEFAULT_LICENSE' in os.environ else 'mit'
DEFAULT_HOST = os.environ['DEFAULT_HOST'] if 'DEFAULT_HOST' in os.environ else 'code-license.org'
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE'] if 'DYNAMODB_TABLE' in os.environ else False
GITHUB_URL = os.environ['GITHUB_BASE_URL'] if 'GITHUB_BASE_URL' in os.environ \
    else 'https://raw.githubusercontent.com/angrychimp/code-license/{hash}/code-license/templates/{license}.j2'

class LicenseError(Exception):
    def __init__(self, *args):
        self.statusCode, self.message = args
        super().__init__(self.message)

class License:

    ''' Member variables '''
    query_options = {}
    config = {}

    def __init__(self, **kwargs):
        # Define default configuration
        self.config = {
            'license': DEFAULT_LICENSE,
            'gravatar': False,
            'theme': 'default',
            'format': 'html',
            'copyright': '<copyright holders>',
            'version': 'latest',
            'year': datetime.now().strftime('%Y')
        }
        self.host = kwargs['Host']
        self.query = kwargs['Parameters']
    
    def parse_query(self):
        parts = deque(self.query.split('/'))
        logger.info(parts)
        options = {}
        val = True
        while val:
            try:
                val = parts.popleft()
                logger.info("Query option: '%s'", val)
            except:
                val = False
            if not val or len(val) == 0:
                continue
            
            if val == 'u':
                # Specify user
                # (allows for users with names that cannot go in the domain)
                self.username = parts.popleft()
                continue
            if re.match(r"license\.(txt|html)", val):
                options['format'] = val.split('.')[1]
                continue
            if re.match(r"(@)?([0-9]{4})(-([0-9]{4}))?", val):
                m = re.match(r"(@)?([0-9]{4})(-([0-9]{4}))?$", val)
                if m.group(1) == '@':
                    # Pin to single year
                    options['year'] = m.group(2)
                else:
                    options['year'] = m.group(0)
                continue
            if re.match(r"^([a-f0-9])+$", val):
                # commit hash to pin
                options['hash'] = val
                continue
            
        self.query_options = {**self.query_options, **options}
        
    def fetch_user_data(self):
        client = boto3.client('dynamodb')
        response = client.query(
            TableName=DYNAMODB_TABLE,
            KeyConditionExpression="#U = :username",
            ExpressionAttributeNames={"#U": "username"},
            ExpressionAttributeValues={":username": {"S": self.username}}
        )
        if len(response['Items']) == 0:
            # If user not found, just use username
            data = {"copyright": self.username}
        else:
            data = response['Items'][0]
            helper = TypeDeserializer()
            for k in data.keys():
                data[k] = helper.deserialize(data[k])

        if 'email' in data:
            data['email_md5'] = md5(data['email'].encode('utf-8')).hexdigest()

        logger.info("Merging configs: %s", {'default': self.config, 'dynamo': data, 'query': self.query_options})
        self.config = {**self.config, **data, **self.query_options}
    
    def to_text(self):
        from LicenseStripper import LicenseStripper
        s = LicenseStripper()
        s.feed(self.content)
        self.content = s.get_data()

    def _get_jinja_env(self):
        if 'hash' in self.config:
            logger.info('Fetching template "%s" at commit %s', self.config['license'], self.config['hash'])
            # Create local hash folder
            template_path = '/tmp/templates/' + self.config['hash']
            logger.info("Defined template path: " + template_path)
            try:
                os.makedirs(template_path)
            except OSError as e:
                if e.errno == errno.EEXIST and os.path.isdir(template_path):
                    pass
                else:
                    raise
            # Fetch license file from git
            local_file = "%s/%s.j2" % (template_path, self.config['license'])
            if not os.path.isfile(local_file):
                remote_file = GITHUB_URL.format(hash=self.config['hash'], license=self.config['license'])
                logger.info("Download %s to %s" % (remote_file, local_file))
                r = requests.get(remote_file, stream=True)
                with open(local_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        f.write(chunk)
                f.close()
        else:
            template_path = 'templates'

        env = Environment(
            loader=FileSystemLoader(template_path),
            autoescape=select_autoescape(['html', 'xml'])
        )
        return env

    def build(self):
        # Process host
        if self.host.find(DEFAULT_HOST) < 0:
            raise LicenseError(406, "Host not acceptable: " + self.host)
        parts = self.host.replace(DEFAULT_HOST, '').split('.')[0:-1]
        self.username = parts.pop()
        logger.info("Remaining domain parts: %s", parts)
        if len(parts) > 0:
            # For now, ignore anything other than the right-most part
            self.query_options['license'] = '.'.join(parts)
            logger.info('Using domain-specified license: %s', self.query_options['license'])
        
        self.parse_query()
        self.fetch_user_data()

        logger.info(self.config)

        env = self._get_jinja_env()
        try:
            template = env.get_template(self.config['license'].lower() + '.j2')
            self.content = template.render(self.config)
        except:
            raise LicenseError(503, "License template not found: " + self.config['license'])
        if 'format' in self.config and self.config['format'] == 'txt':
            self.to_text()
    
    def get_format(self):
        return 'text/plain' if self.config['format'] == 'txt' else 'text/html'

    def __str__(self):
        return self.content

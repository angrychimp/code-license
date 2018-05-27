"""
Extracts text license content from HTML template
(adapted from https://stackoverflow.com/questions/11061058/using-htmlparser-in-python-3-2)
"""

from html.parser import HTMLParser

class LicenseStripper(HTMLParser):

    # Override the parent's constructor
    def __init__(self):
        super().__init__()
        self.reset()
        self.in_article = False
        self.fed = []
    
    # Toggle compiling content
    def handle_starttag(self, tag, attrs):
        if tag == "article":
            self.in_article = not self.in_article
    def handle_endtag(self, tag):
        if tag == "article":
            self.in_article = not self.in_article

    # Add content to buffer
    def handle_data(self, d):
        if self.in_article:
            self.fed.append(d)

    # Dump buffer
    def get_data(self):
        return ''.join(self.fed)

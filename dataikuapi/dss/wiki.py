from .discussion import DSSObjectDiscussions
import json
import sys

if sys.version_info >= (3,0):
  import urllib.parse
  dku_quote_fn = urllib.parse.quote
else:
  import urllib
  dku_quote_fn = urllib.quote

class DSSWiki(object):
    """
    A handle to manage the wiki of a project

    :param client: an api client to connect to the DSS backend
    :param project_key: identifier of the project to access
    """
    def __init__(self, client, project_key):
        self.client = client
        self.project_key = project_key

    def get_settings(self):
        """
        Get wiki settings

        :returns: an handle to manage the wiki settings (taxonomy, home article)
        :rtype: DSSWikiSettings
        """
        return DSSWikiSettings(self.client, self.project_key, self.client._perform_json("GET", "/projects/%s/wiki/" % (self.project_key)))

    def get_article(self, article_id):
        """
        Get a wiki article

        :param str article_id: the article ID
        :returns: an handle to manage the Article
        :rtype: DSSWikiArticle
        """
        return DSSWikiArticle(self.client, self.project_key, article_id)

    def __flatten_taxonomy__(self, taxonomy):
        """
        Private recursive method to get the flatten list of article IDs from the taxonomy

        :param list taxonomy:
        :returns: list of articles
        :rtype: list
        """
        article_list = []
        for article in taxonomy:
            article_list.append(self.get_article(article['id']))
            article_list += self.__flatten_taxonomy__(article['children'])
        return article_list

    def list_articles(self):
        """
        Get a list of all the articles

        :returns: list of articles
        :rtype: list
        """
        return self.__flatten_taxonomy__(self.get_settings().get_taxonomy())

    def create_article(self, article_id, parent_id=None, content=None):
        """
        Create a wiki article

        :param str article_id: the article ID
        :param str parent_id: the parent article ID (or None if the article has to be at root level)
        :param str content: the article content
        :returns: the created article
        :rtype: DSSWikiArticle
        """
        body = {
            "projectKey": self.project_key,
            "id": article_id,
            "parent": parent_id
        }
        self.client._perform_json("POST", "/projects/%s/wiki/" % (self.project_key), body=body)
        article = DSSWikiArticle(self.client, self.project_key, article_id)

        # set article content if given
        if content is not None:
            article_data = article.get_data()
            article_data.set_body(content)
            article_data.save()

        return article

class DSSWikiSettings(object):
    """
    Global settings for the wiki, including taxonomy. Call save() to save

    :param client: an api client to connect to the DSS backend
    :param project_key: identifier of the project to access
    :param dict settings: current wiki settings (containing taxonomy and home article)
    """
    def __init__(self, client, project_key, settings):
        self.client = client
        self.project_key = project_key
        self.settings = settings

    def get_taxonomy(self):
        """
        Get the taxonomy

        :returns: The taxonomy
        :rtype: list
        """
        return self.settings["taxonomy"]

    def set_taxonomy(self, taxonomy):
        """
        Set the taxonomy

        :param list taxonomy: the taxonomy
        """
        self.settings["taxonomy"] = taxonomy

    def get_home_article_id(self):
        """
        Get the home article ID

        :returns: The home article ID
        :rtype: str
        """
        return self.settings["homeArticleId"]

    def set_home_article_id(self, home_article_id):
        """
        Set the home article ID

        :param str home_article_id: the home article ID
        """
        self.settings["homeArticleId"] = home_article_id

    def save(self):
        """
        Save the current settings to the backend
        """
        self.settings = self.client._perform_json("PUT", "/projects/%s/wiki/" % (self.project_key), body=self.settings)

class DSSWikiArticle(object):
    """
    A handle to manage an article

    :param DSSClient client: an api client to connect to the DSS backend
    :param str project_key: identifier of the project to access
    :param str article_id: the article ID
    """
    def __init__(self, client, project_key, article_id):
        self.client = client
        self.project_key = project_key
        self.article_id = article_id
        # encode in UTF-8 if its python2 and unicode
        if sys.version_info < (3,0) and isinstance(self.article_id, unicode):
            self.article_id = self.article_id.encode('utf-8')

    def get_data(self):
        """"
        Get article data handle

        :returns: the article data handle
        :rtype: DSSWikiArticleData
        """
        article_data = self.client._perform_json("GET", "/projects/%s/wiki/%s" % (self.project_key, dku_quote_fn(self.article_id)))
        return DSSWikiArticleData(self.client, self.project_key, self.article_id, article_data)

    def upload_attachement(self, fp):
        """
        Upload an attachment file and attaches it to the article

        :param filetype fp: A file-like object that represents the upload file
        """
        self.client._perform_json("POST", "/projects/%s/wiki/%s/upload" % (self.project_key, dku_quote_fn(self.article_id)), files={"file":fp})

    def delete(self):
        """
        Delete the article
        """
        self.client._perform_empty("DELETE", "/projects/%s/wiki/%s" % (self.project_key, dku_quote_fn(self.article_id)))

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the article

        :returns: the discussion handle for this article
        :rtype: DSSObjectDiscussions
        """
        return DSSObjectDiscussions(self.client, self.project_key, "ARTICLE", self.article_id)

class DSSWikiArticleData(object):
    """
    A handle to manage an article

    :param DSSClient client: an api client to connect to the DSS backend
    :param str project_key: identifier of the project to access
    :param str article_id: the article ID
    :param dict article_data: the article data got from the backend
    """
    def __init__(self, client, project_key, article_id, article_data):
        self.client = client
        self.project_key = project_key
        self.article_id = article_id # don't need to check unicode here (already done in DSSWikiArticle)
        self.article_data = article_data

    def get_body(self):
        """
        Get the markdown body as string

        :returns: the article body
        :rtype: str
        """
        return self.article_data["payload"]

    def set_body(self, content):
        """
        Set the markdown body

        :param str content: the article content
        """
        self.article_data["payload"] = content

    def get_metadata(self):
        """
        Get the article metadata

        :returns: the article metadata
        :rtype: dict
        """
        return self.article_data["article"]

    def set_metadata(self, metadata):
        """
        Set the article metadata

        :param dict metadata: the article metadata
        """
        self.article_data["article"] = metadata

    def save(self):
        """
        Save the current article data to the backend
        """
        self.article_data = self.client._perform_json("PUT", "/projects/%s/wiki/%s" % (self.project_key, dku_quote_fn(self.article_id)), body=self.article_data)

from .discussion import DSSObjectDiscussions
import json
import urllib

class DSSWiki(object):
    """
    A handle to manage the wiki of a project
    """
    def __init__(self, client, project_key):
        self.client = client
        self.project_key = project_key

    ###############################
    # Wiki definition
    ###############################
    def get(self):
        """
        Get wiki definition

        Returns:
            the wiki (dict with project key, home article and taxonomy)
        """
        return self.client._perform_json("GET", "/projects/%s/wiki/" % (self.project_key))

    def set(self, wiki):
        """
        Set wiki definition

        Args:
            the wiki (dict with project key, home article and taxonomy)

        Returns:
            the updated wiki
        """
        return self.client._perform_json("PUT", "/projects/%s/wiki/" % (self.project_key), body=wiki)

    def create_article(self, article_id, parent_id):
        """
        Create a wiki article

        Args:
            the article ID
            the parent article ID or None if no parent (at wiki root scope)

        Returns:
            the newly created article definition with payload (article content)
        """
        body = {
            "projectKey": self.project_key,
            "id": article_id,
            "parent": parent_id
        }
        return self.client._perform_json("POST", "/projects/%s/wiki/" % (self.project_key), body=body)

    def get_article(self, article_id):
        """
        Get a wiki article

        Args:
            the article ID

        Returns:
            the wiki article object
        """
        return DSSWikiArticle(self.client, self.project_key, article_id)

class DSSWikiArticle(object):
    """
    A handle to manage an article
    """
    def __init__(self, client, project_key, article_id):
        self.client = client
        self.project_key = project_key
        self.article_id = article_id
        if isinstance(self.article_id, unicode):
            self.article_id = self.article_id.encode('utf-8')

    ##########################
    # Article definition
    ##########################
    def get(self):
        """"
        Get article definition

        Returns:
            the article definition with payload (article content)
        """
        print("/projects/%s/wiki/%s" % (self.project_key, urllib.quote(self.article_id)))
        return self.client._perform_json("GET", "/projects/%s/wiki/%s" % (self.project_key, urllib.quote(self.article_id)))

    def set(self, article_with_payload):
        """
        Set article definition

        Args:
            the article definition with payload (article content)

        Returns:
            the updated article
        """
        return self.client._perform_json("PUT", "/projects/%s/wiki/%s" % (self.project_key, urllib.quote(self.article_id)), body=article_with_payload)

    def delete(self):
        """
        Delete the article
        """
        self.client._perform_empty("DELETE", "/projects/%s/wiki/%s" % (self.project_key, urllib.quote(self.article_id)))

    ########################################################
    # Discussions
    ########################################################
    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the article

        Returns:
            the DSSObjectDiscussions of this article
        """
        return DSSObjectDiscussions(self.client, self.project_key, "ARTICLE", self.article_id)


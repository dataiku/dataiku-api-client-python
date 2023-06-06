from .discussion import DSSObjectDiscussions
from ..utils import DataikuException
import sys
import copy
import re

if sys.version_info >= (3,0):
  import urllib.parse
  dku_quote_fn = urllib.parse.quote
else:
  import urllib
  dku_quote_fn = urllib.quote

class DSSWiki(object):
    """
    A handle to manage the wiki of a project

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.get_wiki`
    """

    def __init__(self, client, project_key):
        self.client = client
        self.project_key = project_key

    def get_settings(self):
        """
        Get wiki settings

        :returns: a handle to manage the wiki settings (taxonomy, home article)
        :rtype: :class:`dataikuapi.dss.wiki.DSSWikiSettings`
        """
        return DSSWikiSettings(self.client, self.project_key, self.client._perform_json("GET", "/projects/%s/wiki/" % (self.project_key)))

    def get_article(self, article_id_or_name):
        """
        Get a wiki article

        :param str article_id_or_name: reference to the article, it can be its ID or its name
        :returns: a handle to manage the Article
        :rtype: :class:`dataikuapi.dss.wiki.DSSWikiArticle`
        """
        return DSSWikiArticle(self.client, self.project_key, article_id_or_name)

    def __flatten_taxonomy__(self, taxonomy):
        """
        Private recursive method to get the flatten list of article IDs from the taxonomy

        :param list taxonomy:

        :returns: list of articles
        :rtype: list of :class:`dataikuapi.dss.wiki.DSSWikiArticle`
        """
        article_list = []
        for article in taxonomy:
            article_list.append(self.get_article(article['id']))
            article_list += self.__flatten_taxonomy__(article['children'])
        return article_list

    def list_articles(self):
        """
        Get a list of all the articles in form of :class:`dataikuapi.dss.wiki.DSSWikiArticle` objects

        :returns: list of articles
        :rtype: list of :class:`dataikuapi.dss.wiki.DSSWikiArticle`
        """
        return self.__flatten_taxonomy__(self.get_settings().get_taxonomy())

    def create_article(self, article_name, parent_id=None, content=None):
        """
        Create a wiki article and return a handle to interact with it.

        :param str article_name: the article name
        :param str parent_id: the parent article ID (or None if the article has to be at root level, defaults to **None**)
        :param str content: the article content (defaults to **None**)

        :returns: the created article
        :rtype: :class:`dataikuapi.dss.wiki.DSSWikiArticle`
        """
        body = {
            "projectKey": self.project_key,
            "name": article_name,
            "parent": parent_id
        }
        result = self.client._perform_json("POST", "/projects/%s/wiki/" % (self.project_key), body=body)
        article = DSSWikiArticle(self.client, self.project_key, result['article']['id'])

        # set article content if given
        if content is not None:
            article_data = article.get_data()
            article_data.set_body(content)
            article_data.save()

        return article

    def get_export_stream(self, paper_size="A4", export_attachment=False):
        """
        Download the whole wiki of the project in PDF format as a binary stream.

         .. warning::
            You need to close the stream after download. Failure to do so will result in the DSSClient becoming unusable.

        :param str paper_size: the format of the exported page, can be one of 'A4', 'A3', 'US_LETTER' or 'LEDGER' (defaults to **A4**)
        :param bool export_attachment: export the attachments of the article(s) in addition to the pdf in a zip file (defaults to **False**)
        :returns: the exported pdf or zip file as a stream
        """
        body = {
            "paperSize": paper_size,
            "exportAttachment": export_attachment
        }
        return self.client._perform_raw("POST", "/projects/%s/wiki/actions/export" % (self.project_key), body=body)

    def export_to_file(self, path, paper_size="A4", export_attachment=False):
        """
        Download the whole wiki of the project in PDF format into the given output file.

        :param str path: the path of the file where the pdf or zip file will be downloaded
        :param str paper_size: the format of the exported page, can be one of 'A4', 'A3', 'US_LETTER' or 'LEDGER' (defaults to **A4**)
        :param bool export_attachment: export the attachments of the article(s) in addition to the pdf in a zip file (defaults to **False**)
        """
        with self.get_export_stream(paper_size=paper_size, export_attachment=export_attachment) as stream:
            with open(path, 'wb') as f:
                for chunk in stream.iter_content(chunk_size=10000):
                    if chunk:
                        f.write(chunk)
                        f.flush()


class DSSWikiSettings(object):
    """
    Global settings for the wiki, including taxonomy. Call save() to save
    """
    def __init__(self, client, project_key, settings):
        """Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.wiki.DSSWiki.get_settings`"""
        self.client = client
        self.project_key = project_key
        self.settings = settings

    def get_taxonomy(self):
        """
        Get the taxonomy.
        The taxonomy is an array listing at top level the root article IDs and their children in a tree format.
        Every existing article of the wiki has to be in the taxonomy once and only once.
        For instance:

        .. code-block:: python

            [
                {
                    'id': 'article1',
                    'children': []
                },
                {
                    'id': 'article2',
                    'children': [
                        {
                            'id': 'article3',
                            'children': []
                        }
                    ]
                }
            ]

        .. note ::
            Note that this is a direct reference, not a copy, so modifications to the returned object will be reflected when saving

        :returns: The taxonomy
        :rtype: list
        """
        return self.settings["taxonomy"] if "taxonomy" in self.settings else []

    def __retrieve_article_in_taxonomy__(self, taxonomy, article_id, remove=False):
        """
        Private recursive method that get the sub tree structure from the taxonomy for a specific article

        :param list taxonomy: the current level of taxonomy
        :param str article_id: the article to retrieve
        :param bool remove: either remove the sub tree structure or not (defaults to **False**)

        :returns: the sub tree structure at a specific article level
        :rtype: dict
        """
        idx = 0
        for tax_article in taxonomy:
            if tax_article["id"] == article_id:
                ret = taxonomy.pop(idx) if remove else taxonomy[idx]
                return ret
            children_ret = self.__retrieve_article_in_taxonomy__(tax_article["children"], article_id, remove)
            if children_ret is not None:
                return children_ret
            idx += 1
        return None

    def move_article_in_taxonomy(self, article_id, parent_article_id=None):
        """
        An helper to update the taxonomy by moving an article with its children as a child of another article

        :param str article_id: the main article ID
        :param str parent_article_id: the new parent article ID or None for root level (defaults to **None**)
        """
        old_taxonomy = copy.deepcopy(self.settings["taxonomy"])

        tax_article = self.__retrieve_article_in_taxonomy__(self.settings["taxonomy"], article_id, True)
        if tax_article is None:
            raise DataikuException("Article not found: %s" % (article_id))

        if parent_article_id is None:
            self.settings["taxonomy"].append(tax_article)
        else:
            tax_parent_article = self.__retrieve_article_in_taxonomy__(self.settings["taxonomy"], parent_article_id, False)
            if tax_parent_article is None:
                self.settings["taxonomy"] = old_taxonomy
                raise DataikuException("Parent article not found (or is one of the article descendants): %s" % (parent_article_id))
            tax_parent_article["children"].append(tax_article)


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
        return self.settings["homeArticleId"] if "homeArticleId" in self.settings else None

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
    """
    def __init__(self, client, project_key, article_id_or_name):
        """Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.wiki.DSSWiki.get_article`"""
        self.client = client
        self.project_key = project_key

        # Retrieve the real article id
        article_data = self.client._perform_json("GET", "/projects/%s/wiki/%s" % (project_key, article_id_or_name))
        self.article_id = article_data["article"]['id']
        # encode in UTF-8 if its python2 and unicode
        if sys.version_info < (3,0) and isinstance(self.article_id, unicode):
            self.article_id = self.article_id.encode('utf-8')

    def get_data(self):
        """
        Get article data handle

        :returns: the article data handle
        :rtype: :class:`dataikuapi.dss.wiki.DSSWikiArticleData`
        """
        article_data = self.client._perform_json("GET", "/projects/%s/wiki/%s" % (self.project_key, self.article_id))
        return DSSWikiArticleData(self.client, self.project_key, self.article_id, article_data)

    def upload_attachement(self, fp, filename):
        """
        Upload and attach a file to the article.

        .. note ::
            Note that the type of file will be determined by the filename extension

        :param file fp: A file-like object that represents the upload file
        :param str filename: The attachement filename
        """
        clean_filename = re.sub(r'[^A-Za-z0-9 ._-]+', '', filename)

        self.client._perform_json("POST", "/projects/%s/wiki/%s/upload" % (self.project_key, dku_quote_fn(self.article_id)), files={"file":(clean_filename, fp)})

    def get_uploaded_file(self, upload_id):
        """
        Download an attachment of the article

        .. warning::
            You need to close the stream after download. Failure to do so will result in the DSSClient becoming unusable.

        :param str upload_id: The attachement upload id

        :returns: The attachment file as a stream
        :rtype: :class:`requests.Response`
        """
        return self.client._perform_raw("GET", "/projects/%s/wiki/%s/uploads/%s" % (self.project_key, self.article_id, upload_id))

    def get_export_stream(self, paper_size="A4", export_children=False, export_attachment=False):
        """
        Download the article in PDF format as a binary stream.

        .. warning::
           You need to close the stream after download. Failure to do so will result in the DSSClient becoming unusable.

        :param str paper_size: the format of the exported page, can be one of 'A4', 'A3', 'US_LETTER' or 'LEDGER' (defaults to **A4**)
        :param bool export_children: export the children of the article in the pdf (defaults to **False**)
        :param bool export_attachment: export the attachments of the article(s) in addition to the pdf in a zip file (defaults to **False**)

        :returns: the exported pdf or zip file as a stream
        :rtype: :class:`requests.Response`
        """
        body = {
            "paperSize": paper_size,
            "exportChildren": export_children,
            "exportAttachment": export_attachment
        }
        return self.client._perform_raw("POST", "/projects/%s/wiki/%s/actions/export" % (self.project_key, self.article_id), body=body)

    def export_to_file(self, path, paper_size="A4", export_children=False, export_attachment=False):
        """
        Download the article in PDF format into the given output file.

        :param str path: the path of the file where the pdf or zip file will be downloaded
        :param str paper_size: the format of the exported page, can be one of 'A4', 'A3', 'US_LETTER' or 'LEDGER' (defaults to **A4**)
        :param bool export_children: export the children of the article in the pdf (defaults to **False**)
        :param bool export_attachment: export the attachments of the article(s) in addition to the pdf in a zip file (defaults to **False**)
        """
        with self.get_export_stream(paper_size=paper_size, export_children=export_children, export_attachment=export_attachment) as stream:
            with open(path, 'wb') as f:
                for chunk in stream.iter_content(chunk_size=10000):
                    if chunk:
                        f.write(chunk)
                        f.flush()

    def delete(self):
        """
        Delete the article
        """
        self.client._perform_empty("DELETE", "/projects/%s/wiki/%s" % (self.project_key, dku_quote_fn(self.article_id)))

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the article

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.dss.wiki.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "ARTICLE", self.article_id)

class DSSWikiArticleData(object):
    """
    A handle to manage an article
    """
    def __init__(self, client, project_key, article_id, article_data):
        """Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.wiki.DSSWikiArticle.get_data`"""
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
        return self.article_data["payload"] if "payload" in self.article_data else None

    def set_body(self, content):
        """
        Set the markdown body

        :param str content: the article content
        """
        self.article_data["payload"] = content

    def get_metadata(self):
        """
        Get the article metadata

        .. note ::
            Note that this is a direct reference, not a copy, so modifications to the returned object will be reflected when saving

        :returns: the article metadata
        :rtype: dict
        """
        return self.article_data["article"] if "article" in self.article_data else None

    def set_metadata(self, metadata):
        """
        Set the article metadata

        :param dict metadata: the article metadata
        """
        self.article_data["article"] = metadata

    def get_name(self):
        """
        Get the article name

        :returns: the article name
        :rtype: str
        """
        return self.article_data["article"]["name"]

    def set_name(self, name):
        """
        Set the article name

        :param str name: the article name
        """
        self.article_data["article"]["name"] = name

    def save(self):
        """
        Save the current article data to the backend.
        """
        self.article_data = self.client._perform_json("PUT", "/projects/%s/wiki/%s" % (self.project_key, dku_quote_fn(self.article_id)), body=self.article_data)

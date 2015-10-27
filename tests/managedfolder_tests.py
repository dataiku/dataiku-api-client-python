from dataikuapi.dssclient import DSSClient
import json
from nose.tools import ok_
from nose.tools import eq_
import tempfile
import filecmp
import os.path as osp
import sys, traceback
from contextlib import closing

host="http://localhost:8082"
apiKey="ZZYqWxPnc2nWMJMUXwykn6wzA7jokbp5"
testProjectKey="BOX"

def list_managedfolders_test():
    client = DSSClient(host, apiKey)
    managedfolders = client.get_project(testProjectKey).list_managed_folders()
    ok_(len(managedfolders) > 0)    

def create_delete_test():
    client = DSSClient(host, apiKey)
    project = client.get_project(testProjectKey)
    count = len(project.list_managed_folders())

    managedfolder = project.create_managed_folder("titi")
    eq_(count + 1, len(project.list_managed_folders()))
    
    managedfolder.delete()    
    eq_(count, len(project.list_managed_folders()))
    
def get_set_test():
    client = DSSClient(host, apiKey)
    project = client.get_project(testProjectKey)
    managedfolder = project.create_managed_folder("titi")
    
    definition = managedfolder.get_definition()
    definition['description'] = 'describe me!'
    managedfolder.set_definition(definition)
    definition2 = managedfolder.get_definition()

    eq_('describe me!', definition2['description'])
    
    managedfolder.delete()    

def updload_download_test():
    temp_folder = tempfile.mkdtemp()
    stuff = osp.join(temp_folder, "test.txt")
    with open(stuff, "w") as f:
        f.write('some contents\n on several\nlines')
    
    client = DSSClient(host, apiKey)
    project = client.get_project(testProjectKey)
    managedfolder = project.create_managed_folder("titi")

    count = len(managedfolder.list_contents()['items'])
    with open(stuff, "r") as f:
        managedfolder.put_file('stuff', f)
    eq_(count + 1, len(managedfolder.list_contents()['items']))
        
    stuff2 = osp.join(temp_folder, "test2.txt")
    with open(stuff2, "w") as f:
        with closing(managedfolder.get_file('stuff')) as s:
            f.write(s.raw.read())
    
    eq_(True, filecmp.cmp(stuff, stuff2))

    managedfolder.delete()    
           
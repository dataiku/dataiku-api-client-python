from dataikuapi.dssclient import DSSClient
from dataikuapi.utils import DataikuException
import json
from nose.tools import ok_
from nose.tools import eq_
from nose.tools import raises
import tempfile
import filecmp
import os.path as osp
import sys, traceback
from contextlib import closing

host="http://localhost:8082"
apiKey="5YZ4lHpXexhlNk29FqRi8AcO2EVGddtA"
testProjectKey="BOX3"


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
     
def updload_replace_delete_test():
    temp_folder = tempfile.mkdtemp()
    stuff = osp.join(temp_folder, "test.txt")
    stuffb = osp.join(temp_folder, "testb.txt")
    with open(stuff, "w") as f:
        f.write('some contents\n on several\nlines')
    
    client = DSSClient(host, apiKey)
    project = client.get_project(testProjectKey)
    managedfolder = project.create_managed_folder("titi")

    count = len(managedfolder.list_contents()['items'])
    with open(stuff, "r") as f:
        managedfolder.put_file('stuff', f)
    eq_(count + 1, len(managedfolder.list_contents()['items']))
        
    with open(stuffb, "w") as f:
        with closing(managedfolder.get_file('stuff')) as s:
            f.write(s.raw.read())
    
    eq_(True, filecmp.cmp(stuff, stuffb))

    managedfolder.delete_file('stuff')
    eq_(count, len(managedfolder.list_contents()['items']))

    managedfolder.delete()    


@raises(DataikuException)
def access_contents_outside_test():
    temp_folder = tempfile.mkdtemp()
    file_content = 'some contents\n on several\nlines'
    stuff = osp.join(temp_folder, "test.txt")
    with open(stuff, "w") as f:
        f.write(file_content)
    
    client = DSSClient(host, apiKey)
    project = client.get_project(testProjectKey)
    managedfolder = project.create_managed_folder("titi")

    count = len(managedfolder.list_contents()['items'])
    with open(stuff, "r") as f:
        managedfolder.put_file('stuff', f)
    eq_(count + 1, len(managedfolder.list_contents()['items']))
        
    with closing(managedfolder.get_file('stuff')) as s:
        c = s.raw.read()
    eq_(file_content, c)
    
    try:
        # climb the file hierarchy up to the dip_home
        with closing(managedfolder.get_file('../../../shared-secret.txt')) as s:
            c = s.raw.read()
        raise AssertionError('Access outside folder should fail')        
    finally:
        managedfolder.delete()  
          
@raises(DataikuException)
def delete_contents_outside_test():
    temp_folder = tempfile.mkdtemp()
    file_content = 'some contents\n on several\nlines'
    stuff = osp.join(temp_folder, "test.txt")
    with open(stuff, "w") as f:
        f.write(file_content)
    
    client = DSSClient(host, apiKey)
    project = client.get_project(testProjectKey)
    managedfolder = project.create_managed_folder("titi")

    count = len(managedfolder.list_contents()['items'])
    with open(stuff, "r") as f:
        managedfolder.put_file('stuff', f)
    eq_(count + 1, len(managedfolder.list_contents()['items']))
        
    with closing(managedfolder.get_file('stuff')) as s:
        c = s.raw.read()
    eq_(file_content, c)
    
    try:
        # climb the file hierarchy up to the dip_home
        managedfolder.delete_file('../../../shared-secret.txt')
        raise AssertionError('Access outside folder should fail')        
    finally:
        managedfolder.delete()    
           
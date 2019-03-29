#!/usr/bin/env python

from ldap3 import Server, Connection, ALL
from ldap3.extend.microsoft.addMembersToGroups import ad_add_members_to_groups as ad_add
from ldap3.extend.microsoft.removeMembersFromGroups import ad_remove_members_from_groups as ad_remove
import yaml
import os

username = os.environ['LDAP_USER']
password = os.environ['LDAP_PASSWORD']
domain = os.environ['LDAP_DOMAIN']
user_files = os.environ['USER_FILES_DIR']
user_search_base = os.environ['USER_SEARCH_BASE']
group_search_base = os.environ['GROUP_SEARCH_BASE']
config = {}
ad_users = []
ad_mgmt = []
users_to_add = []
mgmt_to_add = []
users_to_remove = []
mgmt_to_remove = []
server = Server(domain, get_info=ALL)
conn = Connection(server, user=username, password=password, auto_bind=True, authentication='NTLM')

def get_users_from_files(d):
    #Given a directory path (full or relative) return a list of dicts containing yaml configuration.
    #dict spec: {org:'org_name',users:[sAMAccountname],managers:[sAMAccountname]}
    print("Retrieving users from files located at "+d)
    _config = []
    os.chdir(d)
    for file in os.listdir():
        if file.endswith('.yml') and not file.startswith('sample'):
            with open(file, 'r') as f:
                _config.append(yaml.load(f.read()))
                
    return _config

def get_group_members(group_name,sb=user_search_base):
    #Given an AD search base and a group common name return a list of dicts containing user attributes of the members
    #dict spec: {sAMAccountname:distinguishedName}
    print("Retrieving users from group "+group_name)
    _users = {}
    conn.search(sb, '(&(objectClass=person)(memberOf=CN='+group_name+',DC=fabrikam,DC=foo))',attributes=['sAMAccountname','distinguishedName'])

    for i in conn.entries:
        _users.update({i.sAMAccountName.value:i.distinguishedName.value})
    
    return _users

def update_group_members(user_sam,membershipDict,sb=user_search_base):
    #Given a list of user sAMAccountnames, a dictionary of user attributes, and an AD search base, return an updated dictionary including users from the passed list.
    #If the user is not found in AD the program will exit with a non-zero exit code.
    #dict spec: {sAMAccountname:distinguishedName}
    if len(user_sam) > 0:
        print("Fetching user DNs for new users")
        print(user_sam)
        for u in user_sam:
            if conn.search(sb, '(&(objectClass=person)(sAMAccountname='+u+'))',attributes='distinguishedName'):
              membershipDict.update({u:conn.entries[0].distinguishedName.value})
            else:
              print("User "+u+" not found. Nothing has been changed. Exiting...")
              exit(1)
        return membershipDict

def diff_users(truth_list,record_list):
    #Given two lists, return a dict of differences of each list
    #dict spec: {left_list:[list_items],right_list:[list_items]}
    lower_truth_list = _to_lower_case(truth_list)
    lower_record_list = _to_lower_case(record_list)
    print("Computing the difference between user lists")
    _list_diff = {}
    _list_diff.update({'left_list':list(set(lower_truth_list)-set(lower_record_list))})
    _list_diff.update({'right_list':list(set(lower_record_list)-set(lower_truth_list))})
    return _list_diff

def get_group_DN(group_name,sb=group_search_base):
    #Given a search base DN and a group name returns a string describing the distinguishedName of the group. Returns an empty string if the group doesn't exist in active directory
    # or if an error is returned from active directory.
    print("Retrieving distinguished name for the group "+group_name)
    if conn.search(sb, '(&(objectClass=group)(CN='+group_name+'))',attributes='distinguishedName'):
        return conn.entries[0].distinguishedName.value
    else:
        print("Group "+group_name+" not found in search base "+sb)
        return ''

def get_attr_from_dict(id_dict,id_list=users_to_add):
    #Given a list of keys and a dictionary return a list of the corresponding values from the dictionary
    print("Retrieving distinguished names from the ID dictionary")
    _attr_list = []
    
    for i in id_list:
        _attr_list.append(id_dict[i])
    
    return _attr_list

def add_users(ad_connection,user_list,group_dn):
    #Given an active directory connection object, a list of user sAMAccountnames, and a group distinguished name, add the users from the list to the group in active directory    
    if len(user_list) > 0:
        print("Adding users to the group "+group_dn)
        print(user_list)
        ad_add(ad_connection,user_list,group_dn,raise_error=False)
    else:
        print("No users to add to the group "+group_dn)

def remove_users(ad_connection,user_list,group_dn):
    #Given an active directory connection object, a list of user sAMAccountnames, and a group distinguished name, remove the users from the list from the group in active directory 
    if len(user_list) > 0:
        print("Removing users from group "+group_dn)
        print(user_list)
        ad_remove(ad_connection,user_list,group_dn,fix=True,raise_error=False)
    else:
        print("No users to remove from the group "+group_dn)

def _to_lower_case(user_list):
  lower_list = []
  for item in user_list:
    lower_list.append(item.lower())
  return lower_list

config = get_users_from_files(user_files)
for c in config:
  ad_group = 'Group_naming_'+c['org']+'_convention'
  ad_users = get_group_members(ad_group)
  users_to_add = diff_users(c['users'],list(ad_users.keys()))['left_list']
  users_to_remove = diff_users(c['users'],list(ad_users.keys()))['right_list']
  user_group_dn = get_group_DN(ad_read_group,group_search_base)

  add_users(conn,get_attr_from_dict(update_group_members(users_to_add,ad_users,user_search_base),users_to_add),user_group_dn)
  remove_users(conn,get_attr_from_dict(ad_users,users_to_remove),user_group_dn)
  
conn.unbind()
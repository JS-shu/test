#!/usr/bin/env python
# coding=utf-8
from os import listdir
from os.path import isfile, isdir, join
import cgi, cgitb
import syslog
import os
import sys
import json
import commands
import time
import ConfigParser
import requests


def getConfig(section, name, expt = True):
    config = ConfigParser.ConfigParser()
    config.read("/etc/toplink/toplink_deploy.ini")
    if not config.has_section("global"):
        syslog.syslog("Section global not be set")
        sys.exit()

    if not config.has_section(section):
        section = "global"
    if config.has_option(section,name):
        return config.get(section,name)
    if config.has_option("global",name):
        return config.get("global",name)

    if expt == False:
        return False

    syslog.syslog("The section %s name %s not be found!" % (section_name,name))
    sys.exit()


form = cgi.FieldStorage()
data = form.file.read()
if not data:
    syslog.syslog("No Post data!")
    sys.exit()

syslog.syslog(data)

hook_json = json.loads(data)
if 'ref' not in hook_json:
    syslog.syslog("Error json format")
    syslog.syslog(data)
    sys.exit()

if hook_json['event_name'] != "push":
    syslog.syslog("Error event_name:%s" % hook_json['event_name'])
    sys.exit()

git_project = hook_json['project']['name']
git_group   = hook_json['project']['namespace']
git_event   = hook_json['event_name']
git_branch  = hook_json['ref']
git_url     = hook_json['project']['git_http_url']
respo       = getConfig(git_group,"respo")
git_path    = hook_json['project']['path_with_namespace']

loc_git    = "%s/%s.git" % (respo, git_path)

ts = time.time()
#default is dev
git_branch_name = "dev"
param      = getConfig("global","param")
target_url = getConfig(git_group,"deploy_to_dev")
s3_url     = getConfig(git_group,"deploy_to_s3",False)
work_tree  = getConfig("global","work_tree_dev")
key        = getConfig(git_group,"key")
auto_deploy= getConfig(git_group,"auto_deploy")
target_url_slave = getConfig(git_group,"deploy_to_slave",False)

if auto_deploy=="no":
    syslog.syslog("The group [%s] Don't need to deploy!" % git_group)
    sys.exit()

if git_branch == "refs/heads/master":
    git_branch_name = "master"
    work_tree = getConfig("global","work_tree")
    key        = getConfig(git_group,"key")

    if getConfig(git_group,git_project+"_deploy_to",False) == False:
        target_url = getConfig(git_group,"deploy_to")
    else:
        target_url = getConfig(git_group,git_project+"_deploy_to")
        key        = getConfig(git_group,git_project+"_key")

    if getConfig(git_group,git_project+"_deploy_to_s3",False) == False:
        s3_url = getConfig(git_group,"deploy_to_s3",False)
    else:
        s3_url = getConfig(git_group,git_project+"_deploy_to_s3",False)

    param      = getConfig(git_group,"param")

if not os.path.exists(work_tree+git_project):
    os.makedirs(work_tree+git_project)

syslog.syslog("work tree:%s" % work_tree)

syslog.syslog("Group name:%s Project name:%s" % (git_group, git_project))
cmd_str = "sudo /etc/toplink/git_checkout.sh %s %s %s" % (loc_git, work_tree+git_project, git_branch_name)
#cmd_str = "sudo git --git-dir=%s --work-tree=%s checkout master -f" % (loc_git, work_tree)
syslog.syslog("build work tree:%s" % cmd_str)
(status, output) = commands.getstatusoutput(cmd_str)
syslog.syslog("result[%d]:%s" %(status,output))


#原本是不管master分支還是dev分支,只要/etc/toplink/toplink_deploy.ini有設定,就會更新至aws上
#現在依照分支來推版
#cmd_sync = "rsync %s \"ssh -i %s\" -o StrictHostKeyChecking=no %s %s" % (param ,key ,work_tree+git_project ,target_url)
if git_branch_name == "master":
    cmd_sync ="sudo /etc/toplink/git_deploy.sh '%s' %s %s %s"  % (param ,key ,work_tree+git_project ,target_url)
    syslog.syslog("deploy to production server:%s" % cmd_sync)
    (status, output) = commands.getstatusoutput(cmd_sync)
    syslog.syslog("===>result[%d]:%s" %(status,output))

#if target_url_slave:
if git_branch_name == "dev":
    cmd_sync ="sudo /etc/toplink/git_deploy.sh '%s' %s %s %s"  % (param ,key ,work_tree+git_project ,target_url_slave)
    syslog.syslog("deploy to slave server:%s" % cmd_sync)
    (status, output) = commands.getstatusoutput(cmd_sync)
    syslog.syslog("===>slave result[%d]:%s" %(status,output))

delpoy_time = time.time() - ts
s3_time = 0
if s3_url:
    ts_s3 = time.time()
    root_path = work_tree+git_project
    root_path = root_path.rstrip('/')
    s3_path = s3_url.rstrip('/')

    cmd_sync = "s3cmd -c /etc/.s3cfg  --no-mime-magic --guess-mime-type sync  %s %s/" % (root_path, s3_path )
    syslog.syslog("deploy to aws s3:%s" % cmd_sync)
    (status, output) = commands.getstatusoutput(cmd_sync)
    s3_time = time.time() - ts_s3
    syslog.syslog("===>slave result[%d]:%s time:%d" %(status,output,s3_time))
    #clear for cdn
    if git_group == "webdesign":
        # 會員中心
        my_data = {'cdn_path': '/webdesign/membership/release/*'}
        r = requests.post('http://aws-utils.top-link.com.tw/clear_cdn.php', data = my_data)
    else:
        # cms
        my_data = {'cdn_path': '/exhibit_ui/cms_ui/*'}
        r = requests.post('http://aws-utils.top-link.com.tw/clear_cdn.php', data = my_data)
        path = '/var/www/htdocs/cms_ui'
        files = listdir(path)
        for f in files:
            fullpath = join(path, f)
            if isdir(fullpath):
                my_data = {'cdn_path': '/exhibit_ui/cms_ui/'+f+'/*'}
                r = requests.post('http://aws-utils.top-link.com.tw/clear_cdn.php', data = my_data)
                syslog.syslog("===>clear %s CDN:%s" % ( f, r.text.encode('utf-8').strip()))


syslog.syslog("******deploy finished:%s deploy time:%d s3 time:%d*******" % ((work_tree+git_project),delpoy_time,s3_time))
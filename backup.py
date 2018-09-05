# This script backs up whole Github account with all user forks.
# It depends on Github token with full repo rights which needs to 
# be created in advance.
# The token is then downloaded from S3 bucket so make sure to put it there
# and specify the right filename
#
# These are the pip dependencies which need to be installed:
# # pip install gitpython pygithub3 boto3 --user
import pygithub3
import git
import os
import boto3

organization=''
s3_token_bucket=''
s3_token_file=''
#s3_backup_bucket=''

# Define lists
repos_to_copy=[]

def get_token():
    s3 = boto3.resource('s3')
    obj = s3.Object(s3_token_bucket, s3_token_file)
    return obj.get()['Body'].read().decode('utf-8')

def gather_clone_urls(token):
    print "Getting main repo URLs"
    gh = pygithub3.Github(token=token)
    all_repos = gh.repos.list_by_org(org=organization,type='all').all()
    for repo in all_repos:
        repos_to_copy.append((repo.name, repo.ssh_url))
    print "Getting fork URLs"
    for repo in all_repos:
        forks = gh.repos.forks.list(user=organization, repo=repo.name, sort='newest').all()
        for fork in forks:
            repos_to_copy.append((fork.name, fork.ssh_url))

def clone_repos():
    cwd = os.getcwd()
    dir = cwd + "/backup/"
    for repo in repos_to_copy:
        repo_name=repo[0]
        git_url=repo[1]
        fork_name=git_url[git_url.find('git@github.com:')+len('git@github.com:'):git_url.rfind('/')]
        path=dir + repo_name + "/" + fork_name
        #print fork_name
        #If repo exists, use fetch:
        if os.path.isdir(path):
            print "Fetching " + fork_name + " " + path + " from " + git_url
            repo = git.Repo(path)
            for remote in repo.remotes:
                object = remote.fetch()
                for branch in object:
                    print str(branch) + " fetched"
        else:
            #print "repo doesn't exist"
            print "Cloning " + fork_name + " " + path + " from " + git_url
            git.Repo.clone_from(git_url, os.path.join(dir, path))

# This thing works very slow
def uploadDirectory(bucketname):
    bucketname=s3_backup_bucket
    s3 = boto3.resource('s3')
    cwd = os.getcwd()
    for root,dirs,files in os.walk(cwd):
        for file in files:
            s3.meta.client.upload_file(os.path.join(root,file),bucketname,file)

# Get repo URLs
gather_clone_urls(get_token())
print repos_to_copy
# Clone them
clone_repos()
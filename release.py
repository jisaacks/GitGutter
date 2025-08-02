# -*- coding: utf-8 -*-
#!/usr/bin/python

import json
import os
import subprocess

try:
    PACKAGE_PATH = os.path.dirname(__spec__.origin)
except (AttributeError, NameError):
    PACKAGE_PATH = os.path.dirname(__file__)
MESSAGE_DIR = 'messages'
MESSAGE_PATH = os.path.join(PACKAGE_PATH, MESSAGE_DIR)


def get_message(fname):
    with open(fname, 'r', encoding='utf-8') as file:
        message = file.read()
    return message


def put_message(fname, text):
    with open(fname, 'w', encoding='utf-8') as file:
        file.write(text)


def built_messages_json(version_history):
    """Write the version history to the messages.json file."""
    output = os.path.join(PACKAGE_PATH, 'messages.json')
    with open(output, 'w+', encoding='utf-8') as file:
        json.dump(
            obj={v: MESSAGE_DIR + '/' + v + '.txt' for v in version_history},
            fp=file, indent=4, separators=(',', ': '), sort_keys=True)
        file.write('\n')


def version_history():
    """Return a list of all releases."""
    def generator():
        for filename in os.listdir(MESSAGE_PATH):
            basename, ext = os.path.splitext(filename)
            if ext.lower() == '.txt':
                yield basename

    def sortkey(key):
        """Convert filename to version tuple (major, minor, patch)."""
        try:
            major, minor, patch = key.split('.', 2)
            if '-' in patch:
                patch, _ = patch.split('-')
            return int(major), int(minor), int(patch)
        except:
            return 0, 0, 0

    return sorted(tuple(generator()), key=sortkey)


def git(*args):
    """Run git command within current package path."""
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        startupinfo = None
    proc = subprocess.Popen(
        args=['git'] + [arg for arg in args], startupinfo=startupinfo,
        stdout=subprocess.PIPE, stdin=subprocess.PIPE, cwd=PACKAGE_PATH)
    stdout, _ = proc.communicate()
    return stdout.decode('utf-8').strip() if stdout else None


def commit_release(version):
    """Create a 'Cut <version>' commit and tag."""
    commit_message = 'Cut %s' % version
    git('add', '.')
    git('commit', '-m', commit_message)
    git('tag', '-a', '-m', commit_message, version)


def build_release():
    """Built the new release locally."""
    history = version_history()
    version = history[-1]
    put_message(os.path.join(PACKAGE_PATH, 'VERSION'), version)
    built_messages_json(history)
    commit_release(version)
    print("Release %s created!" % version)


def publish_release(token):
    """Publish the new release."""
    version = get_message(os.path.join(PACKAGE_PATH, 'VERSION'))

    repo_url = 'https://github.com/jisaacks/GitGutter.git'
    # push master branch to server
    git('push', repo_url, 'master')
    # push tags to server
    git('push', repo_url, 'tag', version)

    # publish the release
    post_url = '/repos/jisaacks/GitGutter/releases?access_token=' + token
    headers = {
        'User-Agent': 'Sublime Text',
        'Content-type': 'application/json',
    }
    # get message from /messages/<version>.txt
    text = get_message(os.path.join(MESSAGE_PATH, version + '.txt'))
    # strip message header (version)
    text = text[text.find('\n') + 1:]
    # built the JSON request body
    data = json.dumps({
        "tag_name": version,
        "target_commitish": "master",
        "name": version,
        "body": text,
        "draft": False,
        "prerelease": False
    })
    try:
        import http.client
        client = http.client.HTTPSConnection('api.github.com')
        client.request('POST', post_url, body=data, headers=headers)
        response = client.getresponse()
        print("Release %s published!" % version
              if response.status == 201 else
              "Release %s failed!" % version)
    finally:
        client.close()


"""
======================================
Command Line Interface
======================================
"""
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Built and Publish GitGutter Releases')
    parser.add_argument(
        dest='command',
        help='The command to perform is one of [BUILD|PUBLISH].')
    parser.add_argument(
        '--token',
        nargs='?',
        help='The GitHub access token used for authentication.')
    args = parser.parse_args()
    if args.command.lower() == 'build':
        build_release()
    elif args.command.lower() == 'publish':
        publish_release(args.token)


"""
======================================
Sublime Text Command Interface
======================================
"""
try:
    import sublime
    import sublime_plugin

    SETTINGS = "GitGutter.sublime-settings"

    class GitGutterBuildReleaseCommand(sublime_plugin.ApplicationCommand):

        def is_visible(self):
            settings = sublime.load_settings(SETTINGS)
            return settings.has('github_token')

        def run(self):
            """Built a new release."""
            build_release()

    class GitGutterPublishReleaseCommand(sublime_plugin.ApplicationCommand):

        def is_visible(self):
            settings = sublime.load_settings(SETTINGS)
            return settings.has('github_token')

        def run(self):
            """Publish the new release."""
            settings = sublime.load_settings(SETTINGS)
            publish_release(settings.get('github_token', ''))

except ImportError:
    pass

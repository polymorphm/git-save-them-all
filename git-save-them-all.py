#!/usr/bin/python

import argparse
import datetime
import subprocess
import os, os.path

class SaveThemAllError(Exception):
    pass

def check_hash_in_hash(git, repo, ancestor, descendant):
    hashes = '{}..{}'.format(ancestor, descendant)
    cmd = [git, 'rev-list', '-n1', '--ancestry-path', hashes]
    env = dict(os.environ)
    env['GIT_DIR'] = repo

    p = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env)

    if p.returncode:
        rv = p.stderr.decode().rstrip()
        raise SaveThemAllError(
                'git binary has returned an error: {}: {}'.format(cmd, rv))

    rv = p.stdout.decode().rstrip()

    if not rv:
        return False

    if rv == descendant:
        return True

    raise SaveThemAllError('unexpected result from git binary: {}: {}'.format(
            cmd, rv))

def refs_walk(dir_path):
    if not os.path.isdir(dir_path):
        return

    next_queue = [None]

    while next_queue:
        queue = next_queue
        next_queue = []

        for q_item in queue:
            if q_item is not None:
                path = '{}/{}'.format(dir_path, q_item)
            else:
                path = dir_path

            with os.scandir(path) as scan:
                for d in scan:
                    if d.is_symlink():
                        continue

                    if q_item is not None:
                        next_q_item = '{}/{}'.format(q_item, d.name)
                    else:
                        next_q_item = d.name

                    if d.is_dir():
                        next_queue.append(next_q_item)
                        continue

                    if not d.is_file():
                        continue

                    next_path = '{}/{}'.format(dir_path, next_q_item)

                    yield next_q_item

def take_next_seq(dir_pathes):
    seq = 0

    for dir_path in dir_pathes:
        if not os.path.isdir(dir_path):
            continue

        with os.scandir(dir_path) as scan:
            for d in scan:
                try:
                    num = int(d.name)
                except ValueError:
                    continue

                seq = max(seq, num)

    return seq + 1

def read_hash(path, name):
    file_path = '{}/{}'.format(path, name)

    try:
        with open(file_path, encoding='utf-8') as fd:
            return fd.read().rstrip()
    except FileNotFoundError:
        pass

def make_prefix(path, name):
    dir_path = path
    name_parts = name.split('/')

    for name_part in name_parts:
        dir_path = '{}/{}'.format(dir_path, name_part)

        try:
            os.mkdir(dir_path)
        except FileExistsError:
            pass

def unlink_prefix(path, name):
    dir_path = path
    name_parts = name.split('/')
    dir_pathes = []

    for name_part in name_parts:
        dir_path = '{}/{}'.format(dir_path, name_part)
        dir_pathes.append(dir_path)

    dir_pathes.reverse()

    for dir_path in dir_pathes:
        try:
            os.rmdir(dir_path)
        except OSError:
            break

def make_hash(path, name, h):
    dir_path = path
    name_parts = name.split('/')
    file_name = name_parts.pop()

    for name_part in name_parts:
        dir_path = '{}/{}'.format(dir_path, name_part)

        try:
            os.mkdir(dir_path)
        except FileExistsError:
            pass

    file_path = '{}/{}'.format(dir_path, file_name)

    with open(file_path, 'w', encoding='utf-8', newline='\n') as fd:
        fd.write('{}\n'.format(h))

def unlink_hash(path, name):
    dir_path = path
    name_parts = name.split('/')
    dir_pathes = []

    for name_part in name_parts:
        dir_path = '{}/{}'.format(dir_path, name_part)
        dir_pathes.append(dir_path)

    dir_pathes.reverse()
    file_path = dir_pathes.pop()

    os.unlink(file_path)

    for dir_path in dir_pathes:
        try:
            os.rmdir(dir_path)
        except OSError:
            break

def save_them_all(repo, git=None, namespace=None, remote=None, date=None):
    assert isinstance(git, str)
    assert namespace is None or isinstance(namespace, str)
    assert isinstance(remote, str)
    assert isinstance(date, datetime.datetime)

    date_str = date.strftime('%Y/%m/%d')

    if namespace is not None:
        live_branch_prefix = '{}/live/branch'.format(namespace)
        live_tag_prefix = '{}/live/tag'.format(namespace)
        dead_branch_prefix_proto = '{}/dead/branch/{}'.format(namespace,
                date_str)
        dead_tag_prefix_proto = '{}/dead/tag/{}'.format(namespace, date_str)
    else:
        live_branch_prefix = 'live/branch'
        live_tag_prefix = 'live/tag'
        dead_branch_prefix_proto = 'dead/branch/{}'.format(date_str)
        dead_tag_prefix_proto = 'dead/tag/{}'.format(date_str)

    refs_path = '{}/refs'.format(repo)
    heads_path = '{}/heads'.format(refs_path)

    if not os.path.isdir(heads_path):
        raise SaveThemAllError(
                'repo does not seem like a git repo directory: {}'.format(
                        repo))

    remote_path = '{}/remotes/{}'.format(refs_path, remote)
    # tags are shared, not only for one remote
    tags_path = '{}/tags'.format(refs_path)

    live_branch_path = '{}/{}'.format(heads_path, live_branch_prefix)
    live_tag_path = '{}/{}'.format(heads_path, live_tag_prefix)

    dead_seq = take_next_seq((
            '{}/{}'.format(heads_path, dead_branch_prefix_proto),
            '{}/{}'.format(heads_path, dead_tag_prefix_proto)))
    dead_branch_prefix = '{}/{:0>4}'.format(dead_branch_prefix_proto,
            dead_seq)
    dead_tag_prefix = '{}/{:0>4}'.format(dead_tag_prefix_proto, dead_seq)

    dead_branch_path = '{}/{}'.format(heads_path, dead_branch_prefix)
    dead_tag_path = '{}/{}'.format(heads_path, dead_tag_prefix)

    for name in refs_walk(live_branch_path):
        h = read_hash(live_branch_path, name)
        rel_h = read_hash(remote_path, name)

        if h == rel_h:
            continue

        if rel_h is None or not check_hash_in_hash(git, repo, h, rel_h):
            make_prefix(heads_path, dead_branch_prefix)
            make_hash(dead_branch_path, name, h)
            unlink_hash(live_branch_path, name)
            unlink_prefix(heads_path, live_branch_prefix)

    for name in refs_walk(live_tag_path):
        h = read_hash(live_tag_path, name)
        rel_h = read_hash(tags_path, name)

        # for tags simple checking of hash value equaling is enough
        if h != rel_h:
            make_prefix(heads_path, dead_tag_prefix)
            make_hash(dead_tag_path, name, h)
            unlink_hash(live_tag_path, name)
            unlink_prefix(heads_path, live_tag_prefix)

    for name in refs_walk(remote_path):
        h = read_hash(remote_path, name)
        rel_h = read_hash(live_branch_path, name)

        if h != rel_h:
            make_prefix(heads_path, live_branch_prefix)
            make_hash(live_branch_path, name, h)

    for name in refs_walk(tags_path):
        h = read_hash(tags_path, name)
        rel_h = read_hash(live_tag_path, name)

        if h != rel_h:
            make_prefix(heads_path, live_tag_prefix)
            make_hash(live_tag_path, name, h)

def main():
    parser = argparse.ArgumentParser(
                description='An utility to helping save all '
                'branches-and-tags of another (linked) project\'s git. It\'s '
                'like you\'re making a backup, but its logic is in '
                'branches/tags level. The utility could be a part of some '
                'big automation script.'
            )

    parser.add_argument(
                '-g',
                '--git',
                help='path to git binary. default is \'git\'',
            )

    parser.add_argument(
                '-n',
                '--namespace',
                help='associate this namespace with tracking remote '
                'branches/tags. default is nothing',
            )

    parser.add_argument(
                '-r',
                '--remote',
                help='the name of a tracking remote. default is \'origin\'',
            )

    parser.add_argument(
                '-d',
                '--date',
                help='override the current date',
            )

    parser.add_argument(
                'repo',
                help='path to git repo',
            )

    args = parser.parse_args()

    if args.git is not None:
        git = args.git
    else:
        git = 'git'

    if args.remote is not None:
        remote = args.remote
    else:
        remote = 'origin'

    if args.date is not None:
        try:
            fromisoformat = datetime.datetime.fromisoformat
        except AttributeError:
            # python version before 3.7
            strptime = datetime.datetime.strptime
            fromisoformat = lambda s: strptime(s, '%Y-%m-%d')

        date = fromisoformat(args.date)
    else:
        date = datetime.datetime.now()

    save_them_all(args.repo, git=git, namespace=args.namespace, remote=remote,
            date=date)

if __name__ == '__main__':
    main()

# vi:ts=4:sw=4:et

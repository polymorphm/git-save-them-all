README
======

``git-save-them-all`` is an utility to helping save all branches-and-tags of
another (linked) project's git. It's like you're making a backup, but its
logic is in branches/tags level. The utility could be a part of some big
automation script.

The utility tracks every branch/tag of linked project's git, and while a
tracked branch/tag exists the utility sets it ``live/`` prefix. as soon as the
branch/tag become absent the utility will set it ``dead/XXXX/XX/XX/XXXX/``
prefix (where ``XXXX/XX/XX/XXXX`` is a date of detected death).

A tracked branch/tag **pushed through force** is considared as leaded to death
and recreated a new one. Therefore the previous branch/tag value will be saved
as ``dead/XXXX/XX/XX/XXXX/`` and a new value will be set as ``live/``. That is,
the utility wont let us lose linked project's data for this reason.

In other words, now you are able to do with confidence any dangerous oprations
with linked project's branches and tags (delete, rename, push-forced, rebase,
etc) -- ``git-save-them-all`` will take care about safe saving extended git history.

Why not just use ``git reflog``? The answer: we *should* use ``git reflog``.
The utility can make an additional level of safety besides ``git reflog``.

Version
-------

Development version.

The Example Of Using
--------------------

The first iteration: setup and the first fetch::

   git init --bare ~/path/to/my/git/backup.git

   cd ~/path/to/my/git/backup.git

   git remote add origin git@a-server-name.org:a/project/name.git # write your project's URL here

   git fetch -pPt origin # ``-p`` is ``--prune`` (prune branches); ``-P`` is ``--prune-tags``; ``-t`` is ``--tags`` (fetch all tags)

   ~/my_tools/git-save-them-all/git-save-them-all.py .

Each next iteration for this backup: tracking of branches/tags for the
project::

   cd ~/path/to/my/git/backup.git

   git fetch -pPt origin

   ~/my_tools/git-save-them-all/git-save-them-all.py .

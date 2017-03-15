# -*- coding: utf-8 -*-


class GitStatus(object):
    """Repository and file status class.

    The class represents the branch and file status as returned by a call of
        git status --porcelain=2 -z -b -u --ignored <file>
    """

    # file file_states used by GitGutter
    COMMITTED = 0
    IGNORED = 1
    UNTRACKED = 2
    UNKNOWN = 4
    MODIFIED = 8
    STAGED = 16
    STAGED_MODIFIED = STAGED | MODIFIED
    IGNORED_UNTRACKED = IGNORED | UNTRACKED | UNKNOWN

    # text representations for file status
    _STATUS_TEXT = {
        COMMITTED: 'committed',
        IGNORED: 'ignored',
        MODIFIED: 'modified',
        STAGED: 'staged',
        STAGED_MODIFIED: 'staged and modified',
        UNKNOWN: '(unknown)',
        UNTRACKED: 'untracked',
    }

    def __init__(self):
        """Initialize an GitStatus object."""
        self.valid = False
        # checked out branch name
        self.branch = None
        # checked out branch head commit hash
        self.head = None
        # remote reference
        self.upstream = None
        # commits ahead upstream
        self.ahead = 0
        # commits behind upstream
        self.behind = 0
        # simplified file file_state from <XY>
        self.file_state = self.UNKNOWN
        # index file object id
        self.index_oid = None
        # working file object id
        self.working_oid = None
        # number of deleted regions
        self.lines_deleted = 0
        # number of inserted lines
        self.lines_inserted = 0
        # number of modified lines
        self.lines_modified = 0

    def from_bytes(self, output):
        """Parse output of git status.

        Arguments:
            output (bytes): The binary output of
                git status --porcelain=2 -z -b -u --ignored <file>
            which is used to set the attributes.

        Example:
            # branch.oid <head>
            # branch.head <branch>
            # branch.upstream <upstream>
            # branch.ab +<ahead> -<behind>
            1 <XY> N... 100644 100644 100644 <woid> <ioid> <path>
            ? <path>
            ! <path>

        Returns:
            GitFileStatus: A named tuple with the status of the file.
        """
        # reset some attributes which would not be updated if file is committed
        self.index_oid = None
        self.working_oid = None
        self.file_state = self.UNKNOWN
        # Abort here if output is empty
        if not output:
            return self
        # remove last 0-terminator and split output into lines and columns
        for line in output.strip(b'\x00').split(b'\x00'):
            line = line.decode('utf-8')
            start = line[0] if line else None
            # '#': branch information
            if start == '#':
                # In case only branch information were returned the file is
                # commited.
                self.file_state = self.COMMITTED
                _, key, value = line.split(' ', 2)
                if key == 'branch.oid':
                    self.head = value
                elif key == 'branch.head':
                    self.branch = value
                elif key == 'branch.upstream':
                    self.upstream = value
                elif key == 'branch.ab':
                    ahead, behind = value.split(' ', 1)
                    self.ahead = int(ahead[1:])
                    self.behind = int(behind[1:])
            # '1': committed, staged or modified file entry
            elif start == '1':
                (_, state, _, _, _, _, self.working_oid,
                 self.index_oid, _) = line.split(' ', 8)
                if state[0] != '.':
                    self.file_state |= self.STAGED
                if state[1] != '.':
                    self.file_state |= self.MODIFIED
            # '!': ignored file entry
            elif start == '!':
                self.file_state = self.IGNORED
            # '?': untracked file entry
            elif start == '?':
                self.file_state = self.UNTRACKED
        self.valid = True
        # allow chained commands
        return self

    def clear_line_stats(self):
        """Return status and empty diff result."""
        self.lines_deleted = 0
        self.lines_inserted = 0
        self.lines_modified = 0
        return (self, (0, 0, [], [], []))

    def update_line_stats(self, processed_diff):
        """Merge status and diff result."""
        if processed_diff:
            _, _, inserted, modified, deleted = processed_diff
            self.lines_inserted = len(inserted)
            self.lines_modified = len(modified)
            self.lines_deleted = len(deleted)
        if self.lines_inserted or self.lines_modified or self.lines_deleted:
            self.set_modified()
        return (self, processed_diff)

    def set_modified(self):
        """Set the working file state modified if file is tracked.

        Returns:
            bool: Returns True, if state was changed or false otherwise.
        """
        if self.file_state & (self.IGNORED_UNTRACKED | self.MODIFIED):
            return False
        self.file_state &= self.STAGED
        self.file_state |= self.MODIFIED
        return True

    def is_ignored_or_untracked(self):
        """Return True if the file is ignored or untracked."""
        return self.file_state & self.IGNORED_UNTRACKED

    def is_committed(self):
        """Return True if the file is committed."""
        return self.file_state == self.COMMITTED

    def is_modified(self):
        """Return True if the file is modified."""
        return self.file_state == self.MODIFIED

    def is_staged(self):
        """Return True if the file is in the staging area."""
        return self.file_state & self.STAGED

    def status_text(self):
        """Return a literal representation of the file status."""
        try:
            return self._STATUS_TEXT[self.file_state]
        except KeyError:
            return self._STATUS_TEXT[self.UNKNOWN]

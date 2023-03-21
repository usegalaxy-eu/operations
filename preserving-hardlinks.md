---
title: Usegalaxy.EU preserving-hardlinks
---

# The problem


Conda makes extensive use of POSIX "hardlinks" in order to save mass
storage space: if two or more packages share files with identical
contents, only one copy of the file actually needs to be stored on
disk. This is fine as long as you never need to make manual changes in
the resulting file system tree after the fact.

We did, however, on occasion have to make repairs in the conda tree
(restoring contents of files that had accidentially been truncated to
zero length). This operation requires some care, so as not to break the
hardlink structure.


# Executive summary

Don't use `rsync(1)` *without* the `--inplace` option for copying over
files with "multiple hard links" if the link structure is to be
preserved. It's best to try out your preferred method of file copy in
a different directory on the same file system/network share, to make
sure files are not accidentially unlinked/moved before they are
re-written. Check the link count (2nd column in the output of `ls -l`
to verify). E.g.

```
$ echo "OLD" > f1
$ ln f1 f2
$ ln f2 f3
$ echo "NEW" > f0
$ $YOUR_FILE_COPY_COMMAND_OF_PREDILECTION f0 f2
$ ls -l
total 16
-rw-r--r--  1 janky  bioinf  4 Mar 21 14:46 f0
-rw-r--r--  3 janky  bioinf  4 Mar 21 14:47 f1
-rw-r--r--  3 janky  bioinf  4 Mar 21 14:47 f2
-rw-r--r--  3 janky  bioinf  4 Mar 21 14:47 f3
$ cat *
NEW
NEW
NEW
NEW
$ 
```


## What are "hardlinks" anyway?

In POSIX file systems, with the exception of the file name, all
information about a file is stored on disk in a data structure called
"inode". The inode contains information about the type, ownership,
permissions, size, extent list, modification time etc. The directory
entry for a file just contains a link into the file system's inode
table. For regular files there is usually just one link to its inode,
but it it possible to create an arbitrary number of links to any given
inode, so a POSIX file can, within a given file system, have an
arbitrary number of file names!

If a POSIX file has more than one file name (i.e. more than one link
to its inode exists), it is common to say colloquially that "these
files are hardlinked", which is, however, not technically correct, as
it is really only one file with more than one name. Also, there is no
link back from the inode to the directory entries referencing it, so
there is no easy, direct way to find the other directory entries
linking to a given inode. E.g. in this case

```
$ ll
total 284
-rw-rw-r-- 95 galaxy galaxy 286370 Mar 21 12:22 cacert.pem
lrwxrwxrwx  1 galaxy galaxy     10 Dec  8 00:59 cert.pem -> cacert.pem
$ 
```

the second column in the long listing for the file `cacert.pem`, the
link count (95 in this case), tells us that there are 94 *other*
directory entires referencing the file besides this one, but `ls` can
not tell us where these other directory entries are in the filesystem.

(If we wanted to find them we'd have to list the file's inode number
with `ls -li` and then use the `-inum` primary predicate of `find` on
the root of the file system [and no higher, other file systems may
have assigend the same inode number to a different file!] to find
them. For your convenience, `find` has a shortcut for this: the
`-samefile` primary.)


## "Hardlinks" vs. symlinks

It is important to note how these "hardlinks" differ from the other
file name aliasing mechanism in POSIX file systems, the symbolic link
("symlink").

Symlinks are much like X.509-aliases, they are like a doorsign saying
"This file has moved, don't look *here*, look *there* instead". If the
symlink is removed, the file remains intact but if the actual
directory entry for the file is removed, the file becomes inaccesible
and the symlink pointing to it becomes "dangling".

"Hardlinks", i.e. directory entries pointing to an inode are all
alike. All of them can be created and removed, but the inode is only
deleted when the *last* hard link to it is removed (and the last open
file descriptor on it closed, but that's a different topic...)

Whether or not any given file system operation affects a symlink or
the file pointed to by the symlink depends on whether or not the
operation is question "follows symlinks" (which, usually, its manual
page will tell you). Obviously, no such distinction exists for
"hardlinks" - as mentioned above all of them are different filenames
of equal worth for a given file.


## Working with multiple file names

Still there, well beyond the 280-character default attention span?
Excellent, for now we are ready to discuss the practical side.  How
are (multiple) file names created and removed or preserved?

Inode links are *created*

- Implicitly when a new file is created (the system creates an inode
  for the file, allocates disk extents as needed and adds an entry
  linking to the inode to the directory containing the file name)

- With the `link(2)` or `linkat(2)` system call; at the shell level
  the `ln(1)` command is used (*without* the `-s` option which would
  create a symlink instead)


Inode links are removed (unlinked)

- With the `unlink(2)` or `unlinkat(2)` system call. This is what the
  `rm(1)` shell command calls internally. Also, `mv(1)` uses `link(2)`
  followed by `unlink(2)` *when moving a file within the same file
  system* (otherwise it's a file copy followed by `unlink(2)`).


Inode links are preserved when just opening a file with `O_TRUNC` and
re-writing its contents, or even using mmap(2) for copying file
contents. `cp(1)` works like this, even over NFS. **Do NOT use e.g.
rsync WITHOUT the --inplace option** for the job, it will mess up the
link structure:

```
$ echo OLD > t1
$ ln t1 t2
$ ln t2 t3
$ echo NEW > t0
$ ll
total 16
-rw-r--r--  1 janky  bioinf  4 Mar 21 14:55 t0
-rw-r--r--  3 janky  bioinf  4 Mar 21 14:54 t1
-rw-r--r--  3 janky  bioinf  4 Mar 21 14:54 t2
-rw-r--r--  3 janky  bioinf  4 Mar 21 14:54 t3
$ rsync t0 t2
$ ll
total 16
-rw-r--r--  1 janky  bioinf  4 Mar 21 14:55 t0
-rw-r--r--  2 janky  bioinf  4 Mar 21 14:54 t1
-rw-r--r--  1 janky  bioinf  4 Mar 21 14:55 t2
-rw-r--r--  2 janky  bioinf  4 Mar 21 14:54 t3
$ cat *
NEW
OLD
NEW
OLD
$ 
```

This was probably not what you intended...

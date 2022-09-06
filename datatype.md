---
title: Add New Datatype
---

In order to add a new datatype, we are going to use as example the *Bref3" datatype. It means that it is not a subclass of a previous one (for subclassed new datatypes you can read the [dedicated section](https://docs.galaxyproject.org/en/master/dev/data_types.html#adding-a-new-data-type-subclassed) in the Galaxy documentation).


The first step is to fork the the [main Galaxy repository](https://github.com/galaxyproject/galaxy). Then we should clone the repository in our local instance and create a new branch. 

```console
git clone git@github.com:galaxyproject/galaxy.git
cd galaxy
git checkout -b "Add_new_datatype"
```

Then, we need to register the new datatype in the [**lib/galaxy/config/sample/datatypes_conf.xml.sample**](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/config/sample/datatypes_conf.xml.sample) file. The sample `<datatype` tag includes the following attributes:

- extension - the datatype's file extension
- type - the path to the class for that data type
- mimetype - if present (it’s optional), the datatype's mime type
- display_in_upload - if present (it’s optional), the associated file extension will be displayed in the “File Format” select list in the “Upload File from your computer” tool

In order to create the new entry is recommended to check the [technical specifications](https://faculty.washington.edu/browning/beagle/bref3.14May18.pdf) of the new datatype. This is an example of a new datatype register:

```console
<datatype extension="bref3" type="galaxy.datatypes.binary:Bref3" display_in_upload="true" description="Bref3 format is a binary format for storing phased, non-missing genotypes for a list of samples. More information in https://faculty.washington.edu/browning/beagle/bref3.14May18.pdf" />
```

The next step is to add a new entry in the `<sniffers>` tag section, in the bottom part of the **datatypes_config.xml** file. In the case of our example:

```console
<sniffer type="galaxy.datatypes.binary:Bref3" />
```

It is necessary in order to automatically detect the format from their content by the Galaxy sniffer. For additional details, you can read [the corresponding section](https://docs.galaxyproject.org/en/master/dev/data_types.html#step-2-sniffer) in the documentation.

Now we need to include a new class in the corresponding file, based on its superclass (in our specific case, binary). It requires to include a `file_ext` attribute to the class and create any necessary functions to override the functions in your new datatype’s superclass. An efficient approach for identifying the format of binary files is to use magic numbers.

The following command will create a hexdump of the file we pass to it, which will be useful for finding the Bref3 datatype magic number:

```console
xxd example_file.bref3 | head
```

The magic number can be found in the first line, in our example: *7a88 74f4 0015 6272*.

The next step is to add the corresponding class to [**lib/galaxy/datatypes/binary.py**](https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/datatypes/binary.py) (be aware that the specific Python file depends on your datatype); in our case:

```console
class Bref3(Binary):
    """Bref3 format is a binary format for storing phased, non-missing genotypes for a list of samples."""
    file_ext = "bref3"

    def __init__(self, **kwd):
        super().__init__(**kwd)
        self._magic = binascii.unhexlify("7a8874f400156272")

    def sniff_prefix(self, sniff_prefix):
        return sniff_prefix.startswith_bytes(self._magic)

    def set_peek(self, dataset, is_multi_byte=False):
        if not dataset.dataset.purged:
            dataset.peek = "Binary bref3 file"
            dataset.blurb = nice_size(dataset.get_size())
        else:
            dataset.peek = 'file does not exist'
            dataset.blurb = 'file purged from disk'

    def display_peek(self, dataset):
        try:
            return dataset.peek
        except Exception:
            return f"Binary bref3 file ({nice_size(dataset.get_size())})"

```

Now, we can commit and push the changes:

```console
git add lib/galaxy/datatypes/binary.py
git add lib/galaxy/config/sample/datatypes_conf.xml.sample
git commit -m "Add new datatype"
git push

```

Finally, we need to add a tiny test file to the [galaxy-test-data repository](https://github.com/galaxyproject/galaxy-test-data), which will be used for manually testing the new datatype by running the following command (it should be included in the description of the [Pull Request](https://github.com/galaxyproject/galaxy/pull/12199):

```console
from galaxy.datatypes.sniff import get_test_fname
fname = get_test_fname('affy_v_agcc.cel')
Bref3().sniff(fname)
False
fname = get_test_fname('ref.bref3')
Bref3().sniff(fname)
True

```
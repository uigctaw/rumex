import pathlib

import rumex

# directory structure
#
# +- ...
# +- examples/
#    |
#    +- ...
#    +- fiding_feature_files/
#       |
#       +- find_files.py
#       +- features_files/
#          |
#          +- first_file.feature
#          +- more_files/
#             |
#             +- second_file.feature
#             +- file_with_a_different_extension.test

file1, file2 = rumex.find_input_files(
    root=pathlib.Path(__file__).parent.joinpath("feature_files"),
    extension="feature",
)

assert file1.uri.endswith("feature_files/first_file.feature")
assert file1.text == "Hello, world!\n"

assert file2.uri.endswith("feature_files/more_files/second_file.feature")
assert file2.text == "Mars welcomes...\n"

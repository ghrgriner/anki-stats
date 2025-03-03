# Overview

Anki is open-source flashcard software written in Python, Qt, Rust,
Svelte, and other languages. The software supports add-ons where users
can include their own code or third-party code through a Python
interface. Python is a language commonly used in the data science
field, while Rust is less widely adopted.

The purpose of this repository and documentation is to: 

1. describe the statistics included in Anki in greater detail than
that provided by the application (e.g., to describe the analysis
population and methods used for each table or chart in the output),
and 

2. provide Python code that generates similar output as the 
application reports, with the expectation that this will be 
an easier starting point than the existing Svelte and Rust
code for users who wish to create custom reports.

# Input Data

The Python program expects a tab-delimited flat file with one
record per card and `'"'` as the escape character for quoting.
The expected fields in the input are described in the module 
docstring of the Python program. An Anki add-on capable of
extracting the necessary fields is available in the
[anki-stats-exporter](https://github.com/ghrgriner/anki-stats-exporter/)
repository.

# Repository Wiki

Additional information is available on the wiki of this
repository, which can be accessed by clicking the tab above or
[here](https://github.com/ghrgriner/anki-stats/wiki).


# Trademark Notice
Anki is a registered trademark of Ankitects Pty Ltd.
We are not endorsed by or affiliated with Ankitects Pty Ltd.

# Introduction

Anki™ is open-source flashcard software written in Python, Qt, Rust,
Svelte, and other languages. Flashcards are organized into decks,
and Anki software provides a
[statistics window](https://docs.ankiweb.net/stats.html#statistics)
where users can obtain information on their studying performance for a deck.
In total, eight to eleven figures and two text/tabular outputs are
generated. For example, there is a histogram
for the number of past reviews per day stratified by learning phase, and
unstratified histograms of expected future reviews by day, card difficulty,
and card retrievability.  Bar charts and a table show the number of times
the user indicated the 'right' answer was obtained during study
stratified by study hour or the various learning phases defined by
the software.

The statistics window offers much flexibility in sub-setting the deck population
for analysis, but each table or figure has only limited further
customizability, often a single set of radio buttons to choose
the length of time to display or amount of history to use in the analysis.
Nevertheless, there are
[various use cases](#Motivation) where additional analyses would be of interest.
The Anki software authors
acknowledge in the user manual there may be users interested in their own
statistics (which they call ['manual analysis'](https://docs.ankiweb.net/stats.html#manual-analysis))
but support this only with detailed (and a bit out-of-date) documentation
on the table logging reviews as well as unimplemented suggestions on how
data can be extracted.

Anki software has [an add-on interface](https://addon-docs.ankiweb.net) where users
can write Python modules that interact with the software.
There are [existing add-ons](https://github.com/ghrgriner/anki-stats/wiki/Existing-Add%E2%80%90Ons-That-Create-Custom-Figures)
that add custom figures to the new (or legacy [see previous link]) statistics
window. However, for one-time or infrequent analyses, we believe it is not
worth the effort of integrating the analysis into Anki software. Python is a
general-purpose programming language widely adopted and used, especially
among the subset of users with computer programming ability who are
not full-blown computer scientists. It would benefit these users
to have a Python implementation for manual analysis as well as
improved documentation of behavior in the Rust backend.

A final advantage of a Python implementation is that once the statistics
are extracted from the Anki software into data frames, they can be used
for purposes other than statistical reporting. For example, users who
keep the master copy of their notes on their desktop (e.g., in a spreadsheet)
can run programs to generate columns for pasting (or otherwise incorporating)
into these sheets. Fields of interest might include the days since a note
was studied, the days until the next card for the note is due, card flag
or difficulty information, etc. An [example program](./example_add_fields_to_notes.py)
is provided for interested users to customize.

## Objectives

Given the above, the purpose of this repository and documentation is to:

1. Describe the statistics included in the Anki software statistics window
in greater detail than that provided by the application (e.g., to describe
the analysis population and methods used for each table or figure)

2. Provide technical documentation on key data structures and
database fields in greater detail than that provided in the (mostly
non-technical) [Anki Manual](https://docs.ankiweb.net)

3. Provide Python (pandas) code that generates tabular output that matches the
output in the statistics window for each table or figure (although for
brevity we omit the figure footnotes and provide code that matches only one
radio button selection, usually the '1 month' radio button selection
when this controls the amount of bins on a histogram x-axis and the
'all' button otherwise)

4. Provide [example code](./example_add_fields_to_notes.py)
that reuses the code needed for (3) to perform
useful tasks other than reporting statistics. For example, a sample program
takes a text file of notes as input and outputs a text file with new fields, e.g.,
the number of days since a card on the note was reviewed,
the number of days in the future the next card on the note will be reviewed,
the flags for each card on the note, etc.

Elaborating on point (3) above, this repository does the heavy lifting
of the manual analyses proposed in the Anki Manual. Users can install
and run the
[companion data-exporter add-on](https://github.com/ghrgriner/anki-stats-exporter),
update the parameters in `parameters.py` with the path(s) to the downloaded
file(s), and then run `anki_stats.py` to create analysis datasets at the
card and review level from which they can immediately make custom
tables and figures. The export step can be omitted if the user elects
to configure the input parameters to [access the Anki software database directly](https://github.com/ghrgriner/anki-stats/wiki/Alternate-Data-Access-Methods).

# Motivation

Consider the following motivating questions and situations:

1. Among figures that report card counts the total counts are not always
the same, and similarly for figures that report review counts. Why
is this?

2. How are the tables and figures affected when studying is done in a
[filtered deck](https://docs.ankiweb.net/filtered-decks.html)? For
example, are these reviews included when counting the percent of
reviews that were correct?

3. How are the tables and figures affected when studying is done early
or late? For example, are these included when counting the percent
of reviews that were correct? Does it matter how early or late the
review was?

4. Are early reviews used in calculating Free Spaced Repetition Scheduler (FSRS)
   stability and retrievability? Are they used when optimizing FSRS
   parameters?

5. How are the tables and figures affected when cards are
reset or deleted?

6. Where are the FSRS variables (difficulty, stability, etc...) stored
in the database and with what precision are they stored?

7. You are studying a foreign language and you have two different
card types: one with your target language on the front and the other
with your native language on the front. You are interested in having
selected figures and tables stratified by these two card types.

8. You suspect or know some cards are harder than others and are
interested in quantifying the amount. For example, suppose you are
studying a foreign language with cards that have your native language
on the front. Some cards have a single target language word on the
back, and other cards have multiple target language words, where
you must differentiate between the meanings. You are interested in
quantifying the additional effort for the harder cards. For example,
is the average number of reviews per card for cards with three answers
on the back three times as much as the average number of reviews per
card with one answer on the back? Or is it more or less?

9. Two or more users are studying identical decks, and they would
like to compare their performance at the level of individual cards.

10. A user keeps the 'master copy' of their notes in a spreadsheet on
their desktop. They export its sheet(s) as text files and process these
to make text file(s) for upload. The user would like an indicator on
the sheet of properties stored in the Anki software database, e.g., which
notes were reviewed today (or in the last week, etc.), the due date, flags
for cards on the note, etc.

# Input Data

The Python program expects a tab-delimited flat file with one
record per card and `'"'` as the escape character for quoting.
The expected fields in the input are described in the module
docstring of the Python program. An Anki add-on capable of
extracting the necessary fields is available in the
[anki-stats-exporter](https://github.com/ghrgriner/anki-stats-exporter/)
repository.

# Limitations

The Retrievability table generated by this package differs
slightly from the counts in the figure in the statistics window
for `INPUT_MODE_TEXT`. See [the wiki](https://github.com/ghrgriner/anki-stats/wiki/FSRS-Retrievability)
for details.

There are other ways of interacting with the Anki software backend
than those illustrated in this repository. For example, there is an
add-on called AnkiConnect that appears to be widely used but also
has some apparent limitations discussed [here](https://forums.ankiweb.net/t/built-in-rest-api-for-anki-clients/66425).
(We have no experience ourselves with this add-on.

There is also an `anki` Python package that can be used separately
from Anki's GUI. The [Anki Manual](https://addon-docs.ankiweb.net/command-line-use.html)
strongly recommends using this instead of attempting to read or
write to the `.anki2` file directly. We suspect the code we wrote
for the [anki-stats-exporter](https://github.com/ghrgriner/anki-stats-exporter/)
would not require much modification to be used with this package, since
they both use the `anki` module in the software's code.

# Anki Version

This documentation was written based on v25.02 of the Anki
desktop application.

# Repository Wiki

Additional information is available on the wiki of this
repository, which can be accessed by clicking the tab above or
[here](https://github.com/ghrgriner/anki-stats/wiki).


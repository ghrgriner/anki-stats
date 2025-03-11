# Introduction

Anki is open-source flashcard software written in Python, Qt, Rust,
Svelte, and other languages. The flashcards are organized into decks,
and Anki provides a
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
The Anki authors
acknowledge in the user manual there may be users interested in their own
statistics (which they call ['manual analysis'](https://docs.ankiweb.net/stats.html#manual-analysis))
but support this only with detailed (and a bit out-of-date) documentation
on the table logging reviews as well as unimplemented suggestions on how
data can be extracted.

Anki has [an add-on interface](https://addon-docs.ankiweb.net) where users
can write Python modules that interact with the software.
There are [existing add-ons](#Existing-Add-Ons-That-Create-Custom-Figures)
that add custom figures to the new (or legacy [see previous link]) statistics
window. However, for one-time or infrequent analyses, we believe it is not
worth the effort of integrating the analysis into Anki. Python is a
general-purpose programming language widely adopted and used, especially
among the subset of users with computer programming ability who are
not full-blown computer scientists. It would benefit these users
to have a Python implementation for manual analysis as well as
improved documentation of behavior in the Rust backend.

For these reasons, the purpose of this repository and documentation is to:

1. Describe the statistics included in the Anki statistics window
in greater detail than that provided by the application (e.g., to describe
the analysis population and methods used for each table or figure)

2. Provide technical documentation on key data structures and
database fields in greater detail than that provided in the (mostly
non-technical) [Anki Manual](https://docs.ankiweb.net)

3. Provide Python code that generates tabular output that matches the
output in the statistics window for each table or figure (although for
brevity we omit the figure footnotes and provide code that matches only one
radio button selection, usually the '1 month' radio button selection
when this controls the amount of bins on a histogram x-axis and the
'all' button otherwise)

In other words, for (3) above, this repository does the heavy lifting
of the manual analyses proposed in the Anki Manual. Users can install
and run the
[companion data-exporter add-on](https://github.com/ghrgriner/anki-stats-exporter),
update the parameters in `parameters.py` with the path(s) to the downloaded
file(s), and then run `anki_stats.py` to create analysis datasets at the
card and review level from which they can immediately make custom
tables and figures.

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

10. You would like to recalculate the total time spent with a lower
maximum seconds per card than the configured option.

# Input Data

The Python program expects a tab-delimited flat file with one
record per card and `'"'` as the escape character for quoting.
The expected fields in the input are described in the module
docstring of the Python program. An Anki add-on capable of
extracting the necessary fields is available in the
[anki-stats-exporter](https://github.com/ghrgriner/anki-stats-exporter/)
repository.

# Limitations

The Retrievability table generated by `print_stats_tables.py` differs
slightly from the counts in the figure in the statistics window
for `INPUT_MODE_TEXT`. See [the wiki](https://github.com/ghrgriner/anki-stats/wiki/FSRS-Retrievability)
for details.

# Existing Add-Ons That Create Custom Figures

We have also not previously discussed the fact that there are
actually *two* statistics windows available in Anki: (1) the
(new) window accessible by pushing the `Stats` button, and
(2) the legacy window accessible by pushing `SHIFT + Stats`.
The default graphs in the legacy window offer fewer
figures and less filtering and interaction capabilities than
the new window. Figures in the legacy window are created by
creating strings that contain HTML and Javascript in Python
rather than using Rust and Svelte.

We do not recommend developing figures for the legacy interface,
but we mention its existence so that readers will understand what
these terms refer to if [searching for add-ons on AnkiWeb](https://ankiweb.net/shared/addons).

That being said, below are two example add-ons that add
custom figures to the new statistics window and the legacy
statistics window.

**Disclaimer**: We did not author these add-ons and we have not
inspected their code. As AnkiWeb states: "As add-ons are programs
downloaded from the internet, they are potentially malicious. You
should only download add-ons you trust."

1. [Search Stats Extended](https://ankiweb.net/shared/info/1613056169):
   This add-on adds 20 graphs to the (non-legacy) statistics window.
   This is the only add-on we are aware of that manipulates the new
   statistics window.
2. [Progress Graphs and Stats for Learned and Matured Cards](https://ankiweb.net/shared/info/266436365): This adds two graphs to the legacy statistics
   window.

# Anki Version

This documentation was written based on v25.02 of the Anki
desktop application.

# Repository Wiki

Additional information is available on the wiki of this
repository, which can be accessed by clicking the tab above or
[here](https://github.com/ghrgriner/anki-stats/wiki).


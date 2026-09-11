# GTFS Binary Server Configuration

This repository contains everything for maintaining daily updates to GTFS Binary
feeds. It is based on [Transitous](https://transitous.org/) feed library sourced
from individual providers and other databases.

See [this article](https://izv.ee/gtfs/server) for a draft description.

## Feed Metadata

To adjust processing rules, see the `feeds` directory. Just like the similarly named
[directory](https://github.com/public-transport/transitous/tree/main/feeds) in Transitous,
it contains a series of files named after an ISO-3166-1 code. Here the files are in YAML
format and have `.yaml` extension, for it is easier to edit by hand.

The idea is to keep GTFS feeds between 50 and 100 MB, merging or splitting where necessary.
Also the binary format accepts some metadata not present in GTFS feeds specifically for
aiding passengers offline. Also this is done to reduce [the overlap](https://test.motis-project.org/merge_stats.html)
between feeds.

Note that we do not process feeds for which there are no country file, but the file
_can_ be empty. This is done to limit the load in a testing setup.

## Author and License

Mostly build by Ilya Zverev and published under the CC0 licence for text and data and
ISC license for code.

The NLNet Foundation has [sponsored](https://nlnet.nl/project/EasyTransit2/)
the initial development through the [NGI Mobifree Fund](https://nlnet.nl/mobifree)
with financial support from the European Commission.

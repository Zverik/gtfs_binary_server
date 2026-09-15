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

## Metadata Format

Each entry is a dictionary with a key as a file name part without the country
prefix: e.g. `tallinn` in `ee.yaml` for a feed `ee_tallinn.gtb`.
Source GTFS feeds not mentioned in the metadata are
still processed as if there were empty entries for those. For skipping a source feed,
use `skip: true` key.

Two common keys for a feed metadata are `title` and `title_en` with a feed name in the
local and English languages. Those get written directly into the feed header.

When one or more agencies have real-time information, add it to a list under `realtime`
key. It looks like this:

```yaml
realtime:
- url: https://jbb.ghsq.de/gtfs/elron/VehiclePositions
  type: gtfs-rt
  agencies: ["10520953"]
```

Here a type can be `gtfs-rt`, `siri`, or `siri-json`, just like in Transitous.
If the `agencies` list is present, the link will be written only for those agencies.

Finally, you can write a Markdown-formatted explanation on using the public transit.
It should be in English and answer those questions:

* How to buy tickets offline and online, preferably with links.
* What discounts there are?
* How to validate or whom to show your ticket.
* Can you take a bicycle?
* How to board on a wheelchair?
* Possibly add a map of routes and zones.

Having composed the text in a `feeds/meta/something.md`, add it to the `ticket_info`
metadata with an `agencies` list if needed, and a `file` key with the file name.

### Splitting and Merging Feeds

When a feed is too big (say over 100 MB), it would be a great idea to split it
into a few smaller feeds. For that, use a non-existent feed name for a key,
and add a `split: oldfeed` property with the name of the feed to split.

There are several keys to control how the feed is split:

* `agencies`: a list of strings `agency_id` that explicitly mark which agencies
  should be kept.
* `geojson`: a name of the GeoJSON file in `feeds/meta` subdirectory containing one or
  more polygons. An agency is considered inside a polygon when at least 2/3 of stops
  it serves are located inside that polygon.
* `polygons`: a list of string polygon names to filter polygons inside the geojson.
  Chosen polygons are merged into one, whether you specify the names or not.
* `negate: true`: add to process "all the rest", agencies that do not fit the filter.

Merging several feeds together is simpler: add a key `merge` with either a list
of feed name parts. E.g. `merge: [scotland, wales]` for merging `uk_scotland.gtfs.zip`
and `uk_wales.gtfs.zip`.

There is also an `merge: all` option to merge every single feed for the country.
Please make sure they are less than 100 MB combined, try aiming for ~50 MB.

## Server Directory Structure

The files are published to [gtfs.osmz.ee](https://gtfs.osmz.ee/gtb/). Here is where everything is:

```
gtb
├── ee_elron.gtb   <-- country_region.gtb, the latest binary feed
├── fi_hsl.gtb
├── feeds.json     <-- JSON array with the latest version, bbox and title for every feed
├── diffs
│   ├── ee_elron   <-- look for bsdiff output for ee_elron here
│   │   ├── 5.diff <-- use it to update from version 5 to the latest (or +20 versions)
│   │   ├── 6.diff <-- assuming 7 is the latest, so 6 here is top
│   │   └── versions.json <-- very small file with a list of versions and the latest one
│   └── fi_hsl
│       ├── 6.diff
│       └── versions.json
└── archive
    ├── ee_elron
    │   ├── 5.gtb.gz <-- gzipped historic feed
    │   ├── 6.gtb.gz
    │   └── 7.gtb.gz
    └── fi_hsl
        ├── 6.gtb.gz
        └── 7.gtb.gz
```

Note that the server expects and accepts gzip encoding for transfer! It would decrease the size
~3 times!

## Author and License

Mostly build by Ilya Zverev and published under the CC0 licence for text and data and
ISC license for code.

The NLNet Foundation has [sponsored](https://nlnet.nl/project/EasyTransit2/)
the initial development through the [NGI Mobifree Fund](https://nlnet.nl/mobifree)
with financial support from the European Commission.

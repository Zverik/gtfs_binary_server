from zipfile import ZipFile, ZIP_DEFLATED
from shapely.geometry import shape
from io import TextIOWrapper
from contextlib import contextmanager
from collections import defaultdict
import shapely
import csv
import argparse
import json
import shutil
from split_filters import processors, Filters


def read_polygon(geojson_file: str, polygon_names: list[str] | None):
    with open(geojson_file, 'r') as f:
        geojson = json.load(f)
    typ = geojson.get('type')
    if typ == 'FeatureCollection':
        polygons = geojson['features']
    elif typ == 'Feature':
        polygons = [geojson]
    else:
        polygons = [{'type': 'Feature', 'geometry': geojson, 'properties': {}}]

    shapes = []
    for poly in polygons:
        gtyp = poly.get('geometry', {}).get('type')
        if gtyp not in ('Polygon', 'MultiPolygon'):
            continue
        p = poly.get('properties', {})
        if polygon_names:
            name = p.get('name') or p.get('title') or p.get('id')
            if name not in polygon_names:
                continue
        shapes.append(shape(poly['geometry']))

    if not shapes:
        return None
    result = shapely.unary_union(shapes)
    shapely.prepare(result)
    return result


@contextmanager
def open_table(gtfs: ZipFile, table: str):
    with gtfs.open(f'{table}.txt', 'r') as f:
        yield TextIOWrapper(f, encoding='utf-8-sig')


def stops_by_agency(gtfs_in: ZipFile) -> dict[str, set[str]]:
    trips_by_route: dict[str, set[str]] = defaultdict(set)
    with open_table(gtfs_in, 'trips') as f:
        for row in csv.DictReader(f):
            trips_by_route[row['route_id']].add(row['trip_id'])

    agencies_by_trip: dict[str, set[str]] = defaultdict(set)
    with open_table(gtfs_in, 'routes') as f:
        for row in csv.DictReader(f):
            for trip_id in trips_by_route[row['route_id']]:
                agencies_by_trip[trip_id].add(row['agency_id'])

    result: dict[str, set[str]] = defaultdict(set)
    with open_table(gtfs_in, 'stop_times') as f:
        for row in csv.DictReader(f):
            for agency in agencies_by_trip[row['trip_id']]:
                result[agency].add(row['stop_id'])
    return result


def stops_in_polygon(gtfs_in: ZipFile, polygon) -> set[str]:
    stop_ids = set[str]()
    with open_table(gtfs_in, 'stops') as f:
        for row in csv.DictReader(f):
            location = shapely.Point(
                float(row['stop_lon']), float(row['stop_lat']))
            if polygon.contains(location):
                stop_ids.add(row['stop_id'])
    return stop_ids


def split(inputfile: str, outputfile: str, agencies: list[str] | None = None,
          geometry: str | None = None, polygons: list[str] | None = None,
          negate: bool = False):
    with ZipFile(inputfile, 'r') as gtfs_in:
        agency_ids = set[str]()

        if geometry:
            polygon = read_polygon(geometry, polygons)
            if not polygon:
                raise IndexError(
                    f'Could not find a polygon named {polygons} '
                    f'in {geometry}')
            poly_stops = stops_in_polygon(gtfs_in, polygon)
            agency_stops = stops_by_agency(gtfs_in)
            for agency, stops in agency_stops.items():
                # 2/3 stops served should be inside the polygon.
                if 3.0 * len(stops.intersection(poly_stops)) / len(stops) > 2:
                    agency_ids.add(agency)

        if agencies:
            ag_list = set(a.strip() for a in agencies)
            if not agency_ids:
                agency_ids = ag_list
            else:
                # If both geometry and agencies are supplies,
                # limit found agencies by the supplied list.
                agency_ids.intersection_update(ag_list)

        if not agency_ids:
            raise IndexError('No agencies to filter by')

        filters = Filters(agency_ids, negate)
        with ZipFile(outputfile, 'w', ZIP_DEFLATED) as output:
            for proc in processors:
                proc.run(gtfs_in, output, filters)
            # Copy all unprocessed files unmodified.
            files = set(proc.filename for proc in processors)
            for filename in gtfs_in.namelist():
                if filename not in files:
                    with gtfs_in.open(filename, 'r') as infile:
                        with output.open(filename, 'w') as outfile:
                            shutil.copyfileobj(infile, outfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Split a GTFS file by a polygon or agencies')
    parser.add_argument('input', help='GTFS input file')
    parser.add_argument('output', help='GTFS output, smaller file')
    parser.add_argument(
        '-a', '--agencies',
        help='List of agency_ids, comma-separated')
    parser.add_argument(
        '-g', '--geometry',
        help='GeoJSON file with polygons for filtering by stops')
    parser.add_argument(
        '-p', '--polygons', nargs='*', metavar='poly_name',
        help='For GeoJSON, names of polygons to filter by')
    parser.add_argument(
        '--not', action='store_true', dest='negate',
        help='Write agencies NOT in the list / polygon')
    options = parser.parse_args()

    agencies = [] if not options.agencies else options.agencies.split(',')
    split(options.input, options.output, agencies,
          options.geometry, options.polygons, options.negate)

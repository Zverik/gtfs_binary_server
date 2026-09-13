import io
import csv
from zipfile import ZipFile


class Filters:
    def __init__(self, agencies: set[str], negate: bool):
        self.agencies = agencies
        self.negate = negate
        self.routes = set[str]()
        self.trips = set[str]()
        self.shapes = set[str]()
        self.services = set[str]()
        self.stops = set[str]()
        self.fares = set[str]()

    def in_agencies(self, agency_id: str) -> bool:
        if not self.agencies:
            return True
        if self.negate:
            return agency_id not in self.agencies
        else:
            return agency_id in self.agencies


class ProcessorBase:
    filename: str = ''
    required: bool = True

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        raise NotImplementedError()

    def run(self, gtfs_in: ZipFile, gtfs_out: ZipFile, filters: Filters):
        if not self.required and self.filename not in gtfs_in.namelist():
            return
        with gtfs_in.open(self.filename, 'r') as csv_in:
            with gtfs_out.open(self.filename, 'w') as csv_out:
                r = csv.DictReader(io.TextIOWrapper(csv_in, 'utf-8-sig'))
                w = csv.DictWriter(io.TextIOWrapper(
                    csv_out, 'utf-8-sig', write_through=True), r.fieldnames)
                w.writeheader()
                for row in r:
                    if self.process(row, filters):
                        w.writerow(row)


class ProcessAgencies(ProcessorBase):
    filename = 'agency.txt'

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        return filters.in_agencies(row['agency_id'])


class ProcessRoutes(ProcessorBase):
    filename = 'routes.txt'

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        ok = filters.in_agencies(row['agency_id'])
        if ok:
            filters.routes.add(row['route_id'])
        return ok


class ProcessTrips(ProcessorBase):
    filename = 'trips.txt'

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        ok = row['route_id'] in filters.routes
        if ok:
            filters.trips.add(row['trip_id'])
            filters.services.add(row['service_id'])
            if row['shape_id']:
                filters.shapes.add(row['shape_id'])
        return ok


class ProcessShapes(ProcessorBase):
    filename = 'shapes.txt'
    required = False

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        return row['shape_id'] in filters.shapes


class ProcessCalendar(ProcessorBase):
    filename = 'calendar.txt'

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        return row['service_id'] in filters.services


class ProcessCalendarDates(ProcessorBase):
    filename = 'calendar_dates.txt'
    required = False

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        return row['service_id'] in filters.services


class ProcessFrequencies(ProcessorBase):
    filename = 'frequencies.txt'
    required = False

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        return row['trip_id'] in filters.trips


class ProcessStopTimes(ProcessorBase):
    filename = 'stop_times.txt'

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        if row['trip_id'] in filters.trips:
            filters.stops.add(row['stop_id'])
            return True
        return False


class ProcessStops(ProcessorBase):
    filename = 'stops.txt'

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        return row['stop_id'] in filters.stops


class ProcessTransfers(ProcessorBase):
    filename = 'transfers.txt'
    required = False

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        return (
            (not row['from_stop_id'] or row['from_stop_id'] in filters.stops)
            and (not row['to_stop_id'] or row['to_stop_id'] in filters.stops)
            and (not row['from_route_id'] or
                 row['from_route_id'] in filters.routes)
            and (not row['to_route_id'] or
                 row['to_route_id'] in filters.routes)
            and (not row['from_trip_id'] or
                 row['from_trip_id'] in filters.trips)
            and (not row['to_trip_id'] or
                 row['to_trip_id'] in filters.trips)
        )


class ProcessFeedInfo(ProcessorBase):
    filename = 'feed_info.txt'
    required = False

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        return True


class ProcessFareAttributes(ProcessorBase):
    filename = 'fare_attributes.txt'
    required = False

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        if filters.in_agencies(row['agency_id']):
            filters.fares.add(row['fare_id'])
            return True
        return False


class ProcessFareRules(ProcessorBase):
    filename = 'fare_rules.txt'
    required = False

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        return row['fare_id'] in filters.fares


class ProcessStopAreas(ProcessorBase):
    filename = 'stop_areas.txt'
    required = False

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        return row['stop_id'] in filters.stops


class ProcessRouteNetworks(ProcessorBase):
    filename = 'route_networks.txt'
    required = False

    def process(self, row: dict[str, str], filters: Filters) -> bool:
        return row['route_id'] in filters.routes


processors = [
    ProcessFeedInfo(),
    ProcessAgencies(),
    ProcessRoutes(),
    ProcessTrips(),
    ProcessShapes(),
    ProcessCalendar(),
    ProcessCalendarDates(),
    ProcessFrequencies(),
    ProcessStopTimes(),
    ProcessStops(),
    ProcessTransfers(),
    ProcessFareAttributes(),
    ProcessFareRules(),
    ProcessStopAreas(),
    ProcessRouteNetworks(),
]

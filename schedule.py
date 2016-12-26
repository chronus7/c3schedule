#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""schedule.py

Interface to the 33C3 lecture schedule

- Dave J (https://github.com/chronus7)
"""
import argparse
from collections import defaultdict
import datetime
import enum
import json
import os
import re
import textwrap
from urllib.request import urlopen
from urllib.error import URLError

DATEFMT = '%Y-%m-%d'
DATETIMEFMT = '%Y-%m-%dT%H:%M:%S+01:00'     # %z does not provide the colon
TIMEFMT = '%H:%M'

REMOTE = 'https://fahrplan.events.ccc.de/congress/2016/Fahrplan/schedule.json'
LOCAL = 'schedule.json'
SELECTED = 'selected.lst'


class GenericObject(dict):
    def __init__(self, obj: dict):
        super().__init__(self)
        self.update(obj)

    def update(self, data):
        # TODO would be nice to also go into lists
        for k, v in data.items():
            if isinstance(v, dict):
                v = GenericObject(v)
            self[k] = v

    def __getattr__(self, item):
        if item in self:
            return self[item]
        return AttributeError


class Schedule:
    events = []
    ids = {}
    days = defaultdict(list)
    rooms = defaultdict(list)
    tracks = defaultdict(list)
    speakers = defaultdict(list)

    def __init__(self, data: GenericObject):
        self._data = data.schedule

        self._prepare()

    def _prepare(self):
        """Prepare data for easy and correct usage"""
        self.version = self._data.version
        conf = self._data.conference
        self.title = conf.title
        self.short = conf.acronym
        # 2016-12-27
        self.start = datetime.datetime.strptime(conf.start, DATEFMT).date()
        # 2016-12-30
        self.end = datetime.datetime.strptime(conf.end, DATEFMT).date()

        for dayobj in conf.days:
            dayobj = GenericObject(dayobj)
            day_date = datetime.datetime.strptime(dayobj.date, DATEFMT).date()

            for room, evlist in dayobj.rooms.items():
                for evobj in evlist:
                    evobj = GenericObject(evobj)
                    evobj.date = datetime.datetime.strptime(evobj.date,
                                                            DATETIMEFMT)
                    evobj.start = datetime.datetime.strptime(evobj.start,
                                                             TIMEFMT).time()
                    dur = datetime.datetime.strptime(evobj.duration,
                                                     TIMEFMT).time()
                    evobj.duration = datetime.timedelta(hours=dur.hour,
                                                        minutes=dur.minute)
                    evobj.end = evobj.date + evobj.duration
                    evobj.persons = [i['public_name'] for i in evobj.persons]
                    # adding
                    self.events.append(evobj)
                    self.ids[evobj.id] = evobj
                    self.days[day_date].append(evobj)
                    self.rooms[room].append(evobj)
                    self.tracks[evobj.track].append(evobj)
                    for p in evobj.persons:
                        self.speakers[p] = evobj
        # sorting
        self.events.sort(key=lambda x: x.date)

    @property
    def rooms_list(self):
        # ordered, as in webinterface
        return ['Saal 1', 'Saal 2', 'Saal G', 'Saal 6']
        # return sorted(self.rooms.keys())

    @property
    def days_list(self):
        return sorted(self.days.keys())

    @property
    def speakers_list(self):
        return sorted(self.speakers.keys())

    @property
    def tracks_list(self):
        return sorted(self.tracks.keys())

    def at(self, time: datetime.datetime, room=None, track=None) -> list:
        """Return a list of events at the given timepoint"""
        res = [ev for ev in self.days[time.date()]
               if ev.date <= time <= ev.end]
        if room is not None:
            res = [ev for ev in res if ev.room == room]
        if track is not None:
            res = [ev for ev in res if ev.track == track]
        return res

    def next(self, time: datetime.datetime, room=None, track=None) -> list:
        """Return a list of upcoming events"""
        at = self.at(time)
        if not at:
            return []
        end = min(e.end for e in at)
        return self.at(end + datetime.timedelta(minutes=15), room, track)

    def __repr__(self):
        # replace with daysLeft
        return '<{} "{}" ({}) [{} events]>'.format(self.__class__.__name__,
                                                   self.short, self.version,
                                                   len(self.events))


class Color(str, enum.Enum):
    Neutral = '\033[m'
    Grey = '\033[1;30m'
    Red = '\033[1;31m'
    Green = '\033[1;32m'
    Yellow = '\033[1;33m'
    Blue = '\033[1;34m'
    Magenta = '\033[1;35m'
    Cyan = '\033[1;36m'
    White = '\033[1;37m'

    Title = '\033[37m'
    Selected = '\033[7;33m'
    Hilighted = '\033[7;38m'
    # Title = Hilighted

    @classmethod
    def get(cls, index):
        return list(cls.__members__.values())[index]

    @classmethod
    def nocolor(cls):
        d = {k: '' for k in cls.__members__}

        def g(c, i):
            return ''
        d['get'] = g

        def c(c):
            global Color
            Color = cls
        d['color'] = c
        global Color
        Color = type(cls.__name__, (dict, ), d)(d)

    def __str__(self):
        return self.value


class Display:
    HL, VL = '-', '|'
    TL = TR = BL = BR = '+'
    PREFIX_FORMAT = '{:>5s}{}'
    HTML_REGEX = re.compile('<.+?>')    # TODO really not good ;)

    def __init__(self, schedule: Schedule, steps: datetime.timedelta=None,
                 ascii: bool=False):
        self.schedule = schedule
        if steps is None or steps <= datetime.timedelta(0):
            steps = datetime.timedelta(minutes=15)
        self.step_size = steps
        if not ascii:
            self.HL, self.VL = '\u2500', '\u2502'
            self.TL, self.TR = '\u250C', '\u2510'
            self.BL, self.BR = '\u2514', '\u2518'
        self.WIDTH, self.HEIGHT = os.get_terminal_size()
        self.WIDTH -= 1     # for those fckng terminal errors etc.

    def parallel(self, events: list,
                 rooms: list=None, selected: set=set()) -> str:
        start_time = min(ev.date for ev in events)
        end_time = max(ev.end for ev in events)

        step_size = self.step_size          # easier access
        if rooms is None:
            rooms = self.schedule.rooms_list
        if not isinstance(rooms, list):
            rooms = [rooms]
        lines = []

        # add rooms (header)
        l1 = self.PREFIX_FORMAT.format('', self.VL)
        l2 = self.PREFIX_FORMAT.format(self.HL * 5, self.VL)
        w = self.WIDTH - len(l1) - 1
        rw = w // len(rooms)
        l1 += self.VL.join('{:^{}}'.format(r, rw) for r in rooms) + self.VL
        l2 += self.VL.join(self.HL * rw for _ in rooms) + self.VL
        lines.append(l1)
        lines.append(l2)

        timelines = defaultdict(list)

        # build events for rooms
        for i, room in enumerate(rooms):
            room_events = sorted((ev for ev in events if ev.room == room),
                                 key=lambda x: x.date)
            for j, event in enumerate(room_events):
                # wrap title
                possible_lines = ['{}{:{}}{}'.format(Color.Selected if
                                                     event.id in selected else
                                                     Color.Title, l, rw,
                                                     Color.Neutral) for l in
                                  textwrap.wrap('{} ({})'.format(event.title,
                                                                 event.id),
                                                rw)]
                # colourful track
                possible_lines.append('{}{:{}}{}'.format(
                    self.color(event.track), event.track, rw, Color.Neutral))
                # persons
                possible_lines += textwrap.wrap(', '.join(event.persons), rw)
                # end
                while len(possible_lines) < event.duration // step_size:
                    possible_lines.append('')
                possible_lines.append(self.HL * rw)

                current = event.date
                # adjust end to allow for more info
                end = event.end
                if j < len(room_events) - 1:
                    upcoming = room_events[j + 1]
                    if event.end == upcoming.date:
                        end = event.end - step_size

                # select writable lines
                index = 0
                while current <= end:
                    line = ' ' * rw
                    if index < len(possible_lines):
                        line = possible_lines[index]
                    timelines[current].append(line)
                    index += 1
                    current += step_size

            # add empty lines
            for k, v in sorted(timelines.items()):
                if len(v) < i + 1:
                    v.append('')

        # set up default times
        current = start_time
        while current <= end_time:
            if current not in timelines:
                timelines[current] = []
            current += step_size

        # set up prefix
        in_set = {30}
        if step_size < datetime.timedelta(minutes=15):
            in_set = {15, 30, 45}
        for k, v in sorted(timelines.items()):
            prefix = ''
            if k.minute == 0:
                prefix = k.strftime(TIMEFMT)
            elif k.minute in in_set:
                prefix = k.strftime(':%M')
            prefix = self.PREFIX_FORMAT.format(prefix, self.VL)
            v.insert(0, prefix)

        # fill lines and join to strings
        for _, v in sorted(timelines.items()):
            while len(v) < len(rooms) + 1:
                v.append('')
            lines.append(v[0] + self.VL.join('{:{}}'.format(p, rw)
                                             for p in v[1:]) + self.VL)

        return '{}\n'.format(Color.Neutral).join(lines)

    def event(self, event: GenericObject,
              short: bool=False, selected: set=set()) -> str:
        # {T}title{n} (id)
        # --- subtitle
        # {t}track{n} // room // language
        # day [<start> -<dur>- <end>]
        # persons
        # abstract
        # description
        width = self.WIDTH - 2

        lines = [
            '{}{}{} ({})'.format(Color.Selected if event.id in selected
                                 else Color.Title,
                                 event.title,
                                 Color.Neutral,
                                 event.id),
            '--- {}'.format(event.subtitle),
            '{}{}{} // {} // {}'.format(self.color(event.track),
                                        event.track,
                                        Color.Neutral,
                                        event.room,
                                        event.language),
            '{} {} [{} <{}> {}]'.format(event.date.strftime('%a'),
                                        event.date.strftime(DATEFMT),
                                        event.date.strftime(TIMEFMT),
                                        datetime.datetime.fromtimestamp(
                                            event.duration.seconds)
                                        .strftime(TIMEFMT),
                                        event.end.strftime(TIMEFMT)),
            ', '.join(event.persons)
        ]
        if not short:
            lines.append('')
            abstract = '{}ABSTRACT{} '.format(Color.Grey, Color.Neutral)
            abstract += self.HTML_REGEX.sub('', event.abstract)
            for line in abstract.split('\n'):
                lines += textwrap.wrap(line, width)
            lines.append('')
            description = '{}DESCRIPTION{} '.format(Color.Grey, Color.Neutral)
            description += self.HTML_REGEX.sub('', event.description)
            for line in description.split('\n'):
                lines += textwrap.wrap(line, width)

        l = [self.TL + self.HL * width + self.TR]
        for line in lines:
            tmp = re.sub('\033[[0-9;]*m', '', line)
            w = width + len(line) - len(tmp)
            l.append('{}{:{}}{}'.format(self.VL, line, w, self.VL))
        l.append(self.BL + self.HL * width + self.BR)
        lines = l

        return '{}\n'.format(Color.Neutral).join(lines)

    def color(self, track: str) -> Color:
        index = self.schedule.tracks_list.index(track)
        return Color.get((index % (len(Color) - 1)) + 1)


def retrieve(offline=False) -> GenericObject:
    """Retrieve data (either remote or local)"""
    data = None
    if not offline:
        try:
            with urlopen(REMOTE) as response:
                code = response.getcode()
                if code == 200:
                    data = json.loads(response.read().decode())
        except URLError as err:
            pass
    if data:
        with open(LOCAL, 'w') as f:
            json.dump(data, f)
    else:
        with open(LOCAL, 'r') as f:
            data = json.load(f)
    return GenericObject(data)


def main():
    ap = argparse.ArgumentParser(
        description='Interface to the 33C3 Fahrplan (schedule).')
    # nocolors
    # ascii
    # verbose
    # offline
    # steps
    # event-listing
    # selected: select, show selected (no colors useless here)
    # rooms
    # tracks
    # time: [[[[[year] month] day] hour] minute]
    # next
    # day
    # all
    # one
    ap.add_argument('-a', '--ascii', action='store_true',
                    help='Print ascii symbols instead of UTF-8 ones.')
    ap.add_argument('-n', '--nocolor', action='store_true',
                    help='Print no colors. Boring.')
    ap.add_argument('-o', '--offline', action='store_true',
                    help='Do not try to pull the schedule from the internet.')
    ap.add_argument('-v', '--verbose', action='store_true',
                    help='Print additional info about the schedule.')
    ap.add_argument('-i', '--interval', type=int, metavar='MIN',
                    help='Interval steps between the lines. '
                    'Default is 15 minutes.')
    ap.add_argument('-e', '--events', choices={'short', 'full'},
                    help='Print events individually instead a timetable.')

    # selected
    ap.add_argument('-s', '--select', nargs='+', metavar='ID', type=int,
                    help='Store the given ids as selected ones.')
    ap.add_argument('--selectfile', default=SELECTED,
                    help='The file to store the selected events in.')
    ap.add_argument('-S', '--selected', action='store_true',
                    help='Show only selected events.')

    # filter
    ap.add_argument('-r', '--rooms', nargs='+', metavar='ROOM',
                    choices={'Saal 1', 'Saal 2', 'Saal G', 'Saal 6'},
                    help='Rooms to filter for.')
    ap.add_argument('-t', '--tracks', nargs='+', metavar='TRACK',
                    help='Tracks (categories) to filter for.')
    ap.add_argument('-d', '--date', '--time', nargs='+', type=int,
                    help='The time to filter for. Default is now. '
                    '[[[[[year] month] day] hour] minute]')

    # method
    ma = ap.add_mutually_exclusive_group()
    ma.add_argument('-N', '--next', action='store_true',
                    help='Show upcoming events instead of currently running.')
    ma.add_argument('-D', '--day', action='store_true',
                    help='Show the complete day instead of only a time-slot.')
    ma.add_argument('-A', '--all', action='store_true',
                    help='Show all events (in regards to time; '
                    'other filters still apply).')
    ma.add_argument('-O', '--one', '--event', type=int, metavar='ID',
                    help='Show only the given event (ignores other filter).')

    # == parse args ======
    args = ap.parse_args()
    # ====================

    # store selected ids
    if args.select:
        with open(args.selectfile, 'a') as f:
            for i in args.select:
                print(i, file=f)

    # reading selected
    selected = set()
    if os.path.exists(args.selectfile):
        with open(args.selectfile, 'r') as f:
            selected = {int(i.strip()) for i in f.readlines()}

    # nocolor
    if args.nocolor:
        Color.nocolor()

    # set time
    time = datetime.datetime.now()
    dt_args = ['year', 'month', 'day', 'hour', 'minute']
    dt_vals = {k: getattr(time, k, 0) for k in dt_args}
    if args.date:
        n = dict(zip(reversed(dt_args), reversed(args.date)))
        dt_vals.update(n)
    time = datetime.datetime(*(dt_vals[i] for i in dt_args))

    # set interval
    interval = datetime.timedelta(minutes=15)
    if args.interval:
        interval = datetime.timedelta(minutes=args.interval)

    # get schedule
    schedule = Schedule(retrieve(args.offline))

    # verbose
    if args.verbose:
        print('[{0.short}] {0.title} ({0.version})'.format(schedule))
        # prefix = ' ' * (2 + len(schedule.short))
        prefix = ''
        print(prefix, 'days:', ', '.join(d.strftime('%a ' + DATEFMT) for d in
                                         schedule.days_list))
        print(prefix, 'rooms:', ', '.join(schedule.rooms_list))
        print(prefix, 'tracks:', ', '.join(schedule.tracks_list))
        print(prefix, '{:3d} events'.format(len(schedule.events))),
        print(prefix, '{:3d} speakers'.format(len(schedule.speakers_list)))

    # display
    display = Display(schedule, interval, args.ascii)

    events = []
    if args.one:
        events = [schedule.ids[args.one]]
    elif args.next:
        events = schedule.next(time, args.rooms, args.tracks)
    elif args.day:
        events = schedule.days[time.date()]
    elif args.all:
        events = schedule.events
    else:
        events = schedule.at(time, args.rooms, args.tracks)
    if args.events:
        for event in events:
            print(display.event(event, args.events == 'short', selected))
    else:
        room_list = args.rooms if args.rooms else schedule.rooms_list
        print(display.parallel(events, room_list, selected))


if __name__ == '__main__':
    main()

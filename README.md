c3schedule
==========

`c3schedule` is a console interface to the 33C3 schedule. It shows you events,
based on the given filters.

- **Views**: The tool supports two different methods to display events.
    1. The default one is the timetable-view as seen [here](#timetable). The
       columns are adjusted to the available space (can be changed with the
       interval (`-i`) option). As of such, some information might not be
       visible.
    2. The other one is an individual view, where the event is displayed in more
       or less detail (depending on the value of `-e`; use `-O <id> -e full` for
       all information about that one event). See [here](#individual) for
       examples.
- **Date**: The tool's most important filter is the time (`-d`). Per default the
  current time is used and all parallel running lectures are listed. Options
  like `-d`, `-N`, `-D`, `-A` influence that time. The options for `-d` are
  nested: `[[[[[year] month] day] hour] minute]`. So to select the second day,
  while being in December, one could write `-d 28 11 00 -D`.
- **Filter**: There are different options to filter the output. This includes
  date/time, rooms, tracks (categories) and selections.
- **Selection**: The tool lets you select/mark different events, so they can be
  highlighted, when viewed. The events have to selected via their id (seen
  behind their title) with the option `-s` (or alternatively you can write them
  into the `SELECFILE` by yourself). To see all selected items, use `-SA`.
- **Offline**: Per default, `c3schedule` tries to pull the schedule from the net
  and stores it locally. If the network connection fails, it uses the locally
  stored version. Use the `-o` flag to use the local file directly.

Installation
------------

```shell
git clone https://github.com/chronus7/c3schedule
cd c3schedule
./schedule.py -h
```

Usage
-----

```
usage: schedule.py [-h] [-a] [-n] [-o] [-v] [-i MIN] [-e {full,short}]
                   [-s ID [ID ...]] [--selectfile SELECTFILE] [-S]
                   [-r ROOM [ROOM ...]] [-t TRACK [TRACK ...]]
                   [-d DATE [DATE ...]] [-N | -D | -A | -O ID]

Interface to the 33C3 Fahrplan (schedule).

optional arguments:
  -h, --help            show this help message and exit
  -a, --ascii           Print ascii symbols instead of UTF-8 ones.
  -n, --nocolor         Print no colors. Boring.
  -o, --offline         Do not try to pull the schedule from the internet.
  -v, --verbose         Print additional info about the schedule.
  -i MIN, --interval MIN
                        Interval steps between the lines. Default is 15
                        minutes.
  -e {full,short}, --events {full,short}
                        Print events individually instead a timetable.
  -s ID [ID ...], --select ID [ID ...]
                        Store the given ids as selected ones.
  --selectfile SELECTFILE
                        The file to store the selected events in.
  -S, --selected        Show only selected events.
  -r ROOM [ROOM ...], --rooms ROOM [ROOM ...]
                        Rooms to filter for.
  -t TRACK [TRACK ...], --tracks TRACK [TRACK ...]
                        Tracks (categories) to filter for.
  -d DATE [DATE ...], --date DATE [DATE ...], --time DATE [DATE ...]
                        The time to filter for. Default is now. [[[[[year]
                        month] day] hour] minute]
  -N, --next            Show upcoming events instead of currently running.
  -D, --day             Show the complete day instead of only a time-slot.
  -A, --all             Show all events (in regards to time; other filters
                        still apply).
  -O ID, --one ID, --event ID
                        Show only the given event (ignores other filter).
```

Timetable
---------

```
# 95 columns
     │       Saal 1        │       Saal 2        │       Saal G        │       Saal 6        │
─────│─────────────────────│─────────────────────│─────────────────────│─────────────────────│
  :30│The Global           │Reverse engineering  │What could possibly  │Everything you always│
     │Assassination Grid   │Outernet (8399)      │go wrong with <insert│wanted to know about │
12:00│(8425)               │Hardware & Making    │x86 instruction      │Certificate          │
     │Ethics, Society & .. │Daniel Estévez       │here>? (8044)        │Transparency (8167)  │
  :30│Cian Westmoreland    │─────────────────────│Security             │Security             │
```

```
# 119 columns
     │          Saal 1           │          Saal 2           │          Saal G           │          Saal 6           │
─────│───────────────────────────│───────────────────────────│───────────────────────────│───────────────────────────│
  :30│The Global Assassination   │Reverse engineering        │What could possibly go     │Everything you always      │
     │Grid (8425)                │Outernet (8399)            │wrong with <insert x86     │wanted to know about       │
12:00│Ethics, Society & Politics │Hardware & Making          │instruction here>? (8044)  │Certificate Transparency   │
     │Cian Westmoreland          │Daniel Estévez             │Security                   │(8167)                     │
  :30│───────────────────────────│───────────────────────────│Clémentine Maurice, Moritz │Security                   │
```

Individual
----------

```
# -e short
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│The Global Assassination Grid (8425)                                                        │
│--- The Infrastructure and People behind Drone Killings                                     │
│Ethics, Society & Politics // Saal 1 // en                                                  │
│Tue 2016-12-27 [11:30 <01:00> 12:30]                                                        │
│Cian Westmoreland                                                                           │
└────────────────────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│Everything you always wanted to know about Certificate Transparency (8167)                  │
│--- (but were afraid to ask)                                                                │
│Security // Saal 6 // en                                                                    │
│Tue 2016-12-27 [11:30 <01:00> 12:30]                                                        │
│Martin Schmiedecker                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```
```
# -e full
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│The Global Assassination Grid (8425)                                                                                │
│--- The Infrastructure and People behind Drone Killings                                                             │
│Ethics, Society & Politics // Saal 1 // en                                                                          │
│Tue 2016-12-27 [11:30 <01:00> 12:30]                                                                                │
│Cian Westmoreland                                                                                                   │
│                                                                                                                    │
│ABSTRACT As they say in the Air Force, ‚No comms no bombs‘,  – A technician’s insight into the invisible            │
│networks governing military drones and the quest for accountability                                                 │
│                                                                                                                    │
│DESCRIPTION Cian has spent a great deal of time thinking about the issues of responsibility in, and how             │
│communications technology has been used to distance people from the act of killing. Rising superpowers around the   │
│world are working day and night to build the next stealth drone that can penetrate air defense systems. The         │
│automation of target selection processes, navigation and control are incentivized by the vulnerability posed by the │
│signals drones rely upon to operate.                                                                                │
│A drone is merely a networked platform that moves across a grid, much like a mouse. It’s „mind“ is distributed among│
│dozens of individuals located around the globe, controlling separate parts of the the overall mission using data    │
│derived from surveillance, and processed using algorithms that may or may not reflect the reality on the ground.    │
│Cian challenges the common notion that drones are the most effective tool for combatting terrorism and seeks to     │
│explain why this is so, as well as how mistakes happen. The automation of these processes will further take the     │
│responsibility out of the hands of individuals and disperse them further. This calls for a new level of ethical     │
│considerations and accountability mechanisms to be developed.                                                       │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

<!--
vim: ft=markdown:tw=80
-->

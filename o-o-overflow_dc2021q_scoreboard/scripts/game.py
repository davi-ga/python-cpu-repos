#!/usr/bin/env python3
import datetime
import sys
from contextlib import contextmanager
from time import sleep

import boto3
import psycopg2
from botocore.config import Config

DB_HOST = "sb-{environment}.cgrvtkkg9riu.us-east-2.rds.amazonaws.com"
ENVIRONMENT = "production"
START_TIME = datetime.datetime(2021, 5, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)


def get_db_password():
    client = boto3.client("ssm", config=Config(region_name="us-east-2"))
    return client.get_parameter(Name="/production/db_password", WithDecryption=True)[
        "Parameter"
    ]["Value"]


def main(argv):
    with psql_connection() as psql:
        if len(argv) == 1:
            stats(psql)
        elif argv[1] == "cat":
            categories(psql)
        elif argv[1] == "timeline":
            timeline(psql)
        elif argv[1] == "solcount":
            solcount(psql)
        elif argv[1] == "challs":
            challs_table(psql)
        elif argv[1] == "graph":
            graph(psql)
        elif argv[1] == "teams":
            teams_table(psql)
        elif argv[1] == "cinfo":
            if len(argv) != 3:
                print("You need to specify one challenge id")
                sys.exit(1)
            info_chall(psql, argv[2])
        elif argv[1] == "log":
            if len(argv) < 3:
                n = 30
            else:
                n = int(argv[2])
            log(psql, n)
        elif argv[1] == "tinfo":
            if len(argv) != 3:
                print("You need to specify one team id")
                sys.exit(1)
            info_team(psql, argv[2])
        elif argv[1] == "blood":
            blood(psql)
        else:
            print("\nUse:")
            print(
                " %s                     \x1b[33m# Generic Info about the game\x1b[0m"
                % argv[0]
            )
            print(
                " %s challs              \x1b[33m# Info about open challengs\x1b[0m"
                % argv[0]
            )
            print(
                " %s log <threshold>     \x1b[33m# Tail -f the solutions\x1b[0m"
                % argv[0]
            )
            print(
                " %s teams               \x1b[33m# Info about all teams\x1b[0m"
                % argv[0]
            )
            print(
                " %s cinfo <chall>       \x1b[33m# Detailed info about one chall\x1b[0m"
                % argv[0]
            )
            print(
                " %s tinfo <team>        \x1b[33m# Provides info about one team\x1b[0m"
                % argv[0]
            )
            print(
                " %s timeline            \x1b[33m# Prints a hourly timeline of the game\x1b[0m"
                % argv[0]
            )
            print(" %s blood               \x1b[33m# First blood \x1b[0m" % argv[0])
            print(" %s solcount            \x1b[33m# Solutions count \x1b[0m" % argv[0])
            print(
                " %s cat                 \x1b[33m# List chaallenges by category \x1b[0m"
                % argv[0]
            )
            print("")
            sys.exit(0)

    return 0


def diff_string(diff):
    last = ""
    diff_days = diff.days
    diff_m = diff.seconds // 60
    diff_h = diff_m // 60
    if diff_days > 0:
        last += "%dd " % diff_days
    if int(diff_h) > 0:
        diff_m %= 60
        last += "%dh %dm" % (diff_h, diff_m)
    else:
        last += "%dm" % diff_m
    return last


@contextmanager
def psql_connection():
    psql = psycopg2.connect(
        dbname="scoreboard",
        host=DB_HOST.format(environment=ENVIRONMENT),
        password=get_db_password(),
        user="scoreboard",
    )
    try:
        yield psql
    finally:
        psql.close()


def log(psql, maxn):
    with psql.cursor() as cursor2:
        last = 0
        challs = {}
        cursor2.execute(
            "SELECT solves.date_created, team_name, challenge_id FROM solves,users WHERE solves.user_id = users.id order by solves.date_created"
        )
        for time, team, chall in cursor2.fetchall():
            if chall not in challs:
                challs[chall] = 0
            challs[chall] += 1
            if challs[chall] == 1:
                print("\x1b[31m >>> FIRST BLOOD! %s from %s <<<\x1b[0m" % (chall, team))
            elif challs[chall] <= maxn:
                print(
                    "%s | %s solved %s (solved %d times)"
                    % (time.strftime("%b-%d %H:%M:%S"), team, chall, challs[chall])
                )
            if challs[chall] == maxn:
                print(
                    "\x1b[32m> %s reached %d solves. It wont be printed anymore \x1b[0m"
                    % (chall, maxn)
                )
        last = time
        while True:
            cursor2.execute(
                "SELECT solves.date_created, team_name, challenge_id FROM solves,users WHERE solves.date_created > '%s' and solves.user_id = users.id order by solves.date_created"
                % last
            )
            for time, team, chall in cursor2.fetchall():
                if chall not in challs:
                    challs[chall] = 0
                challs[chall] += 1
                if challs[chall] == 1:
                    print(
                        "\x1b[31m >>> FIRST BLOOD! %s from %s <<<\x1b[0m"
                        % (chall, team)
                    )
                elif challs[chall] <= maxn:
                    print(
                        "%s | %s solved %s (solved %d times)"
                        % (time.strftime("%b-%d %H:%M:%S"), team, chall, challs[chall])
                    )
                if challs[chall] == maxn:
                    print(
                        "\x1b[32m> %s reached %d solves. It wont be printed anymore \x1b[0m"
                        % (chall, maxn)
                    )
            last = time
            sleep(5)


def solcount(psql):
    with psql.cursor() as cursor2:
        cursor2.execute(
            "SELECT team_name, count(challenge_id) FROM solves,users WHERE solves.user_id = users.id group by team_name;"
        )
        count = {}
        for team, chall in cursor2.fetchall():
            if chall not in count:
                count[chall] = 0
            count[chall] += 1
        print("Solved   Teams")
        for c in sorted(count.keys(), reverse=True):
            print("\x1b[32m %2d \x1b[0m       %s" % (c, count[c]))


def info_team(psql, team):
    with psql.cursor() as cursor2:
        cursor2.execute("SELECT id FROM users WHERE team_name=%s;", (team,))
        team_id = cursor2.fetchone()
        if not team_id:
            print("  Error: team %s not found" % team)
            sys.exit(2)
        else:
            team_id = team_id[0]
    now = datetime.datetime.now(datetime.timezone.utc)
    print("")
    print("\x1b[32m----------------------------------------------------------\x1b[0m")
    print("\x1b[32m          Challenge       Wrong Attempts     Solved \x1b[0m ")
    with psql.cursor() as cursor:
        cursor.execute("SELECT id from challenges;")
        for (name,) in cursor.fetchall():
            with psql.cursor() as cursor2:
                cursor2.execute(
                    "SELECT solves.date_created FROM solves WHERE challenge_id=%s and user_id=%s;",
                    (name, team_id),
                )
                when = cursor2.fetchone()
                if when is None:
                    when = "   -"
                else:
                    diff = now - when[0]
                    when = diff_string(diff)
            with psql.cursor() as cursor2:
                cursor2.execute(
                    "SELECT count(*) FROM submissions WHERE challenge_id=%s and user_id=%s;",
                    (name, team_id),
                )
                wrong = cursor2.fetchone()
                if not wrong or wrong[0] == 0:
                    wrong = "-"
                else:
                    wrong = wrong[0]
            print("\x1b[33m%23s\x1b[0m         %3s          %s" % (name, wrong, when))
    print("\x1b[32m----------------------------------------------------------\x1b[0m")
    print("")


def timeline(psql):
    now = datetime.datetime.now(datetime.timezone.utc)
    start = START_TIME
    slots = [[0, set()] for i in range(49)]
    diff = now - start
    current = int(diff.total_seconds() // 60 // 60)
    print("\x1b[32mHour     Solved      Active Teams\x1b[0m")
    with psql.cursor() as cursor2:
        cursor2.execute("SELECT solves.date_created, user_id FROM solves;")
        for when, who in cursor2.fetchall():
            diff = when - start
            slot = int(diff.total_seconds() // 60 // 60)
            slots[slot][0] += 1
            slots[slot][1].add(who)

    for i in range(len(slots)):
        if i == current:
            print(
                "\x1b[32mNOW>\x1b[0m     %5s          %5s"
                % (slots[i][0], len(slots[i][1]))
            )
        else:
            print(" %2d      %5s          %5s" % (i, slots[i][0], len(slots[i][1])))


def graph(psql):
    print("")
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - START_TIME
    now_pos = int((diff.seconds // 60) / 30)
    print("                          |%s> now" % ("-" * now_pos))
    with psql.cursor() as cursor:
        cursor.execute("SELECT id from challenges;")
        for (name,) in cursor.fetchall():
            with psql.cursor() as cursor2:
                cursor2.execute(
                    "SELECT solves.date_created FROM solves WHERE challenge_id=%s limit 10;",
                    (name,),
                )
                when = cursor2.fetchall()
                first_blood = -1
                ten_solved = -1
                if when:
                    first = when[0][0]
                    diff = first - START_TIME
                    first_blood = int((diff.seconds // 60) / 30)
                    if len(when) > 9:
                        last = when[-1][0]
                        diff = last - START_TIME
                        ten_solved = int((diff.seconds // 60) / 30)
            with psql.cursor() as cursor2:
                cursor2.execute(
                    "SELECT date_created FROM challenges WHERE id=%s;", (name,)
                )
                opentime = cursor2.fetchone()[0]
                diff = opentime - START_TIME
                opentime = int((diff.seconds // 60) / 30)

            if opentime > 0:
                gap = " " * (opentime - 1)
            else:
                gap = ""

            if first_blood == -1:
                print(
                    "\x1b[33m%25s\x1b[0m |%s\x1b[32m[%s\x1b[0m"
                    % (name, gap, "~" * (now_pos - opentime))
                )
            else:
                if first_blood == opentime:
                    if ten_solved >= 0:
                        print(
                            "\x1b[33m%25s\x1b[0m |%s\x1b[31mX%s]\x1b[0m"
                            % (name, gap, "=" * (ten_solved - opentime))
                        )
                    else:
                        print(
                            "\x1b[33m%25s\x1b[0m |%s\x1b[31mX%s\x1b[0m"
                            % (name, gap, "=" * (now_pos - opentime))
                        )
                else:
                    if ten_solved >= 0:
                        print(
                            "\x1b[33m%25s\x1b[0m |%s\x1b[32m[%s\x1b[31mX%s]\x1b[0m"
                            % (
                                name,
                                gap,
                                "~" * (first_blood - opentime),
                                "=" * (ten_solved - first_blood),
                            )
                        )
                    else:
                        print(
                            "\x1b[33m%25s\x1b[0m |%s\x1b[32m[%s\x1b[31mX%s\x1b[0m"
                            % (
                                name,
                                gap,
                                "~" * (first_blood - opentime),
                                "=" * (now_pos - opentime),
                            )
                        )

    print("")


def categories(psql):
    print("")
    print("\x1b[32m           Name            : Categories\x1b[0m")
    print(
        "\x1b[32m-----------------------------------------------------------------\x1b[0m"
    )
    cats_count = {}
    with psql.cursor() as cursor:
        cursor.execute("SELECT id from challenges order by date_created;")
        for (name,) in cursor.fetchall():
            with psql.cursor() as cursor2:
                cursor2.execute("SELECT * FROM challenges WHERE id=%s;", (name,))
                cat = [
                    n.strip()
                    for n in cursor2.fetchone()[-1].split(",")
                    if not n.strip().startswith("-")
                ]
                for c in cat:
                    if c not in cats_count:
                        cats_count[c] = 0
                    cats_count[c] += 1
                print("\x1b[33m%25s\x1b[0m  :  %s" % (name, ", ".join(cat)))
    print(
        "\x1b[32m-----------------------------------------------------------------\x1b[0m"
    )
    for c in cats_count:
        print("                        %2d - \x1b[33m%s\x1b[0m" % (cats_count[c], c))
    print("")


def info_chall(psql, chall):
    now = datetime.datetime.now(datetime.timezone.utc)
    with psql.cursor() as cursor2:
        cursor2.execute("SELECT date_created FROM challenges WHERE id=%s;", (chall,))
        opentime = cursor2.fetchone()
        if not opentime:
            print("  Error: challenge not found or not yet open")
            sys.exit(2)
        else:
            opentime = opentime[0]
    print("")
    print("\x1b[32m----------------------------------\x1b[0m")
    diff = now - opentime
    when = diff_string(diff)
    print("\x1b[32m Open Time:\x1b[0m %s ago" % when)
    with psql.cursor() as cursor2:
        cursor2.execute(
            "SELECT solves.date_created, team_name FROM solves,users WHERE solves.user_id = users.id and challenge_id=%s;",
            (chall,),
        )
        solvedby = cursor2.fetchall()
        if len(solvedby) == 0:
            print("\x1b[32m Solved by:\x1b[0m no one yet")
        else:
            solvedby.sort(key=lambda x: x[0])
            print("\x1b[32m Solved by:\x1b[0m %d teams" % len(solvedby))
            print("\x1b[32m First Solved by:\x1b[0m %s" % solvedby[0][1])
            diff = solvedby[0][0] - opentime
            when = diff_string(diff)
            print("\x1b[32m                 \x1b[0m %s after it was open" % when)
            print("\x1b[32m Last 3 teams that solved it:\x1b[0m")
            for solver in solvedby[-3:][::-1]:
                diff = now - solver[0]
                when = diff_string(diff)
                print("      %s, %s ago" % (solver[1], when))

    with psql.cursor() as cursor2:
        cursor2.execute(
            "SELECT submissions.date_created, team_name, flag FROM submissions,users WHERE submissions.user_id = users.id and challenge_id=%s;",
            (chall,),
        )
        errors = cursor2.fetchall()
        if len(errors) == 0:
            print("\x1b[32m Wrong Flag Submitted:\x1b[0m none")
        else:
            errors.sort(key=lambda x: x[0])
            print("\x1b[32m Wrong Flag Submitted:\x1b[0m %d" % len(errors))
            print("\x1b[32m Last 20 wrong submissions:\x1b[0m")
            for when, team, flag in errors[-20:][::-1]:
                # for when, team, flag in errors[::-1]:
                diff = now - when
                when = diff_string(diff)
                print("      '%s' from %s, %s ago" % (flag, team, when))
    print("\x1b[32m----------------------------------\x1b[0m")
    print("")


def challs_table(psql):
    print("")
    print(
        "\x1b[32m           Name            : Status   Solved  Wrong    Last  Open Since\x1b[0m"
    )
    print(
        "\x1b[32m-----------------------------------------------------------------\x1b[0m"
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    with psql.cursor() as cursor:
        cursor.execute("SELECT id from challenges order by date_created;")
        for (name,) in cursor.fetchall():
            with psql.cursor() as cursor2:
                cursor2.execute(
                    "SELECT max(solves.date_created), count(user_id) FROM solves WHERE challenge_id=%s;",
                    (name,),
                )
                last, tot = cursor2.fetchone()
            with psql.cursor() as cursor2:
                cursor2.execute(
                    "SELECT count(*) FROM submissions WHERE challenge_id=%s;", (name,)
                )
                (wrong,) = cursor2.fetchone()
            if last is None:
                last = "   -"
            else:
                diff = now - last
                last = diff_string(diff)
            with psql.cursor() as cursor2:
                cursor2.execute(
                    "SELECT date_created FROM challenges WHERE id=%s;", (name,)
                )
                openfrom = "X"
                opentime = cursor2.fetchone()[0]
                diff = now - opentime
                openfrom = diff_string(diff)
            if wrong == 0:
                wrong = "-"
            if tot == 0:
                tot = "-"
            print(
                "\x1b[33m%25s\x1b[0m  :  OPEN    %4s    %5s %7s  %10s"
                % (name, tot, wrong, last, openfrom)
            )

    with psql.cursor() as cursor:
        cursor.execute("SELECT id from unopened_challenges;")
        for name in cursor.fetchall():
            print("%25s  :  CLOSE      -        -       -" % name)
    print("")


def blood(psql):
    with psql.cursor() as cursor:
        # cursor.execute('SELECT id,team_name FROM users;')
        # for (team_id,team_name) in cursor.fetchall():
        #    print ('ID: %s, team: %s' % (team_id, team_name))
        cursor.execute("SELECT id from challenges order by date_created;")
        for chall in cursor.fetchall():
            name = chall[0]
            with psql.cursor() as cursor2:
                cursor2.execute(
                    "SELECT date_created FROM challenges WHERE id=%s;", (chall,)
                )
                opentime = cursor2.fetchone()
                if not opentime:
                    continue
                opentime = opentime[0]
                cursor2.execute(
                    "SELECT solves.date_created, team_name FROM solves,users WHERE solves.user_id = users.id and challenge_id=%s;",
                    (chall,),
                )
                solvedby = cursor2.fetchall()
                if len(solvedby) > 0:
                    solvedby.sort(key=lambda x: x[0])
                    diff = solvedby[0][0] - opentime
                    when = diff_string(diff)
                    print(
                        "\x1b[32m %30s \x1b[0m %s in %s" % (name, solvedby[0][1], when)
                    )


def stats(psql):
    with psql.cursor() as cursor:
        cursor.execute("SELECT count(*) from users;")
        total = cursor.fetchone()[0]

    with psql.cursor() as cursor:
        cursor.execute("SELECT count(*) from solves;")
        tsolved = cursor.fetchone()[0]

    with psql.cursor() as cursor:
        cursor.execute("SELECT count(distinct(challenge_id)) from solves;")
        usolved = cursor.fetchone()[0]

    with psql.cursor() as cursor:
        cursor.execute("SELECT count(*) from submissions;")
        flags = cursor.fetchone()[0]

    with psql.cursor() as cursor:
        cursor.execute("SELECT count(*) from challenges;")
        open = cursor.fetchone()[0]

    with psql.cursor() as cursor:
        cursor.execute("SELECT count(*) from unopened_challenges;")
        closed = cursor.fetchone()[0]

    with psql.cursor() as cursor:
        cursor.execute("SELECT count(distinct(user_id)) from solves;")
        active = cursor.fetchone()[0]

    with psql.cursor() as cursor:
        cursor.execute("SELECT count(*) as c from solves group by user_id order by c;")
        max_solved = cursor.fetchall()
        if not max_solved:
            max_solved = 0
        else:
            max_solved = max_solved[-1][0]

    now = datetime.datetime.now(datetime.timezone.utc)
    start = START_TIME
    diff = now - start
    diffm = diff.days * 24 * 60 + diff.seconds // 60
    progress = diffm * 100 / (48 * 60)
    diffs = diff_string(now - start)
    print("")
    print("\x1b[32m----------------------------------\x1b[0m")
    print("\x1b[32m Game Time\x1b[0m:           %7s (%d%%)" % (diffs, int(progress)))
    print("\x1b[32m Total Teams\x1b[0m:         %7s" % total)
    print("\x1b[32m Active Teams\x1b[0m:        %7s" % active)
    print(
        "\x1b[32m Open Challenges\x1b[0m:     %7s (%d%%)"
        % (open, open * 100 / max(1, open + closed))
    )
    print("\x1b[32m Solved Challenges\x1b[0m:   %7s" % usolved)
    print("\x1b[32m Correct Submissions\x1b[0m: %7s" % tsolved)
    print("\x1b[32m Buffer\x1b[0m:              %7s" % (open - max_solved,))
    print("\x1b[32m Wrong Flags\x1b[0m:         %7s" % flags)
    print("\x1b[32m----------------------------------\x1b[0m")
    print("  (for more options use %s -h )" % sys.argv[0])
    print("")


def teams_table(psql):
    print("")
    print("\x1b[32m           Name       : Solved  Wrong    Last \x1b[0m")
    print("\x1b[32m-------------------------------------------------------\x1b[0m")
    now = datetime.datetime.now(datetime.timezone.utc)
    flags = {}
    with psql.cursor() as cursor:
        cursor.execute(
            "SELECT count(submissions.date_created), team_name FROM submissions, users WHERE submissions.user_id = users.id group by team_name;"
        )
        for count, team in cursor.fetchall():
            flags[team] = count

    with psql.cursor() as cursor:
        # cursor.execute('SELECT solves.date_created, challenge_id, team_name FROM solves, users WHERE solves.user_id = users.id;')
        cursor.execute(
            "SELECT max(solves.date_created), count(challenge_id), team_name FROM solves, users WHERE solves.user_id = users.id group by team_name;"
        )
        for last, solved, team in cursor.fetchall():
            now = datetime.datetime.now(datetime.timezone.utc)
            if last is None:
                last = "   -"
            else:
                diff = now - last
                last = diff_string(diff)
            print(
                "%20s  :  %3s    %3s    %s" % (team, solved, flags.get(team, 0), last)
            )

    print("")


if __name__ == "__main__":
    sys.exit(main(sys.argv))

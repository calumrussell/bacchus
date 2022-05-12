import sqlite3
import json
from datetime import datetime 
import os
import subprocess
import sys

class Schedule:

    def _current_day_hour():
        today = datetime.today()
        day = today.strftime("%A")
        hour = today.strftime("%H")
        minute = today.strftime("%M")
        print(f'System time is: {hour}:{minute}')
        return day, hour

    def is_schedule_active(self):
        day, hour = Schedule._current_day_hour()
        schedule_time = self.schedule['schedule'][day]
        start, end = schedule_time[0], schedule_time[1]
        return int(hour) >= start and int(hour) <= end

    def block_location(self):
        return self.schedule['block_path']

    def load(self):
        with open (self.path, 'r') as f:
            self.schedule = json.loads(f.read())

    def __init__(self, file_path):
        loc = os.getenv('SCHEDULE_LOC')
        if not loc:
            raise Exception("No schedule folder ENV variable")
        else:
            self.path = loc + file_path

class BlockList:

    def get_block_list(self):
        is_active = self.schedule.is_schedule_active()
        res = []
        with open(self.schedule.block_location(), 'r') as f:
            for i, line in enumerate(f):
                res.append(line.strip())
        return is_active, res

    def __init__(self, schedule):
        self.schedule = schedule

class PiHole:

    def _check_block_list(self):
        cur = self.conn.cursor()
        query = """
        select * from domainlist;
        """
        return [row for row in cur.execute(query)]

    ##Domains on the block schedule are managed by this script
    ##Won't enable a blocked site that isn't on active block
    ##Will enable a site that is on active block outside schedule
    def _diff_block_list(self, is_active, domain_list):
        current_block_list = self._check_block_list()
        #{domain: [id, is_enabled]
        current_fast_search = {
            row[2]: (row[0], row[3]) 
            for row 
            in current_block_list
        }
        to_insert = [] #domain string
        to_disable = [] #ids
        to_enable = [] #ids

        if is_active:
            for domain in domain_list:
                if domain in current_fast_search:
                    id, enabled = current_fast_search[domain]
                    if not enabled:
                        print(f'Enabling: {domain}')
                        to_enable.append(id)
                else:
                    print(f'Inserting: {domain}')
                    to_insert.append(domain)
        else:
            for domain in domain_list:
                if domain in current_fast_search:
                    id, enabled = current_fast_search[domain]
                    if enabled:
                        print(f'Disabling: {domain}')
                        to_disable.append(id)
        return to_insert, to_disable, to_enable 

    ##Domain never gets deleted, just deactivated
    ##Grouped for transactions
    def _disable_domains(self, ids):
        cur = self.conn.cursor()
        for id in ids:
            query = """
              UPDATE domainlist
              SET enabled = 0
              WHERE
                id={id}
            """.format(id=id)
            cur.execute(query)
        self.conn.commit()
        return

    def _enable_domains(self, ids):
        cur = self.conn.cursor()
        for id in ids:
            query = """
              UPDATE domainlist
              SET enabled = 1
              WHERE
                id={id}
            """.format(id=id)
            cur.execute(query)
        self.conn.commit()
        return

    ##Grouped for transactions
    def _insert_domains(self, domains):
        cur = self.conn.cursor()
        for domain in domains:
            query = """
              INSERT INTO domainlist(domain, type) 
              VALUES('{domain}', 3);
            """.format(domain=domain)
            cur.execute(query)
        self.conn.commit()
        return

    ##Can think of the update as owning the state of domains on PiHole
    ##it is responsible for enabling/disabling those domains in
    ##accordance with the schedule
    def update(self, is_active, block_list):
        insert, disable, enable = self._diff_block_list(
                is_active, block_list)
        self._insert_domains(insert)
        self._disable_domains(disable)
        self._enable_domains(enable)
        ##If we have changed anything return True
        return not(not insert and not disable and not enable)

    def __init__(self):
        loc = os.getenv('PIHOLE_DB_LOC')
        if not loc:
            raise Exception("No pihole DB ENV variable")
        else:
            self.conn = sqlite3.connect(loc)

if __name__ == "__main__":

    args = sys.argv
    if len(args) <= 1:
        raise Exception("Must pass schedule file path and restart command as argument")
    else:
        schedule_path = args[1]
        restart_cmd = args[2]

    s = Schedule(schedule_path)
    s.load()

    b = BlockList(s)
    is_active, block_list = b.get_block_list()

    pi = PiHole()
    has_changed = pi.update(is_active, block_list)
    if has_changed:
        print(f'Restarting PiHole')
        p = subprocess.run(
                restart_cmd, capture_output=True, shell=True);
        print(f'Restart completed with {p.returncode}')
    else:
        print(f'No changes detected')
    print(f'Shutdown')
    

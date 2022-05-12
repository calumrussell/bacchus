Bacchus is a Pihole-based website blocker with schedulding functionality.

Create a list of websites, create a weekly schedule with start and end times, and Bacchus will enable and disable DNS blocking in Pihole on your schedule.

For simplicitly, the app is completely stateless and so needs to be scheduled to run at least every hour to check the state of the current blocklist in Pihole. The app does not use groups, everything is run against the default group right now. The app cannot remove websites from the blocklist, but it will disable when your schedule dictates. Finally, the app functions more as a time-based list manager and doesn't do anything but add/enable/disable websites on a list.

To run the application, you need to pass the environment variables:

* SCHEDULE_LOC - the location of the folder containing the schedules
* PIHOLE_DB_LOC - the location of the pihole gravity.db database file.

The formatting for the schedule and block list is shown in the example files above.

And call the program like:

        python main.py [name of schedule file] [command to restart the pihole dns process]

My pihole is running on Docker so I can restart it with:

        docker exec -i pihole pihole restartdns

The application takes the time from Python's datetime module. This may not be the same time as your system time so it is advisable to run the program from the CLI once, and the actual time (as well as the program logs) will appear on stdout.

DNS blocking isn't a perfect solution, and the blocklists are a better permanent solution. This was just something I wanted to quickly code up, and see if it would work.

If you are using Chrome, you also need to deactivate SecureDNS. And you will find that some apps, those that use service workers such as Reddit, won't be fully blocked without clearing all the stuff that site has saved in your browser. 

The only way that was consistently able to tell me whether the block was working (or whether it was something with Chrome/browser) was pinging the domain name from the command-line.

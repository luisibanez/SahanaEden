# -*- coding: utf-8 -*-

""" Synchronization

    @author: Amer Tahir

"""

module = "sync"

# -----------------------------------------------------------------------------
# Sync Policy
#
sync_policy_opts = {
    0:T("No Sync"),
    1:T("Keep Local"),
    2:T("Replace with Remote"),
    3:T("Newer Timestamp"),
#    4:T("Role-based"),
    5:T("Choose Manually")
}

opt_sync_policy = db.Table(None, "sync_policy",
                           Field("policy", "integer", notnull=True,
                                 requires = IS_IN_SET(sync_policy_opts),
                                 default = 3,
                                 represent = lambda opt: sync_policy_opts.get(opt, UNKNOWN_OPT)))


# -----------------------------------------------------------------------------
# Settings
#
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        Field("uuid", length=36, notnull=True),     # Our UUID for sync purposes
                        Field("beacon_service_url", default = "http://sync.eden.sahanafoundation.org/sync/beacon"), # URL of beacon service that our sahana instance is configured to work with
                        Field("sync_pools"),                        # Comma-separated list of sync pools we've subscribed to
                        Field("comments", length=128, default = "This is a SahanaEden instance, see http://eden.sahanafoundation.org" ),
                        migrate=migrate)


# -----------------------------------------------------------------------------
# Sync partners
#
sync_partner_instance_type_opts = {
    "Sahana Eden":T("Sahana Eden"),
    "Sahana Agasti":T("Sahana Agasti"),
    "Ushahidi":T("Ushahidi"),
    "Other":T("Other")
}

# Custom settings for sync partners
resource = "partner"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        Field("uuid", length=36, notnull=True),     # uuid of this partner
                        Field("name", default="Sahana Eden Instance"), # name of the partner (descriptive title)
                        Field("instance_url", default = "http://sync.eden.sahanafoundation.org/eden", notnull=True), # URL of their instance
                        Field("instance_type",                      # the type of instance => "SahanaEden", "SahanaAgasti", "Ushahidi", etc.
                              default="Sahana Eden",
                              requires = IS_IN_SET(sync_partner_instance_type_opts) ),
                        Field("username"),                          # username required to sync with this partner
                        Field("password", "password"),              # password required to sync with this partner
                        Field("sync_pools"),                        # Comma-separated list of sync pools they're subscribed to
                        opt_sync_policy,                            # sync_policy for this partner
                        Field("last_sync_on", "datetime"),          # the last time we sync-ed with this partner
                        Field("comments", length=128),
                        migrate=migrate)


# -----------------------------------------------------------------------------
# Sync Conflicts Log - record all conflicts here
#
resource = "conflict"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        Field("uuid", length=36, notnull=True),     # uuid of the conflicting resource
                        Field("resource_table"),                    # the table name of the conflicting resource
                        Field("remote_record", "text"),             # String dump of the remote record
                        Field("remote_modified_by"),                # the user who modified the remote resource, empty if it is None
                        Field("remote_modified_on", "datetime"),    # the date and time when the remote record was modified
                        Field("logged_on", "datetime"),             # the date and time when this conflict was logged
                        Field("resolved", "boolean"),               # whether this conflict has been resolved or not
                        migrate=migrate)


# -----------------------------------------------------------------------------
# Sync General Log - keeps log of all syncs
#
resource = "log"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("partner_uuid", length=36),           # uuid of remote system we synced with
                Field("timestmp", "datetime"),              # the date and time when sync was performed
                Field("sync_resources", "text"),            # comma-separated list of resources synced
                Field("sync_errors", "text"),               # sync errors encountered
                Field("sync_mode"),                         # whether this was an "online" sync (standard sync mode) or "offline" sync (USB/File based)
                Field("complete_sync", "boolean"),          # whether all resources were synced (complete sync) or only those modified since the last sync (partial sync)
                Field("sync_method"),                       # whether this was a Pull only, Push only, Remote Push or a Pull-Push sync operation
                migrate=migrate)

# -----------------------------------------------------------------------------
# Sync Now - stored state
#
resource = "now"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("sync_jobs", "text"),                 # comma-separated list of sync jobs (partner uuids for now, sync job ids from scheduler in future)
                Field("started_on", "datetime"),            # timestamp when the sync now process began
                Field("job_resources_done", "text"),        # comma-separated list of resources synced of the currently running job
                Field("job_resources_pending", "text"),     # comma-separated list of resources to be synced of the currently running job
                Field("job_sync_errors", "text"),           # sync errors encountered while processing the current job
                migrate=migrate)

# -----------------------------------------------------------------------------
# Sync Schedule - scheduled sync jobs
#
sync_schedule_period_opts = {
    "h":T("Hourly"),
    "d":T("Daily"),
    "w":T("Weekly"),
    "o":T("Just Once"),
    "m":T("Manual")
}

sync_schedule_job_type_opts = {
    1:T("Sahana Eden <=> Sahana Eden sync"),
    2:T("Sahana Eden <= Other sync (Sahana Agasti, Ushahidi, etc.)")
}

resource = "schedule"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                        Field("comments", length=128),              # brief comments about the scheduled job
                        Field("period",                             # schedule interval period, either hourly, "h", daily, "d", weekly, "w" or one-time, "o"
                              length=10,
                              notnull=True,
                              default="h",
                              requires = IS_IN_SET(sync_schedule_period_opts) ),
                        Field("hours", "integer", default=4),       # specifies the number of hours when hourly period is specified in 'period' field
                        Field("days_of_week", length=40),           # comma-separated list of the day(s) of the week when job runs on weekly basis.
                                                            # A day in a week is represented as a number ranging from 1 to 7 (1 = Sunday, 7 = Saturday)
                        Field("time_of_day", "time"),               # the time (at day_of_week) when job runs on a weekly or daily basis
                        Field("runonce_datetime", "datetime"),      # the date and time when job runs just once
                        Field("job_type", "integer", default=1,     # This specifies the type of job: 1 - SahanaEden <=> SahanaEden sync,
                              requires = IS_IN_SET(sync_schedule_job_type_opts) ),
                                                            # 2 - SahanaEden <= Other sync (could be SahanaAgasti, Ushahidi, etc.)
                        Field("job_command", "text", notnull=True), # sync command to execute when this job runs. This command is encoded as a JSON formatted object.
                                                            # It contains the UUID of the sync partner, the list of modules along
                                                            # with resources within them to sync, whether this would be a complete or partial sync
                                                            # (partial sync only retrieves data modified after the last sync, complete sync fetches all),
                                                            # whether this sync would be a two-way (both push and pull) or one-way (push or pull),
                                                            # and sync policy (default policy is taken from the sync partner's record)
                        Field("last_run", "datetime"),              # the date and time of last scheduled run
                        Field("enabled", "boolean",                 # whether this schedule is enabled or not. Useful in cases when you want to temporarily
                              default=True),                          # disable a schedule
                        migrate=migrate)


# -----------------------------------------------------------------------------

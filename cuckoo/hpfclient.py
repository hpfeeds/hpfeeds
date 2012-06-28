import json

from lib.cuckoo.common.abstracts import Report
from lib.cuckoo.common.exceptions import CuckooDependencyError, CuckooReportError

try:
    import lib.hpfeeds as hpfeeds
except:
    raise CuckooDependencyError("Unable to import HPFeeds library")

# This file should be placed in "modules/reporting/" in Cuckoo >= 0.4.
# You should have the hpfeeds.py library installed in "lib/" and you should
# place the following configuration section in "conf/reporting.conf":
#
# [hpfclient]
# enabled = on
# host = <host name>
# port = 10000
# ident = <ident>
# secret = <secret key>
# channel = <channel name>

class HPFClient(Report):
    """Publishes the results on an HPFeeds broker channel."""

    def run(self, results):
        """Sends JSON report to HPFeeds channel.
        @param results: Cuckoo results dict.
        @raise CuckooReportError: if fails to write report.
        """
        try:
            hpc = hpfeeds.HPC(self.options["host"], self.options["port"], self.options["ident"], self.options["secret"], timeout=60)
            hpc.publish(self.options["channel"], json.dumps(results, sort_keys=False, indent=4))
            hpc.close()
        except hpfeeds.FeedException as e:
            raise CuckooReportError("Failed to publish on HPFeeds channel: %s" % e.message)

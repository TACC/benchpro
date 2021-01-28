
class init(object):
    def __init__(self, glob):
        self.glob = glob

    # Get list of uncaptured results and print note to user
    def new_results(self):
        print("Checking for uncaptured results...")
        # Uncaptured results + job complete
        pending_results = self.glob.lib.get_completed_results(self.glob.lib.get_pending_results(), True)
        if pending_results:
            print(self.glob.note)
            print("There are " + str(len(pending_results)) + " uncaptured results found in " + self.glob.lib.rel_path(self.glob.stg['pending_path']))
            print("Run 'benchtool --capture' to send to database.")
        else:
            print("No new results found.")

        print()


    def prt_brk(self):
        print("---------------------------")
        print()

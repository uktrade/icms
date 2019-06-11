class Archivable(object):
    def archive(self):
        self.is_active = False
        self.save()

    def unarchive(self):
        self.is_active = True
        self.save()

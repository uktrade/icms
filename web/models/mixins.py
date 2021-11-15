class Archivable(object):
    def archive(self):
        self.is_active = False
        self.save()  # type: ignore[attr-defined]

    # TODO: we have to expand this unarchive, sometimes it should be blocked.
    # e.g. the system shouldn't allow you to have more than one active
    # translation for language X for some template (see what was done in
    # ICMSLST-483)
    def unarchive(self):
        self.is_active = True
        self.save()  # type: ignore[attr-defined]

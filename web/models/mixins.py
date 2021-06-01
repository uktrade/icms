from django.db import transaction


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


class Sortable(object):
    @transaction.atomic
    def swap_order(self, swap_with):
        current_order = self.order  # type: ignore[has-type]
        new_order = swap_with.order
        self.order = new_order
        swap_with.order = current_order
        self.save()  # type: ignore[attr-defined]
        swap_with.save()

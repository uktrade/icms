from django.db import transaction


class Archivable(object):
    def archive(self):
        self.is_active = False
        self.save()

    # TODO: we have to expand this unarchive, sometimes it shuold be blocked.
    # e.g. the system shouldn't allow you to have more than one active
    # translation for language X for some template
    def unarchive(self):
        self.is_active = True
        self.save()


class Sortable(object):
    @transaction.atomic
    def swap_order(self, swap_with):
        current_order = self.order
        new_order = swap_with.order
        self.order = new_order
        swap_with.order = current_order
        self.save()
        swap_with.save()

def handle_actions(request, model):
    action = request.POST.get('action') if request.POST else None
    item = request.POST.get('item')
    if item:
        object = model.objects.get(pk=item)
        if action == 'archive':
            object.archive()
            return True  # handled
        elif action == 'unarchive':
            object.unarchive()
            return True

    return False

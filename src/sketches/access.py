"""La propiedad se controla en consultas y escrituras; no se confía en datos del cliente."""
def visible_to(model, user):
    if not user.is_authenticated or not user.is_active:
        return model.objects.none()
    return model.objects.all() if user.is_superuser else model.objects.filter(owner=user)

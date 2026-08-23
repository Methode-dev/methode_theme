def post_init_hook(env):
    """Seed the mappings that cannot be expressed as XML ``ref=`` and do a first
    pass over the manifests.

    Runs once, on a read/write cursor, with every model loaded. This is the only
    thing that covers a cold first install: ``ir.module.module.update_list()`` is
    called by ``odoo/modules/loading.py`` while only ``base`` is in the registry,
    so our override of it is inert during ``-i``/``-u``.
    """
    env['methode.apps.category']._seed_dynamic_module_category_mapping()
    env['ir.module.module']._sync_apps_dropdown_keys()

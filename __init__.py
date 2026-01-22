# -*- coding: utf-8 -*-

from . import models

def post_init_hook(env):
    """Clean problematic actions after module install/upgrade"""
    env.cr.execute("DELETE FROM ir_actions_act_window WHERE context LIKE '%is_bod_user%'")
    env.cr.execute("DELETE FROM ir_actions_client WHERE context LIKE '%is_bod_user%'")
    env.cr.execute("DELETE FROM ir_attachment WHERE name LIKE '%assets%'")
    print("Cleaned problematic actions from database")
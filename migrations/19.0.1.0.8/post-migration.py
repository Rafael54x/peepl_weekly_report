def migrate(cr, version):
    """Update field templates that use client_id anchor to use pic_id instead"""
    cr.execute("""
        UPDATE peepl_field_template 
        SET anchor_field = 'pic_id' 
        WHERE anchor_field = 'client_id'
    """)
    
    # Delete saved filters that contain client_id or request_form
    cr.execute("""
        DELETE FROM ir_filters 
        WHERE model_id = 'peepl.weekly.report' 
        AND (domain LIKE '%client_id%' OR domain LIKE '%request_form%')
    """)
    
    # Clear any UI view customizations
    cr.execute("""
        DELETE FROM ir_ui_view_custom 
        WHERE arch LIKE '%client_id%' OR arch LIKE '%request_form%'
    """)

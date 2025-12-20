# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """
    Pre-init hook to handle firm_name field conversion
    This runs BEFORE the module is loaded, so it can fix the database schema
    """
    cr = env.cr
    
    _logger.info("="*70)
    _logger.info("Running pre-init hook for qaco_audit")
    _logger.info("="*70)
    
    try:
        # Disable triggers temporarily
        cr.execute("SET CONSTRAINTS ALL DEFERRED")
        
        # Check if firm_name column exists and is varchar (Selection field)
        cr.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='qaco_audit' AND column_name='firm_name'
        """)
        result = cr.fetchone()
        
        if result and result[1] in ('character varying', 'varchar', 'text'):
            _logger.info("Found old firm_name Selection field - fixing...")
            
            # Rename the column
            cr.execute("""
                ALTER TABLE qaco_audit 
                RENAME COLUMN firm_name TO firm_name_old
            """)
            _logger.info("✓ Renamed firm_name to firm_name_old")
            
            # Delete field metadata - this is critical
            cr.execute("""
                DELETE FROM ir_model_fields 
                WHERE model='qaco.audit' AND name='firm_name'
            """)
            deleted_fields = cr.rowcount
            _logger.info("✓ Deleted old field metadata (%s records)", deleted_fields)
            
            # Delete any constraints on the field
            cr.execute("""
                DELETE FROM ir_model_constraint
                WHERE model IN (
                    SELECT id FROM ir_model WHERE model='qaco.audit'
                )
            """)
            
            # Delete selection values
            cr.execute("""
                DELETE FROM ir_model_fields_selection 
                WHERE field_id IN (
                    SELECT id FROM ir_model_fields 
                    WHERE model='qaco.audit' AND name='firm_name'
                )
            """)
            deleted_selections = cr.rowcount
            _logger.info("✓ Deleted selection values (%s records)", deleted_selections)
            
            # Force commit to ensure changes are persisted
            cr.commit()
            
            _logger.info("="*70)
            _logger.info("✓ Pre-init hook completed successfully")
            _logger.info("="*70)
        else:
            _logger.info("No firm_name Selection field found - skipping")
            
    except Exception as e:
        _logger.error("Error in pre-init hook: %s", str(e), exc_info=True)
        # Try to rollback and continue
        try:
            cr.rollback()
        except:
            pass
        raise


# def post_init_hook(env):
#     """
#     Post-init hook to auto-install phase modules after qaco_audit is installed
#     """
#     _logger.info("Running post-init hook for qaco_audit - installing phase modules")
#     
#     phase_modules = [
#         'qaco_client_onboarding',
#         'qaco_planning_phase',
#         'qaco_execution_phase',
#         'qaco_finalisation_phase',
#         'qaco_deliverables',
#         'qaco_quality_review',
#     ]
#     
#     try:
#         modules = env['ir.module.module'].search([
#             ('name', 'in', phase_modules),
#             ('state', '!=', 'installed')
#         ])
#         if modules:
#             _logger.info("Marking phase modules for installation: %s", modules.mapped('name'))
#             modules.button_install()
#             env.cr.commit()
#     except Exception as e:
#         _logger.warning("Could not auto-install phase modules: %s", str(e))


def uninstall_hook(env):
    """
    Uninstall hook to remove all phase modules when qaco_audit is uninstalled
    """
    _logger.info("Running uninstall hook for qaco_audit - uninstalling phase modules")
    
    phase_modules = [
        'qaco_client_onboarding',
        'qaco_planning_phase',
        'qaco_execution_phase',
        'qaco_finalisation_phase',
        'qaco_deliverables',
        'qaco_quality_review',
    ]
    
    try:
        modules = env['ir.module.module'].search([
            ('name', 'in', phase_modules),
            ('state', '=', 'installed')
        ])
        if modules:
            _logger.info("Uninstalling phase modules: %s", modules.mapped('name'))
            modules.button_immediate_uninstall()
    except Exception as e:
        _logger.warning("Could not auto-uninstall phase modules: %s", str(e))

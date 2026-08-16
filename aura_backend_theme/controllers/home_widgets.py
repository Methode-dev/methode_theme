# -*- coding: utf-8 -*-
import json
import logging
import uuid
from datetime import date, timedelta
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def _company_domain(env, model_name):
    """Return a safe company scope domain for models that support company_id."""
    model = env[model_name]
    if 'company_id' in model._fields:
        return [('company_id', 'in', env.companies.ids)]
    return []


def _list_action(name, model, domain=None, context=None, views=None):
    return {
        'type': 'ir.actions.act_window',
        'name': name,
        'res_model': model,
        'views': views or [[False, 'list'], [False, 'form']],
        'domain': domain or [],
        'context': context or {},
        'target': 'current',
    }


def _form_action(name, model, res_id):
    return {
        'type': 'ir.actions.act_window',
        'name': name,
        'res_model': model,
        'res_id': res_id,
        'views': [[False, 'form']],
        'target': 'current',
    }


def _create_action(name, model, context=None):
    return {
        'type': 'ir.actions.act_window',
        'name': name,
        'res_model': model,
        'views': [[False, 'form']],
        'context': context or {},
        'target': 'current',
    }


def _has_model_read_access(model):
    try:
        if hasattr(model, 'check_access_rights'):
            return model.check_access_rights('read', raise_exception=False)
        if hasattr(model, 'check_access'):
            model.check_access('read')
        return True
    except Exception:
        return False


# ── Widget catalog ────────────────────────────────────────────────────────────
# module=None → always available.
# Widgets with a module are hidden in the picker when that module isn't installed.

WIDGET_CATALOG = [
    # General
    {'id': 'quick_actions',  'label': 'Quick Actions',      'description': 'Fast shortcuts for common tasks',         'icon': 'fa-bolt',                 'color': 'brand',  'module': None,      'group': 'General',    'default_col_span': '3'},
    {'id': 'stats',          'label': 'Overview Stats',     'description': 'KPI metrics: invoices, activities, CRM',  'icon': 'fa-chart-bar',            'color': 'blue',   'module': None,      'group': 'General',    'default_col_span': '3'},
    {'id': 'activities',     'label': 'My Activities',      'description': 'Scheduled tasks grouped by urgency',      'icon': 'fa-tasks',                'color': 'orange', 'module': None,      'group': 'General',    'default_col_span': '2'},
    {'id': 'focus',          'label': "Today's Focus",      'description': 'Urgent items and contextual alerts',      'icon': 'fa-fire',                 'color': 'red',    'module': None,      'group': 'General',    'default_col_span': '1'},
    {'id': 'recent',         'label': 'Continue Working',   'description': 'Recently modified records across apps',   'icon': 'fa-history',              'color': 'gray',   'module': None,      'group': 'General',    'default_col_span': '1'},
    {'id': 'activity_trend', 'label': 'My Activity Trend',  'description': 'Overdue, today, and upcoming activity mix', 'icon': 'fa-chart-pie',         'color': 'orange', 'module': None,      'group': 'General',    'default_col_span': '1'},
    # Accounting
    {'id': 'invoices',       'label': 'Top Invoices',       'description': 'Open and overdue customer invoices',      'icon': 'fa-file-invoice-dollar',  'color': 'blue',   'module': 'account', 'group': 'Accounting', 'default_col_span': '2'},
    # CRM
    {'id': 'pipeline',       'label': 'My Pipeline',        'description': 'CRM opportunities grouped by stage',      'icon': 'fa-chart-line',           'color': 'green',  'module': 'crm',     'group': 'CRM',        'default_col_span': '3'},
    # Inventory
    {'id': 'inventory_reorder',   'label': 'Products to Reorder', 'description': 'Items at or below minimum stock level',     'icon': 'fa-boxes',          'color': 'orange', 'module': 'stock',    'group': 'Inventory', 'default_col_span': '2'},
    {'id': 'inventory_receipts',  'label': 'Pending Receipts',    'description': 'Incoming shipments ready to receive',       'icon': 'fa-truck',          'color': 'blue',   'module': 'stock',    'group': 'Inventory', 'default_col_span': '1'},
    # Purchase
    {'id': 'purchase_rfq',        'label': 'RFQs to Send',        'description': 'Draft purchase orders awaiting confirmation','icon': 'fa-paper-plane',   'color': 'purple', 'module': 'purchase', 'group': 'Purchase',  'default_col_span': '2'},
    {'id': 'purchase_orders',     'label': 'Open Purchase Orders', 'description': 'Confirmed POs pending delivery',            'icon': 'fa-shopping-cart', 'color': 'green',  'module': 'purchase', 'group': 'Purchase',  'default_col_span': '2'},
    # Sales
    {'id': 'sale_quotations',     'label': 'Quotations to Send',  'description': 'Draft and sent quotations',                 'icon': 'fa-file-alt',      'color': 'blue',   'module': 'sale',     'group': 'Sales',     'default_col_span': '2'},
    {'id': 'sale_to_invoice',     'label': 'Orders to Invoice',   'description': 'Confirmed orders ready for invoicing',      'icon': 'fa-file-invoice',  'color': 'green',  'module': 'sale',     'group': 'Sales',     'default_col_span': '2'},
    {'id': 'sales_trend',         'label': 'Sales Trend',         'description': 'Monthly sales totals for the last 6 months', 'icon': 'fa-chart-column', 'color': 'blue',   'module': 'sale',     'group': 'Sales',     'default_col_span': '2'},
    # HR
    {'id': 'hr_leaves',           'label': 'Leave Requests',      'description': 'Approved and pending leave requests',       'icon': 'fa-calendar-minus', 'color': 'orange', 'module': 'hr_holidays',   'group': 'HR',           'default_col_span': '2'},
    {'id': 'hr_attendance',       'label': 'Attendance Today',    'description': 'Today\'s check-ins and check-outs',         'icon': 'fa-user-clock',     'color': 'blue',   'module': 'hr_attendance', 'group': 'HR',           'default_col_span': '1'},
    # Project
    {'id': 'project_tasks',       'label': 'My Tasks',           'description': 'Tasks assigned to you and still open',      'icon': 'fa-tasks',          'color': 'green',  'module': 'project',       'group': 'Project',      'default_col_span': '2'},
    {'id': 'project_deadlines',   'label': 'Project Deadlines',   'description': 'Tasks due in the next 7 days',              'icon': 'fa-hourglass-half', 'color': 'orange', 'module': 'project',       'group': 'Project',      'default_col_span': '2'},
    # Manufacturing
    {'id': 'mrp_production',      'label': 'Production Orders',   'description': 'Confirmed production orders in progress',   'icon': 'fa-industry',       'color': 'purple', 'module': 'mrp',           'group': 'Manufacturing', 'default_col_span': '2'},
    # Accounting
    {'id': 'account_cashflow',    'label': 'Cash Flow Summary',   'description': 'Bank balance and near-term cash movements', 'icon': 'fa-sack-dollar',    'color': 'green',  'module': 'account',       'group': 'Accounting',   'default_col_span': '3'},
    {'id': 'account_aged_recv',   'label': 'Aged Receivables',    'description': 'Open customer invoices bucketed by age',    'icon': 'fa-file-invoice-dollar', 'color': 'red', 'module': 'account', 'group': 'Accounting', 'default_col_span': '2'},
]

# ── Data fetchers ─────────────────────────────────────────────────────────────
# Each fetcher receives (env, uid) and returns a dict that the JS widget consumes.
# Only called when the widget is active and its module is installed.

def _fetch_inventory_reorder(env, uid):
    try:
        # qty_on_hand is a computed non-stored field; sort in Python after filtering.
        company_domain = _company_domain(env, 'stock.warehouse.orderpoint')
        orderpoints = env['stock.warehouse.orderpoint'].search(
            company_domain,
            limit=200
        )
        to_reorder = sorted(
            [op for op in orderpoints if op.qty_on_hand <= op.product_min_qty],
            key=lambda op: op.qty_on_hand,
        )
        items = []
        for op in to_reorder[:8]:
            items.append({
                'id': op.id,
                'product_name': op.product_id.display_name or '',
                'qty_on_hand': op.qty_on_hand,
                'product_min_qty': op.product_min_qty,
                'product_max_qty': op.product_max_qty,
                'uom': op.product_uom.name if op.product_uom else '',
                'warehouse': op.warehouse_id.name if op.warehouse_id else '',
                'record_url': f'/odoo/inventory/products/{op.product_id.id}',
                'action': _form_action(op.product_id.display_name or 'Product', 'product.product', op.product_id.id),
            })
        return {
            'items': items,
            'count': len(to_reorder),
            'viewAction': _list_action(
                'Products to Reorder',
                'stock.warehouse.orderpoint',
                company_domain,
            ),
        }
    except Exception:
        _logger.warning('Failed to fetch inventory reorder data', exc_info=True)
        return {'items': [], 'count': 0}


def _fetch_inventory_receipts(env, uid):
    try:
        company_domain = _company_domain(env, 'stock.picking')
        picking_domain = company_domain + [
                ('picking_type_code', '=', 'incoming'),
                ('state', '=', 'assigned'),
            ]
        pickings = env['stock.picking'].search(
            picking_domain,
            order='scheduled_date asc',
            limit=6
        )
        items = []
        for p in pickings:
            scheduled = p.scheduled_date
            days_late = (date.today() - scheduled.date()).days if scheduled and scheduled.date() < date.today() else 0
            items.append({
                'id': p.id,
                'name': p.name or '',
                'partner_name': p.partner_id.name or 'Unknown',
                'scheduled_date': str(scheduled.date()) if scheduled else '',
                'days_late': days_late,
                'product_count': len(p.move_ids),
                'record_url': f'/odoo/inventory/receipts/{p.id}',
                'action': _form_action(p.display_name or 'Receipt', 'stock.picking', p.id),
            })
        total = env['stock.picking'].search_count(picking_domain)
        return {
            'items': items,
            'count': total,
            'viewAction': _list_action('Pending Receipts', 'stock.picking', picking_domain),
        }
    except Exception:
        _logger.warning('Failed to fetch inventory receipts data', exc_info=True)
        return {'items': [], 'count': 0}


def _fetch_purchase_rfq(env, uid):
    try:
        orders = env['purchase.order'].search(
            [('state', '=', 'draft'), ('user_id', '=', uid)],
            order='date_order asc',
            limit=6
        )
        items = []
        for o in orders:
            items.append({
                'id': o.id,
                'name': o.name or '',
                'partner_name': o.partner_id.name or '',
                'amount_total': o.amount_total,
                'currency_symbol': o.currency_id.symbol or '',
                'date_order': str(o.date_order.date()) if o.date_order else '',
                'product_count': len(o.order_line),
                'record_url': f'/odoo/purchase/{o.id}',
                'action': _form_action(o.display_name or 'RFQ', 'purchase.order', o.id),
            })
        total = env['purchase.order'].search_count([('state', '=', 'draft'), ('user_id', '=', uid)])
        return {
            'items': items,
            'count': total,
            'viewAction': _list_action('RFQs to Send', 'purchase.order', [('state', '=', 'draft'), ('user_id', '=', uid)]),
            'createAction': _create_action('New RFQ', 'purchase.order'),
        }
    except Exception:
        _logger.warning('Failed to fetch purchase RFQ data', exc_info=True)
        return {'items': [], 'count': 0}


def _fetch_purchase_orders(env, uid):
    try:
        orders = env['purchase.order'].search(
            [('state', '=', 'purchase'), ('user_id', '=', uid)],
            order='date_approve desc',
            limit=6
        )
        items = []
        for o in orders:
            items.append({
                'id': o.id,
                'name': o.name or '',
                'partner_name': o.partner_id.name or '',
                'amount_total': o.amount_total,
                'currency_symbol': o.currency_id.symbol or '',
                'date_approve': str(o.date_approve.date()) if o.date_approve else '',
                'invoice_status': o.invoice_status or '',
                'record_url': f'/odoo/purchase/{o.id}',
                'action': _form_action(o.display_name or 'Purchase Order', 'purchase.order', o.id),
            })
        total = env['purchase.order'].search_count([('state', '=', 'purchase'), ('user_id', '=', uid)])
        return {
            'items': items,
            'count': total,
            'viewAction': _list_action('Open Purchase Orders', 'purchase.order', [('state', '=', 'purchase'), ('user_id', '=', uid)]),
        }
    except Exception:
        _logger.warning('Failed to fetch purchase orders data', exc_info=True)
        return {'items': [], 'count': 0}


def _fetch_sale_quotations(env, uid):
    try:
        orders = env['sale.order'].search(
            [('state', 'in', ['draft', 'sent']), ('user_id', '=', uid)],
            order='date_order desc',
            limit=6
        )
        items = []
        for o in orders:
            items.append({
                'id': o.id,
                'name': o.name or '',
                'partner_name': o.partner_id.name or '',
                'amount_total': o.amount_total,
                'currency_symbol': o.currency_id.symbol or '',
                'state': o.state,
                'state_label': 'Sent' if o.state == 'sent' else 'Draft',
                'date_order': str(o.date_order.date()) if o.date_order else '',
                'record_url': f'/odoo/sales/{o.id}',
                'action': _form_action(o.display_name or 'Quotation', 'sale.order', o.id),
            })
        total = env['sale.order'].search_count([('state', 'in', ['draft', 'sent']), ('user_id', '=', uid)])
        return {
            'items': items,
            'count': total,
            'viewAction': _list_action('Quotations to Send', 'sale.order', [('state', 'in', ['draft', 'sent']), ('user_id', '=', uid)]),
            'createAction': _create_action('New Quotation', 'sale.order'),
        }
    except Exception:
        _logger.warning('Failed to fetch sale quotations data', exc_info=True)
        return {'items': [], 'count': 0}


def _fetch_sale_to_invoice(env, uid):
    try:
        orders = env['sale.order'].search(
            [('invoice_status', '=', 'to invoice'), ('user_id', '=', uid)],
            order='date_order desc',
            limit=6
        )
        items = []
        for o in orders:
            items.append({
                'id': o.id,
                'name': o.name or '',
                'partner_name': o.partner_id.name or '',
                'amount_total': o.amount_total,
                'currency_symbol': o.currency_id.symbol or '',
                'date_order': str(o.date_order.date()) if o.date_order else '',
                'record_url': f'/odoo/sales/{o.id}',
                'action': _form_action(o.display_name or 'Sale Order', 'sale.order', o.id),
            })
        total = env['sale.order'].search_count([('invoice_status', '=', 'to invoice'), ('user_id', '=', uid)])
        return {
            'items': items,
            'count': total,
            'viewAction': _list_action('Orders to Invoice', 'sale.order', [('invoice_status', '=', 'to invoice'), ('user_id', '=', uid)]),
        }
    except Exception:
        _logger.warning('Failed to fetch sale to-invoice data', exc_info=True)
        return {'items': [], 'count': 0}


def _format_date(value):
    if not value:
        return ''
    if hasattr(value, 'date'):
        try:
            return str(value.date())
        except Exception:
            return str(value)
    return str(value)


def _format_time(value):
    if not value:
        return ''
    try:
        return value.strftime('%H:%M')
    except Exception:
        return _format_date(value)


def _parse_widget_config(config_json):
    if not config_json:
        return {}
    try:
        parsed = json.loads(config_json)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _is_custom_widget_id(widget_id):
    return bool(widget_id and str(widget_id).startswith('custom_'))


def _safe_int(value, default=0, minimum=None, maximum=None):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = default
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def _field_label(model, field_name):
    field = model._fields.get(field_name)
    if not field:
        return field_name
    # Utilise fields_get pour obtenir le libellé TRADUIT (langue de l'utilisateur),
    # et non field.string qui renvoie la source anglaise.
    try:
        info = model.fields_get([field_name], ['string'])
        return info.get(field_name, {}).get('string') or field.string or field_name
    except Exception:
        return field.string or field_name


def _normalize_domain(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


def _serialize_field_value(value):
    if value is False or value is None:
        return ''
    if isinstance(value, (list, tuple)):
        # many2one values arrive as [id, display_name] in search_read.
        if len(value) >= 2 and isinstance(value[0], int):
            return value[1] or ''
        return ', '.join(str(v) for v in value if v)
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return value


def _fetch_custom_widget(env, row):
    config = _parse_widget_config(row.config_json)
    model_name = config.get('model')
    widget_type = config.get('widget_type') or 'table'
    title = config.get('title') or 'Custom Widget'
    limit = _safe_int(config.get('limit'), default=5, minimum=1, maximum=25)

    if not model_name or model_name not in env:
        return {'title': title, 'widget_type': widget_type, 'error': 'Model is not available.'}

    Model = env[model_name]
    try:
        if not _has_model_read_access(Model):
            return {'title': title, 'widget_type': widget_type, 'error': 'You do not have access to this model.'}
    except Exception:
        return {'title': title, 'widget_type': widget_type, 'error': 'You do not have access to this model.'}

    domain = _normalize_domain(config.get('domain'))
    view_action = _list_action(title, model_name, domain)

    try:
        if widget_type == 'kpi':
            measure = config.get('measure_field')
            aggregation = config.get('aggregation') or 'count'
            count = Model.search_count(domain)
            value = count
            label = 'records'
            if aggregation in ('sum', 'avg') and measure in Model._fields:
                records = Model.search(domain, limit=1000)
                values = [getattr(record, measure, 0) or 0 for record in records]
                value = sum(values)
                if aggregation == 'avg':
                    value = value / len(values) if values else 0
                label = f"{aggregation} of {_field_label(Model, measure)}"
            return {
                'title': title,
                'widget_type': 'kpi',
                'value': value,
                'label': label,
                'count': count,
                'icon': config.get('icon') or 'fa-chart-bar',
                'viewAction': view_action,
            }

        fields = config.get('fields') or ['display_name']
        safe_fields = [
            field for field in fields
            if field in Model._fields and Model._fields[field].type not in ('binary', 'html')
        ][:6] or ['display_name']
        if 'display_name' not in safe_fields and 'display_name' in Model._fields:
            safe_fields = ['display_name', *safe_fields]
        order = config.get('order') or 'write_date desc'
        records = Model.search_read(domain, safe_fields, limit=limit, order=order)
        columns = [{'name': field, 'label': _field_label(Model, field)} for field in safe_fields]
        rows = []
        for record in records:
            rows.append({
                'id': record.get('id'),
                'values': [_serialize_field_value(record.get(field)) for field in safe_fields],
                'action': _form_action(record.get('display_name') or title, model_name, record.get('id')) if record.get('id') else None,
            })
        return {
            'title': title,
            'widget_type': 'table',
            'columns': columns,
            'rows': rows,
            'count': Model.search_count(domain),
            'icon': config.get('icon') or 'fa-table',
            'viewAction': view_action,
        }
    except Exception:
        _logger.warning('Failed to fetch custom widget data', exc_info=True)
        return {'title': title, 'widget_type': widget_type, 'error': 'Could not load this widget.'}


def _fetch_hr_leaves(env, uid):
    try:
        company_domain = _company_domain(env, 'hr.leave')
        leave_domain = company_domain + [('state', '=', 'confirm')]
        leaves = env['hr.leave'].search(
            leave_domain,
            order='date_from asc',
            limit=6
        )
        items = []
        for leave in leaves:
            start = leave.date_from
            end = leave.date_to
            days = getattr(leave, 'number_of_days_display', 0.0) or leave.number_of_days or 0.0
            items.append({
                'id': leave.id,
                'employee_name': leave.employee_id.name or '',
                'leave_type': leave.holiday_status_id.name or '',
                'date_from': _format_date(start),
                'date_to': _format_date(end),
                'days': days,
                'record_url': f'/web#id={leave.id}&model=hr.leave&view_type=form',
                'action': _form_action(leave.display_name or 'Leave Request', 'hr.leave', leave.id),
            })
        total = env['hr.leave'].search_count(leave_domain)
        return {
            'items': items,
            'count': total,
            'viewAction': _list_action('Leave Requests', 'hr.leave', leave_domain),
        }
    except Exception:
        _logger.warning('Failed to fetch HR leaves data', exc_info=True)
        return {'items': [], 'count': 0}


def _fetch_hr_attendance(env, uid):
    try:
        if 'hr.attendance' not in env.registry:
            return {'items': [], 'count': 0}
        today = date.today()
        company_domain = _company_domain(env, 'hr.attendance')
        attendance_domain = company_domain + [
            ('check_in', '>=', str(today)),
            ('check_in', '<', str(today + timedelta(days=1))),
        ]
        attendances = env['hr.attendance'].search(
            attendance_domain,
            order='check_in desc',
            limit=6
        )
        items = []
        for attendance in attendances:
            check_in = attendance.check_in
            check_out = attendance.check_out
            worked_hours = attendance.worked_hours or 0.0
            items.append({
                'id': attendance.id,
                'employee_name': attendance.employee_id.name or '',
                'check_in': _format_time(check_in),
                'check_out': _format_time(check_out),
                'worked_hours': round(worked_hours, 2),
                'record_url': f'/web#id={attendance.id}&model=hr.attendance&view_type=form',
                'action': _form_action(attendance.display_name or 'Attendance', 'hr.attendance', attendance.id),
            })
        total = env['hr.attendance'].search_count(attendance_domain)
        return {
            'items': items,
            'count': total,
            'viewAction': _list_action('Attendance Today', 'hr.attendance', attendance_domain),
        }
    except Exception:
        _logger.warning('Failed to fetch HR attendance data', exc_info=True)
        return {'items': [], 'count': 0}


def _fetch_project_tasks(env, uid):
    try:
        tasks = env['project.task'].search(
            [('user_ids', 'in', [uid]), ('stage_id.fold', '=', False)],
            order='priority desc, date_deadline asc, id desc',
            limit=6
        )
        items = []
        for task in tasks:
            items.append({
                'id': task.id,
                'name': task.name or '',
                'project_name': task.project_id.name or '',
                'date_deadline': _format_date(task.date_deadline),
                'priority': task.priority or '0',
                'stage_name': task.stage_id.name or '',
                'record_url': f'/web#id={task.id}&model=project.task&view_type=form',
                'action': _form_action(task.display_name or 'Task', 'project.task', task.id),
            })
        total = env['project.task'].search_count([
            ('user_ids', 'in', [uid]), ('stage_id.fold', '=', False)
        ])
        return {
            'items': items,
            'count': total,
            'viewAction': _list_action('My Tasks', 'project.task', [
                ('user_ids', 'in', [uid]),
                ('stage_id.fold', '=', False),
            ]),
        }
    except Exception:
        _logger.warning('Failed to fetch project tasks data', exc_info=True)
        return {'items': [], 'count': 0}


def _fetch_project_deadlines(env, uid):
    try:
        today = date.today()
        cutoff = today + timedelta(days=7)
        tasks = env['project.task'].search(
            [('user_ids', 'in', [uid]), ('stage_id.fold', '=', False), ('date_deadline', '>=', str(today)), ('date_deadline', '<=', str(cutoff))],
            order='date_deadline asc, priority desc',
            limit=6
        )
        items = []
        for task in tasks:
            deadline = task.date_deadline
            deadline_date = deadline.date() if hasattr(deadline, 'date') else deadline
            days_left = (deadline_date - today).days if deadline_date else 0
            items.append({
                'id': task.id,
                'name': task.name or '',
                'project_name': task.project_id.name or '',
                'date_deadline': _format_date(deadline),
                'days_left': days_left,
                'record_url': f'/web#id={task.id}&model=project.task&view_type=form',
                'action': _form_action(task.display_name or 'Task', 'project.task', task.id),
            })
        total = env['project.task'].search_count([
            ('user_ids', 'in', [uid]), ('stage_id.fold', '=', False), ('date_deadline', '>=', str(today)), ('date_deadline', '<=', str(cutoff))
        ])
        return {
            'items': items,
            'count': total,
            'viewAction': _list_action('Project Deadlines', 'project.task', [
                ('user_ids', 'in', [uid]),
                ('stage_id.fold', '=', False),
                ('date_deadline', '>=', str(today)),
                ('date_deadline', '<=', str(cutoff)),
            ]),
        }
    except Exception:
        _logger.warning('Failed to fetch project deadlines data', exc_info=True)
        return {'items': [], 'count': 0}


def _fetch_mrp_production(env, uid):
    try:
        company_domain = _company_domain(env, 'mrp.production')
        production_domain = company_domain + [('state', 'in', ['confirmed', 'progress'])]
        productions = env['mrp.production'].search(
            production_domain,
            order='date_start asc, id desc',
            limit=6
        )
        items = []
        for production in productions:
            items.append({
                'id': production.id,
                'name': production.name or '',
                'product_name': production.product_id.display_name or '',
                'origin': production.origin or '',
                'quantity': production.product_qty or 0.0,
                'unit': production.product_uom_id.name if production.product_uom_id else '',
                'state': production.state or '',
                'record_url': f'/web#id={production.id}&model=mrp.production&view_type=form',
                'action': _form_action(production.display_name or 'Production Order', 'mrp.production', production.id),
            })
        total = env['mrp.production'].search_count(production_domain)
        return {
            'items': items,
            'count': total,
            'viewAction': _list_action('Production Orders', 'mrp.production', production_domain),
        }
    except Exception:
        _logger.warning('Failed to fetch MRP production data', exc_info=True)
        return {'items': [], 'count': 0}


def _fetch_activity_trend(env, uid):
    try:
        today = date.today()
        acts = env['mail.activity'].search([('user_id', '=', uid)])
        overdue = 0
        due_today = 0
        upcoming = 0
        for act in acts:
            if not act.date_deadline:
                continue
            if act.date_deadline < today:
                overdue += 1
            elif act.date_deadline == today:
                due_today += 1
            else:
                upcoming += 1
        total = overdue + due_today + upcoming
        points = [
            {'key': 'overdue', 'label': 'Overdue', 'value': overdue, 'color': 'red'},
            {'key': 'today', 'label': 'Today', 'value': due_today, 'color': 'orange'},
            {'key': 'upcoming', 'label': 'Upcoming', 'value': upcoming, 'color': 'green'},
        ]
        return {
            'points': points,
            'total': total,
            'viewAction': _list_action('My Activities', 'mail.activity', [('user_id', '=', uid)]),
        }
    except Exception:
        _logger.warning('Failed to fetch activity trend data', exc_info=True)
        return {'points': [], 'total': 0}


def _fetch_sales_trend(env, uid):
    try:
        today = date.today()
        # Build last 6 month buckets oldest -> newest
        month_starts = []
        y = today.year
        m = today.month
        for offset in range(5, -1, -1):
            mm = m - offset
            yy = y
            while mm <= 0:
                mm += 12
                yy -= 1
            month_starts.append(date(yy, mm, 1))

        last_start = month_starts[0]
        orders = env['sale.order'].search([
            ('user_id', '=', uid),
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', str(last_start)),
        ])

        sums = {}
        counts = {}
        for start in month_starts:
            key = f'{start.year:04d}-{start.month:02d}'
            sums[key] = 0.0
            counts[key] = 0

        for order in orders:
            if not order.date_order:
                continue
            d = order.date_order.date()
            key = f'{d.year:04d}-{d.month:02d}'
            if key in sums:
                sums[key] += order.amount_total or 0.0
                counts[key] += 1

        points = []
        for start in month_starts:
            key = f'{start.year:04d}-{start.month:02d}'
            points.append({
                'key': key,
                'label': start.strftime('%b'),
                'amount': round(sums[key], 2),
                'count': counts[key],
            })

        total_amount = sum(p['amount'] for p in points)
        return {
            'points': points,
            'total_amount': total_amount,
            'currency_symbol': env.company.currency_id.symbol or '',
            'viewAction': _list_action('Sales Orders', 'sale.order', [
                ('user_id', '=', uid),
                ('state', 'in', ['sale', 'done']),
            ]),
            'createAction': _create_action('New Quotation', 'sale.order'),
        }
    except Exception:
        _logger.warning('Failed to fetch sales trend data', exc_info=True)
        return {'points': [], 'total_amount': 0.0, 'currency_symbol': ''}


def _fetch_account_aged_receivables(env, uid):
    try:
        today = date.today()
        moves = env['account.move'].search(
            [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_user_id', '=', uid),
            ],
            order='invoice_date_due asc, invoice_date asc',
        )
        buckets = [
            {'key': '0_30', 'label': '0-30 days', 'amount': 0.0, 'count': 0},
            {'key': '31_60', 'label': '31-60 days', 'amount': 0.0, 'count': 0},
            {'key': '61_90', 'label': '61-90 days', 'amount': 0.0, 'count': 0},
            {'key': '90_plus', 'label': '90+ days', 'amount': 0.0, 'count': 0},
        ]
        items = []
        for move in moves:
            base_date = move.invoice_date_due or move.invoice_date or move.date
            age_days = max(0, (today - base_date).days) if base_date else 0
            if age_days <= 30:
                bucket = buckets[0]
            elif age_days <= 60:
                bucket = buckets[1]
            elif age_days <= 90:
                bucket = buckets[2]
            else:
                bucket = buckets[3]
            residual = move.amount_residual or 0.0
            bucket['amount'] += residual
            bucket['count'] += 1
            if len(items) < 6:
                items.append({
                    'id': move.id,
                    'name': move.name or '',
                    'partner_name': move.partner_id.name or '',
                    'amount_residual': residual,
                    'currency_symbol': move.currency_id.symbol or '',
                    'age_days': age_days,
                    'record_url': f'/web#id={move.id}&model=account.move&view_type=form',
                    'action': _form_action(move.display_name or 'Invoice', 'account.move', move.id),
                })
        total = len(moves)
        return {
            'buckets': buckets,
            'items': items,
            'count': total,
            'currency_symbol': env.company.currency_id.symbol or '',
            'viewAction': _list_action('Aged Receivables', 'account.move', [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_user_id', '=', uid),
            ]),
        }
    except Exception:
        _logger.warning('Failed to fetch aged receivables data', exc_info=True)
        return {'buckets': [], 'items': [], 'count': 0, 'currency_symbol': ''}


def _fetch_account_cashflow(env, uid):
    try:
        today = date.today()
        cutoff = today + timedelta(days=30)
        company_currency = env.company.currency_id.symbol or ''

        bank_balance = 0.0
        try:
            accounts = env['account.account'].search([
                ('company_id', '=', env.company.id),
                ('account_type', 'in', ['asset_cash', 'asset_bank']),
            ])
            bank_balance = sum(accounts.mapped('balance')) if accounts else 0.0
        except Exception:
            bank_balance = 0.0

        # Incoming: customer invoices due in the next 30 days.
        incoming = env['account.move'].search(
            [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_user_id', '=', uid),
                ('invoice_date_due', '>=', str(today)),
                ('invoice_date_due', '<=', str(cutoff)),
            ],
            order='invoice_date_due asc',
            limit=5,
        )
        # Outgoing: vendor bills due in the next 30 days.
        # Note: vendor bills do not use invoice_user_id, so we scope to the
        # current company only (handled automatically by the ORM).
        outgoing = env['account.move'].search(
            [
                ('company_id', 'in', env.companies.ids),
                ('move_type', '=', 'in_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '>=', str(today)),
                ('invoice_date_due', '<=', str(cutoff)),
            ],
            order='invoice_date_due asc',
            limit=5,
        )

        expected_in = sum((move.amount_residual or 0.0) for move in incoming)
        expected_out = sum((move.amount_residual or 0.0) for move in outgoing)
        items = []
        for move in incoming:
            items.append({
                'id': f'in-{move.id}',
                'name': move.name or '',
                'partner_name': move.partner_id.name or '',
                'amount': move.amount_residual or 0.0,
                'currency_symbol': move.currency_id.symbol or company_currency,
                'due_date': _format_date(move.invoice_date_due),
                'direction': 'in',
                'record_url': f'/web#id={move.id}&model=account.move&view_type=form',
                'action': _form_action(move.display_name or 'Invoice', 'account.move', move.id),
            })
        for move in outgoing:
            items.append({
                'id': f'out-{move.id}',
                'name': move.name or '',
                'partner_name': move.partner_id.name or '',
                'amount': move.amount_residual or 0.0,
                'currency_symbol': move.currency_id.symbol or company_currency,
                'due_date': _format_date(move.invoice_date_due),
                'direction': 'out',
                'record_url': f'/web#id={move.id}&model=account.move&view_type=form',
                'action': _form_action(move.display_name or 'Bill', 'account.move', move.id),
            })

        return {
            'bank_balance': bank_balance,
            'expected_in': expected_in,
            'expected_out': expected_out,
            'net': bank_balance + expected_in - expected_out,
            'items': items[:8],
            'count': len(items),
            'currency_symbol': company_currency,
            'viewAction': _list_action('Cash Flow Summary', 'account.move', [
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '>=', str(today)),
                ('invoice_date_due', '<=', str(cutoff)),
            ]),
        }
    except Exception:
        _logger.warning('Failed to fetch cashflow data', exc_info=True)
        return {
            'bank_balance': 0.0,
            'expected_in': 0.0,
            'expected_out': 0.0,
            'net': 0.0,
            'items': [],
            'count': 0,
            'currency_symbol': '',
        }


_FETCHERS = {
    'activity_trend':      _fetch_activity_trend,
    'inventory_reorder':  _fetch_inventory_reorder,
    'inventory_receipts': _fetch_inventory_receipts,
    'purchase_rfq':       _fetch_purchase_rfq,
    'purchase_orders':    _fetch_purchase_orders,
    'sale_quotations':    _fetch_sale_quotations,
    'sale_to_invoice':    _fetch_sale_to_invoice,
    'sales_trend':        _fetch_sales_trend,
    'hr_leaves':          _fetch_hr_leaves,
    'hr_attendance':      _fetch_hr_attendance,
    'project_tasks':      _fetch_project_tasks,
    'project_deadlines':  _fetch_project_deadlines,
    'mrp_production':     _fetch_mrp_production,
    'account_cashflow':   _fetch_account_cashflow,
    'account_aged_recv':  _fetch_account_aged_receivables,
}


class HomeWidgetsController(http.Controller):

    def _installed_modules(self):
        mods = request.env['ir.module.module'].sudo().search([('state', '=', 'installed')])
        return {m.name for m in mods}

    @http.route('/web/home_dashboard/widgets', type='jsonrpc', auth='user')
    def get_widgets(self):
        env = request.env
        uid = env.uid
        installed = self._installed_modules()

        rows = env['theme.home.widget'].get_user_widgets()
        active_map = {r.widget_id: r for r in rows}

        available = []
        for wdef in WIDGET_CATALOG:
            mod = wdef.get('module')
            is_installed = mod is None or mod in installed
            row = active_map.get(wdef['id'])
            available.append({
                'id': wdef['id'],
                'widget_id': wdef['id'],
                'label': wdef['label'],
                'description': wdef['description'],
                'icon': wdef['icon'],
                'color': wdef['color'],
                'group': wdef['group'],
                'default_col_span': wdef['default_col_span'],
                'installed': is_installed,
                'active': bool(row),
                'row_id': row.id if row else None,
                'position': row.position if row else 999,
                'col_span': row.col_span if row else wdef['default_col_span'],
                'config': _parse_widget_config(row.config_json) if row else {},
            })

        active = []
        catalog_by_id = {w['id']: w for w in WIDGET_CATALOG}
        for row in rows:
            if _is_custom_widget_id(row.widget_id):
                config = _parse_widget_config(row.config_json)
                active.append({
                    'id': row.widget_id,
                    'widget_id': row.widget_id,
                    'label': config.get('title') or 'Custom Widget',
                    'description': config.get('model') or 'User-defined widget',
                    'icon': config.get('icon') or ('fa-table' if config.get('widget_type') == 'table' else 'fa-chart-bar'),
                    'color': config.get('color') or 'brand',
                    'group': 'Custom',
                    'default_col_span': row.col_span,
                    'installed': True,
                    'active': True,
                    'row_id': row.id,
                    'position': row.position,
                    'col_span': row.col_span,
                    'config': config,
                    'data': _fetch_custom_widget(env, row),
                    'missing': False,
                    'custom': True,
                })
                continue

            wdef = catalog_by_id.get(row.widget_id)
            if not wdef:
                active.append({
                    'id': row.widget_id,
                    'widget_id': row.widget_id,
                    'label': row.widget_id,
                    'description': 'This widget is no longer available.',
                    'icon': 'fa-exclamation-triangle',
                    'color': 'red',
                    'group': 'Missing',
                    'default_col_span': row.col_span,
                    'installed': False,
                    'active': True,
                    'row_id': row.id,
                    'position': row.position,
                    'col_span': row.col_span,
                    'config': _parse_widget_config(row.config_json),
                    'data': None,
                    'missing': True,
                })
                continue

            mod = wdef.get('module')
            installed_for_widget = mod is None or mod in installed
            widget_data = None
            fetcher = _FETCHERS.get(row.widget_id) if installed_for_widget else None
            if fetcher:
                widget_data = fetcher(env, uid)
            active.append({
                **wdef,
                'id': row.widget_id,
                'widget_id': row.widget_id,
                'installed': installed_for_widget,
                'active': True,
                'row_id': row.id,
                'position': row.position,
                'col_span': row.col_span,
                'config': _parse_widget_config(row.config_json),
                'data': widget_data,
                'missing': not installed_for_widget,
            })

        return {'available': available, 'active': active}

    @http.route('/web/home_dashboard/custom/models', type='jsonrpc', auth='user')
    def custom_widget_models(self):
        models = request.env['ir.model'].sudo().search([
            ('transient', '=', False),
            ('model', 'not ilike', 'ir.%'),
        ], order='name asc', limit=300)
        result = []
        for model in models:
            model_name = model.model
            if model_name not in request.env:
                continue
            try:
                Model = request.env[model_name]
                if not _has_model_read_access(Model):
                    continue
            except Exception:
                continue
            result.append({'model': model_name, 'name': model.name or model_name})
        return {'models': result}

    @http.route('/web/home_dashboard/custom/fields', type='jsonrpc', auth='user')
    def custom_widget_fields(self, model):
        if not model or model not in request.env:
            return {'fields': []}
        Model = request.env[model]
        try:
            if not _has_model_read_access(Model):
                return {'fields': []}
        except Exception:
            return {'fields': []}
        fields = []
        for name, field in sorted(Model._fields.items(), key=lambda item: item[1].string or item[0]):
            if name == 'id' or field.type in ('binary', 'html', 'one2many', 'many2many'):
                continue
            fields.append({
                'name': name,
                'label': field.string or name,
                'type': field.type,
                'numeric': field.type in ('integer', 'float', 'monetary'),
            })
        return {'fields': fields}

    @http.route('/web/home_dashboard/widgets/custom_create', type='jsonrpc', auth='user')
    def create_custom_widget(self, config=None):
        if not isinstance(config, dict):
            return {'success': False, 'error': 'Invalid widget configuration'}
        model = config.get('model')
        if not model or model not in request.env:
            return {'success': False, 'error': 'Choose a valid model'}
        widget_type = config.get('widget_type') or 'table'
        if widget_type not in ('table', 'kpi'):
            return {'success': False, 'error': 'Unsupported widget type'}
        title = (config.get('title') or 'Custom Widget').strip()[:80]
        safe_config = {
            'title': title,
            'model': model,
            'widget_type': widget_type,
            'limit': _safe_int(config.get('limit'), default=5, minimum=1, maximum=25),
            'domain': _normalize_domain(config.get('domain')),
            'icon': config.get('icon') or ('fa-table' if widget_type == 'table' else 'fa-chart-bar'),
        }
        if widget_type == 'table':
            fields = config.get('fields') or []
            safe_config['fields'] = [field for field in fields if isinstance(field, str)][:6]
        else:
            safe_config['aggregation'] = config.get('aggregation') if config.get('aggregation') in ('count', 'sum', 'avg') else 'count'
            safe_config['measure_field'] = config.get('measure_field') or ''

        env = request.env
        last = env['theme.home.widget'].search([('user_id', '=', env.uid)], order='position desc', limit=1)
        row = env['theme.home.widget'].create({
            'user_id': env.uid,
            'widget_id': f"custom_{uuid.uuid4().hex[:12]}",
            'position': (last.position + 1) if last else 0,
            'col_span': '2' if widget_type == 'table' else '1',
            'config_json': json.dumps(safe_config, ensure_ascii=False, separators=(',', ':')),
        })
        return {'success': True, 'widget_id': row.widget_id}

    @http.route('/web/home_dashboard/widgets/add', type='jsonrpc', auth='user')
    def add_widget(self, widget_id, col_span=None):
        wdef = next((w for w in WIDGET_CATALOG if w['id'] == widget_id), None)
        if not wdef:
            return {'success': False, 'error': 'Unknown widget'}
        env = request.env
        # Search including inactive records to avoid UNIQUE constraint violations
        # when re-adding a previously removed widget.
        existing = env['theme.home.widget'].with_context(active_test=False).search(
            [('user_id', '=', env.uid), ('widget_id', '=', widget_id)], limit=1
        )
        last = env['theme.home.widget'].search(
            [('user_id', '=', env.uid)], order='position desc', limit=1
        )
        next_pos = (last.position + 1) if last else 0
        if existing:
            existing.write({
                'active': True,
                'col_span': col_span or wdef['default_col_span'],
                'position': next_pos,
            })
        else:
            try:
                env['theme.home.widget'].create({
                    'user_id': env.uid,
                    'widget_id': widget_id,
                    'position': next_pos,
                    'col_span': col_span or wdef['default_col_span'],
                })
            except Exception:
                # Concurrent request won the race; activate that record instead.
                env.cr.rollback()
                existing = env['theme.home.widget'].with_context(active_test=False).search(
                    [('user_id', '=', env.uid), ('widget_id', '=', widget_id)], limit=1
                )
                if existing:
                    existing.write({'active': True, 'col_span': col_span or wdef['default_col_span']})
        return {'success': True}

    @http.route('/web/home_dashboard/widgets/restore_defaults', type='jsonrpc', auth='user')
    def restore_default_widgets(self):
        request.env['theme.home.widget'].restore_default_widgets()
        return {'success': True}

    @http.route('/web/home_dashboard/widgets/remove', type='jsonrpc', auth='user')
    def remove_widget(self, widget_id):
        env = request.env
        record = env['theme.home.widget'].search(
            [('user_id', '=', env.uid), ('widget_id', '=', widget_id)], limit=1
        )
        if record:
            record.write({'active': False})
        return {'success': True}

    @http.route('/web/home_dashboard/widgets/reorder', type='jsonrpc', auth='user')
    def reorder_widgets(self, order):
        env = request.env
        for item in order:
            widget_id = item.get('widget_id')
            position = item.get('position')
            if not isinstance(position, int):
                try:
                    position = int(position)
                except (TypeError, ValueError):
                    continue
            record = env['theme.home.widget'].search(
                [('user_id', '=', env.uid), ('widget_id', '=', widget_id)], limit=1
            )
            if record:
                record.write({'position': position, 'col_span': item.get('col_span', record.col_span)})
        return {'success': True}

    @http.route('/web/home_dashboard/widgets/resize', type='jsonrpc', auth='user')
    def resize_widget(self, widget_id, col_span):
        env = request.env
        record = env['theme.home.widget'].search(
            [('user_id', '=', env.uid), ('widget_id', '=', widget_id)], limit=1
        )
        if record and col_span in ('1', '2', '3'):
            record.write({'col_span': col_span})
        return {'success': True}

    @http.route('/web/home_dashboard/widgets/configure', type='jsonrpc', auth='user')
    def configure_widget(self, widget_id, config=None):
        env = request.env
        record = env['theme.home.widget'].search(
            [('user_id', '=', env.uid), ('widget_id', '=', widget_id)], limit=1
        )
        if not record:
            return {'success': False, 'error': 'Widget not found'}

        if config is None:
            config = {}
        if not isinstance(config, dict):
            return {'success': False, 'error': 'Invalid configuration'}

        record.write({'config_json': json.dumps(config, ensure_ascii=False, separators=(',', ':'))})
        return {'success': True}

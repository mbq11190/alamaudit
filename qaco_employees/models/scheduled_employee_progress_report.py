# from odoo import models, fields, api
# import logging
# from datetime import datetime
# import statistics
#
# _logger = logging.getLogger(__name__)
#
# class ScheduledEmployeeProgressReport(models.Model):
#     _name = 'scheduled.employee.progress.report'
#     _inherit = ['mail.thread']
#     _description = "Scheduled Employee Progress Report"
#
#     def _get_cycle_time(self, task):
#         """
#         Compute cycle time (in days) for a task.
#         For corporate tasks (qaco.corporate), try date_last_stage_update first, then write_date.
#         For audit tasks (qaco.audit), if date_last_stage_update is not set or write_date == create_date,
#         return 0 as a fallback.
#         """
#         if task.create_date:
#             delta = None
#             if task._name == 'qaco.corporate':
#                 if task.date_last_stage_update:
#                     delta = task.date_last_stage_update - task.create_date
#                 elif task.write_date and task.write_date != task.create_date:
#                     delta = task.write_date - task.create_date
#             elif task._name == 'qaco.audit':
#                 if hasattr(task, 'date_last_stage_update') and task.date_last_stage_update:
#                     delta = task.date_last_stage_update - task.create_date
#                 elif task.write_date and task.write_date != task.create_date:
#                     delta = task.write_date - task.create_date
#                 # If no meaningful delta is found for an audit task, return 0 days.
#                 if delta is None:
#                     return 0
#             if delta:
#                 return delta.total_seconds() / 86400.0
#         return 0
#
#     def generate_employee_progress_report(self):
#         """
#         Generate and send an employee task report including:
#          - Department (merged for each group)
#          - Employee Name
#          - Completed Tasks (from both corporate and audit tasks, only tasks in 'done' stage)
#          - Pending Tasks
#          - Total Assigned Tasks
#          - Completion Ratio (%)
#          - Median Completion Time (Days) for completed tasks
#
#          Tasks are fetched from both the corporate model (qaco.corporate) and the audit model (qaco.audit).
#          The report groups rows by department (departments sorted by their total tasks in descending order)
#          and uses alternate shading with professional styling.
#         """
#         target_clients = self.env['res.partner'].search([
#             ('name', 'in', ['BAKERTILLY-RDF', 'BAKERTILLY-STATELIFE'])
#         ]).ids
#
#         if not target_clients:
#             _logger.warning("No client records found for target clients.")
#             return
#
#         employees = self.env['hr.employee'].search([
#             ('latest_deputation_client_id', 'in', target_clients),
#             '|',
#             ('parent_id', '=', False),
#             ('parent_id', '!=', False)
#         ])
#         if not employees:
#             _logger.warning("No employees found for the given clients.")
#             return
#
#         employee_ids = employees.ids
#         corporate_tasks = self.env['qaco.corporate'].search([('employee_id', 'in', employee_ids)])
#         audit_tasks = self.env['qaco.audit'].search([('employee_id', 'in', employee_ids)])
#
#         _logger.info("Total Corporate Tasks Found: %s", len(corporate_tasks))
#         _logger.info("Total Audit Tasks Found: %s", len(audit_tasks))
#         for task in corporate_tasks:
#             task_name = getattr(task, 'task_name', 'UNKNOWN')
#             _logger.info("Corporate Task: %s, Employee: %s, Stage: %s",
#                          task_name, task.employee_id.name, task.stage_id.name)
#         for task in audit_tasks:
#             task_name = getattr(task, 'task_name', 'UNKNOWN')
#             _logger.info("Audit Task: %s, Employee: %s, Stage: %s",
#                          task_name, task.employee_id.name, task.stage_id.name)
#
#         if not (corporate_tasks or audit_tasks):
#             _logger.warning("No tasks found for selected employees.")
#             return
#
#         completed_stage = 'done'
#         employee_task_data = []
#
#         for employee in employees:
#             corp_tasks = corporate_tasks.filtered(lambda t: t.employee_id.id == employee.id)
#             audit_emp_tasks = audit_tasks.filtered(lambda t: t.employee_id.id == employee.id)
#
#             completed_corp = corp_tasks.filtered(lambda t: t.stage_id.name.strip().lower() == completed_stage)
#             pending_corp = corp_tasks.filtered(lambda t: t.stage_id.name.strip().lower() != completed_stage)
#             completed_audit = audit_emp_tasks.filtered(lambda t: t.stage_id.name.strip().lower() == completed_stage)
#             pending_audit = audit_emp_tasks.filtered(lambda t: t.stage_id.name.strip().lower() != completed_stage)
#
#             total_completed = len(completed_corp) + len(completed_audit)
#             total_pending = len(pending_corp) + len(pending_audit)
#             total_tasks = total_completed + total_pending
#
#             cycle_times = []
#             for task in completed_corp:
#                 ct = self._get_cycle_time(task)
#                 if ct is not None:
#                     cycle_times.append(ct)
#             for task in completed_audit:
#                 ct = self._get_cycle_time(task)
#                 if ct is not None:
#                     cycle_times.append(ct)
#             median_cycle_time = statistics.median(cycle_times) if cycle_times else 0
#             task_completion_ratio = (total_completed / total_tasks) if total_tasks > 0 else 0
#
#             department = employee.department_id.name if employee.department_id else "Other"
#
#             employee_task_data.append({
#                 'department': department,
#                 'name': employee.name,
#                 'completed_tasks': total_completed,
#                 'pending_tasks': total_pending,
#                 'total_tasks': total_tasks,
#                 'task_completion_ratio': task_completion_ratio,
#                 'median_cycle_time': median_cycle_time,
#             })
#
#         dept_groups = {}
#         for emp in employee_task_data:
#             dept = emp['department']
#             if dept not in dept_groups:
#                 dept_groups[dept] = {'employees': [], 'dept_total': 0}
#             dept_groups[dept]['employees'].append(emp)
#             dept_groups[dept]['dept_total'] += emp['total_tasks']
#
#         sorted_dept_groups = sorted(dept_groups.items(),
#                                     key=lambda item: item[1]['dept_total'],
#                                     reverse=True)
#         for dept, group in sorted_dept_groups:
#             group['employees'] = sorted(group['employees'], key=lambda x: x['name'])
#
#         report_content = """
#         <html>
#         <head>
#             <style>
#                 body { font-family: Arial, sans-serif; }
#                 h2 { text-align: center; color: #2E4053; }
#                 table { width: 100%; border-collapse: collapse; }
#                 th { background-color: #2980B9; color: white; padding: 10px; }
#                 td { padding: 10px; border: 1px solid #ddd; vertical-align: middle; }
#             </style>
#         </head>
#         <body>
#         <h2>Employee Task Report (Grouped by Department)</h2>
#         <table>
#             <tr style="background-color: #f2f2f2;">
#                 <th>Department</th>
#                 <th>Employee Name</th>
#                 <th>Completed Tasks</th>
#                 <th>Pending Tasks</th>
#                 <th>Total Assigned Tasks</th>
#                 <th>Completion Ratio (%)</th>
#                 <th>Median Completion Time (Days)</th>
#             </tr>
#         """
#
#         group_colors = ["#e6f2ff", "#f9f9f9"]
#         for idx, (dept, group) in enumerate(sorted_dept_groups):
#             group_color = group_colors[idx % 2]
#             employees_in_group = group['employees']
#             rowspan = len(employees_in_group)
#             for j, emp in enumerate(employees_in_group):
#                 ratio_percentage = emp['task_completion_ratio'] * 100
#                 if j == 0:
#                     report_content += f"""
#                     <tr style="background-color: {group_color};">
#                         <td rowspan="{rowspan}"><strong>{dept}</strong></td>
#                         <td>{emp['name']}</td>
#                         <td style="text-align: center;">{emp['completed_tasks']}</td>
#                         <td style="text-align: center;">{emp['pending_tasks']}</td>
#                         <td style="text-align: center;">{emp['total_tasks']}</td>
#                         <td style="text-align: center;">{ratio_percentage:.2f}%</td>
#                         <td style="text-align: center;">{emp['median_cycle_time']:.2f}</td>
#                     </tr>
#                     """
#                 else:
#                     report_content += f"""
#                     <tr style="background-color: {group_color};">
#                         <td>{emp['name']}</td>
#                         <td style="text-align: center;">{emp['completed_tasks']}</td>
#                         <td style="text-align: center;">{emp['pending_tasks']}</td>
#                         <td style="text-align: center;">{emp['total_tasks']}</td>
#                         <td style="text-align: center;">{ratio_percentage:.2f}%</td>
#                         <td style="text-align: center;">{emp['median_cycle_time']:.2f}</td>
#                     </tr>
#                     """
#         report_content += """
#         </table>
#         </body>
#         </html>
#         """
#
#         if employee_task_data:
#             mail_values = {
#                 'subject': 'Scheduled Employee Task Report (Grouped by Department)',
#                 'body_html': report_content,
#                 'email_to': 'mbq11190@gmail.com',
#                 'email_from': self.env.user.email,
#             }
#             mail = self.env['mail.mail'].create(mail_values)
#             _logger.info("Mail Created: %s", mail_values)
#
#             try:
#                 mail.send()
#                 _logger.info("Employee task report email sent successfully.")
#             except Exception as e:
#                 _logger.error("Failed to send email: %s", str(e))
#         else:
#             _logger.warning("No report sent as no valid employee task data was found.")
#
#     def _cron_generate_employee_progress_report(self):
#         """Cron Job to automatically generate and send the Employee Task Report."""
#         self.generate_employee_progress_report()

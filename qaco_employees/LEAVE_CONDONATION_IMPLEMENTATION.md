# Leave Condonation System - Implementation Summary

## Overview
Complete implementation of an enhanced Leave Condonation system integrated with payroll processing. The system allows employees to request condonation of leave deductions from their payroll, with approval from Muhammad Bin Qasim, and subsequent processing for salary refunds.

## Key Features Implemented

### 1. Leave Condonation Request Form (`qaco_employees` module)

#### Model Changes (`leave_condonation.py`)
- **New Fields:**
  - `condonation_month`: Selection field for choosing the month (last 7 months)
  - `reason`: Required text field for detailed explanation
  - `total_leave_deduction`: Computed field showing total deduction amount

- **Workflow:**
  1. Employee selects condonation month
  2. Clicks "Load Deductions" button
  3. System fetches leave deductions from `qaco.payroll.line` for that month
  4. Employee writes reason for condonation
  5. Submits for approval
  6. Professional email sent to Muhammad Bin Qasim with:
     - Approve, Reject, Revert, View buttons
     - Detailed table of payroll deductions
     - Employee information and reason
  7. Muhammad Bin Qasim approves/rejects
  8. Employee notified of decision

#### Leave Condonation Line Model (`leave.condonation.line`)
- Stores payroll data in readonly format:
  - `payroll_line_id`: Reference to original payroll line
  - `employee_id`, `department_id`, `designation_id`
  - `gross_salary`, `allowance_amount`, `attendance_days`
  - `leave_deduction_amount`: The key amount to be refunded
  - `net_salary`, `payroll_month`, `payroll_date_from/to`

#### Approval System
- **Single Approver:** Muhammad Bin Qasim user (searched by login='mbqasim' or name containing 'Muhammad Bin Qasim')
- Removed multi-level approval workflow
- Only MBQ or administrators can approve condonations

#### Updated Views (`leave_condonation_views.xml`)
- Enhanced form view with:
  - Month selection dropdown
  - "Load Deductions" button
  - Reason text area
  - Payroll deduction details in tabular format
  - Total leave deduction display
  - Approval status tab
- Improved tree view with color coding:
  - Green: Approved
  - Red: Rejected
  - Yellow: Submitted
  - Gray: Reverted
- Enhanced search filters and grouping

### 2. Leave Condonation Processing (`qaco_payroll` module)

#### New Model (`qaco_leave_condonation_processing.py`)
- **Purpose:** Process approved condonations for salary refunds
- **Main Fields:**
  - `sequence`: Auto-generated (LCP00001, LCP00002, etc.)
  - `processing_month`: Month for which to process condonations
  - `processing_date`: Date of processing
  - `state`: draft → confirmed → processed → cancelled
  - `total_refund_amount`: Sum of all refunds
  - `total_employees`: Count of employees receiving refunds

#### Processing Line Model (`qaco.leave.condonation.processing.line`)
- Groups approved condonations by employee
- **Fields:**
  - `employee_id`, `department_id`, `designation_id`
  - `refund_amount`: Total amount to refund
  - `condonation_count`: Number of condonations
  - `condonation_references`: Comma-separated sequence numbers
  - `condonation_ids`: Many2many link to original condonations
  - `bank_account_id`: Employee's bank account for payment
  - `is_paid`, `paid_date`: Payment tracking

#### Workflow:
1. Create new processing record
2. Select processing month
3. Click "Load Approved Condonations"
4. System fetches all approved condonations for that month
5. Groups by employee and calculates total refunds
6. Confirm the processing
7. Mark as processed when payments are made
8. Each line can be marked individually as paid

#### Views (`leave_condonation_processing_views.xml`)
- **Form View:**
  - Summary section showing totals
  - Processing lines with employee details
  - Bank account information
  - Payment tracking checkboxes
  - State management buttons
- **Tree View:** Color-coded by status
- **Search View:** Filters and grouping options
- **Menu:** Under Payroll menu (sequence 70)

### 3. Email System

#### Professional Email Template
- **Embedded in Model:** Email template built directly in `_send_submit_email()` method
- **Features:**
  - Action buttons (Approve, Reject, Revert, View)
  - Employee and request details
  - Reason for condonation highlighted
  - **Detailed Payroll Table** showing:
    - Employee name, department, designation
    - Payroll month and attendance days
    - Basic salary, allowances
    - Leave deduction amount (highlighted in red)
    - Net salary
    - Total row with sum of deductions
  - Professional styling with blue theme

### 4. Security & Permissions

#### `qaco_employees/security/ir.model.access.csv`
```csv
access_leave_condonation,leave.condonation,model_leave_condonation,base.group_user,1,1,1,0
access_leave_condonation_manager,leave.condonation,model_leave_condonation,qaco_employees.group_qaco_timeoff_manager,1,1,1,1
access_leave_condonation_approval,leave.condonation.approval,model_leave_condonation_approval,base.group_user,1,0,1,0
access_leave_condonation_approval_manager,leave.condonation.approval,model_leave_condonation_approval,qaco_employees.group_qaco_timeoff_manager,1,1,1,1
access_leave_condonation_line,leave.condonation.line,model_leave_condonation_line,base.group_user,1,0,0,0
access_leave_condonation_line_manager,leave.condonation.line,model_leave_condonation_line,qaco_employees.group_qaco_timeoff_manager,1,1,1,1
```

#### `qaco_payroll/security/ir.model.access.csv`
```csv
access_qaco_leave_condonation_processing,qaco.leave.condonation.processing,model_qaco_leave_condonation_processing,base.group_user,1,1,1,1
access_qaco_leave_condonation_processing_line,qaco.leave.condonation.processing.line,model_qaco_leave_condonation_processing_line,base.group_user,1,1,1,1
```

### 5. Data Files

#### New Sequence (`leave_condonation_processing_sequence.xml`)
```xml
<record id="seq_leave_condonation_processing" model="ir.sequence">
    <field name="name">Leave Condonation Processing Sequence</field>
    <field name="code">qaco.leave.condonation.processing</field>
    <field name="prefix">LCP</field>
    <field name="padding">5</field>
</record>
```

### 6. Manifest Updates

#### `qaco_employees/__manifest__.py`
- No changes needed (existing files already included)

#### `qaco_payroll/__manifest__.py`
```python
'data': [
    # ... existing entries ...
    'data/leave_condonation_processing_sequence.xml',  # NEW
    # ... existing entries ...
    'views/leave_condonation_processing_views.xml',    # NEW
    'views/menu_view.xml',
],
```

## Files Modified

### qaco_employees Module:
1. ✅ `models/leave_condonation.py` - Complete rewrite
2. ✅ `views/leave_condonation_views.xml` - Enhanced views
3. ✅ `security/ir.model.access.csv` - Uncommented and updated

### qaco_payroll Module:
4. ✅ `models/qaco_leave_condonation_processing.py` - NEW FILE
5. ✅ `models/__init__.py` - Added import
6. ✅ `views/leave_condonation_processing_views.xml` - NEW FILE
7. ✅ `data/leave_condonation_processing_sequence.xml` - NEW FILE
8. ✅ `security/ir.model.access.csv` - Added new models
9. ✅ `__manifest__.py` - Updated data files list

## User Guide

### For Employees:

1. **Create Leave Condonation Request:**
   - Navigate to Time Off → Leave Condonation
   - Click "Create"
   - Select the condonation month from dropdown
   - Click "Load Deductions" button
   - Review the loaded payroll deduction details
   - Write a detailed reason for requesting condonation
   - Click "Submit for Approval"

2. **Track Status:**
   - Check the Status field: Draft → Submitted → Approved/Rejected
   - View approval status in the "Approval Status" tab
   - Receive email notification when approved/rejected

### For Muhammad Bin Qasim (Approver):

1. **Receive Email:**
   - Email contains all request details and payroll table
   - Click "Approve" button in email to approve directly
   - Or click "View Request" to open in Odoo

2. **Review in Odoo:**
   - Check employee's reason
   - Review payroll deduction details
   - Click "Approve" or "Reject" button

### For Payroll Processors:

1. **Process Condonations:**
   - Navigate to Payroll → Leave Condonation Processing
   - Click "Create"
   - Select processing month
   - Click "Load Approved Condonations"
   - Review all employees and refund amounts
   - Select bank accounts for each employee
   - Click "Confirm"
   - Process payments
   - Mark individual lines as "Paid" with payment date
   - Click "Mark as Processed" when complete

2. **Track Processing:**
   - View all processing batches
   - Filter by status: Draft, Confirmed, Processed
   - Group by month to see historical data

## Technical Details

### Integration Points:
- **Payroll Line Data:** Reads from `qaco.payroll.line` model
- **Employee Bank Accounts:** Uses `employee.bank` model
- **Leave Summary:** May reference `leave.summary` for additional data
- **Email System:** Uses Odoo's `mail.mail` for notifications

### Validation Rules:
- Employee can only create condonation for themselves
- Can only load deductions in draft state
- Must have leave deductions in selected month
- Reason is required before submission
- Only MBQ or admin can approve
- Processing can only load approved condonations

### State Transitions:
**Leave Condonation:** draft → submitted → approved/rejected/reverted
**Processing:** draft → confirmed → processed/cancelled

## Testing Checklist

- [ ] Employee can create leave condonation request
- [ ] Month selection shows last 7 months
- [ ] Load deductions button fetches correct payroll data
- [ ] Payroll lines display all required fields
- [ ] Reason field is required for submission
- [ ] Email is sent to Muhammad Bin Qasim user
- [ ] Email contains action buttons and payroll table
- [ ] MBQ can approve/reject from email
- [ ] MBQ can approve/reject from Odoo interface
- [ ] Employee receives approval/rejection notification
- [ ] Processing form loads approved condonations
- [ ] Condonations are grouped by employee correctly
- [ ] Refund amounts are calculated correctly
- [ ] Bank account selection works
- [ ] Payment tracking (is_paid, paid_date) functions
- [ ] State transitions work correctly
- [ ] Security permissions are enforced

## Notes

- **Muhammad Bin Qasim User:** Must exist in system with login='mbqasim' or name containing 'Muhammad Bin Qasim'
- **Payroll Integration:** Requires `qaco.payroll.line` records with `leave_deduction_amount > 0`
- **Email Configuration:** Ensure email settings are configured in Odoo
- **Transfer Button:** Mentioned in requirements but not implemented (same as leave adjustment pattern)

## Future Enhancements (Optional)

1. Add transfer functionality for reassigning approvals
2. Add reporting/analytics for condonation trends
3. Add bulk approval functionality
4. Add automatic email reminders for pending approvals
5. Add export functionality for processing records
6. Add integration with accounting for payment vouchers

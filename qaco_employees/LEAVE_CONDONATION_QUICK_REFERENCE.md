# Leave Condonation System - Quick Reference

## What Changed?

### Leave Condonation Form (Employee Side)
**Before:** Manual entry of absent days
**After:** Automatic loading of leave deductions from payroll

**New Flow:**
1. Select month → Load deductions → Write reason → Submit → Approval

**New Fields:**
- Condonation Month (dropdown showing last 7 months)
- Reason (required text area)
- Payroll Deduction Lines (auto-loaded, readonly table)

**Approver:** Only Muhammad Bin Qasim (hardcoded)

### Leave Condonation Processing (Payroll Side)
**NEW MODULE:** Under Payroll menu

**Purpose:** Process approved condonations to refund salary deductions

**Flow:**
1. Create processing record
2. Select month
3. Load approved condonations
4. Assign bank accounts
5. Confirm → Process → Mark as paid

## File Changes Summary

| File | Status | Description |
|------|--------|-------------|
| `Qacov17/qaco_employees/models/leave_condonation.py` | ✅ MODIFIED | Complete rewrite with new logic |
| `Qacov17/qaco_employees/views/leave_condonation_views.xml` | ✅ MODIFIED | Enhanced UI |
| `Qacov17/qaco_employees/security/ir.model.access.csv` | ✅ MODIFIED | Enabled access |
| `Qacov17/qaco_payroll/models/qaco_leave_condonation_processing.py` | ✅ NEW | Processing model |
| `Qacov17/qaco_payroll/models/__init__.py` | ✅ MODIFIED | Added import |
| `Qacov17/qaco_payroll/views/leave_condonation_processing_views.xml` | ✅ NEW | Processing views |
| `Qacov17/qaco_payroll/data/leave_condonation_processing_sequence.xml` | ✅ NEW | Sequence data |
| `Qacov17/qaco_payroll/security/ir.model.access.csv` | ✅ MODIFIED | New access rights |
| `Qacov17/qaco_payroll/__manifest__.py` | ✅ MODIFIED | Updated data list |

## Menu Structure

```
Time Off
├── My Time Off
│   ├── My Time Off
│   ├── My Allocations
│   └── Leave Condonation (Employee creates here) ← EXISTING
├── Manager
│   └── Leave Condonation (Manager views here) ← EXISTING
└── [Time Off Menu]
    └── Leave Condonation (Top-level access) ← EXISTING

Payroll
├── Payroll
├── Contracts
├── Adjustments
├── Bonuses
└── Leave Condonation Processing ← NEW
```

## Database Models

### leave.condonation (MODIFIED)
- employee_id
- condonation_month ← NEW
- reason ← NEW
- condonation_date (renamed from "Date of Condonation" to "Application Date")
- total_leave_deduction ← NEW
- line_ids (changed structure)
- approval_ids (simplified to single approver)
- state: draft/submitted/approved/rejected/reverted

### leave.condonation.line (MODIFIED)
**OLD:** condonation_date, reason
**NEW:** payroll_line_id, employee_id, department_id, designation_id, gross_salary, allowance_amount, attendance_days, leave_deduction_amount, net_salary, payroll_month, payroll_date_from, payroll_date_to

### qaco.leave.condonation.processing (NEW)
- sequence (LCP00001, LCP00002, ...)
- processing_month
- processing_date
- state: draft/confirmed/processed/cancelled
- line_ids
- total_refund_amount
- total_employees

### qaco.leave.condonation.processing.line (NEW)
- employee_id
- refund_amount
- condonation_count
- condonation_references
- condonation_ids (M2M)
- bank_account_id
- is_paid, paid_date

## Email Template

**Recipient:** Muhammad Bin Qasim
**Subject:** Leave Condonation Approval Request - {Employee Name} ({Month})

**Content:**
- Action buttons (Approve, Reject, Revert, View)
- Employee details
- Reason (in highlighted box)
- **Payroll Deduction Table** with columns:
  - Employee
  - Department
  - Designation
  - Payroll Month
  - Attendance Days
  - Basic Salary
  - Allowance
  - Leave Deduction (red)
  - Net Salary
- Total row

## Key Business Rules

1. **Employee can only request condonation for themselves**
2. **Must have leave deduction in selected month** (from payroll)
3. **Reason is mandatory** before submission
4. **Only Muhammad Bin Qasim can approve** (or administrators)
5. **Lines are readonly** (fetched from payroll)
6. **Processing groups by employee** (multiple condonations combined)
7. **Must confirm before processing**
8. **Can mark individual lines as paid**

## API Methods

### leave.condonation
- `action_load_deductions()` - Fetch payroll data
- `action_submit()` - Submit for approval
- `action_approve()` - Approve request (MBQ only)
- `action_reject()` - Reject request
- `action_revert()` - Revert to draft
- `_load_payroll_deductions()` - Internal: load payroll lines
- `_send_submit_email()` - Internal: send approval email
- `_ensure_mbq_approver()` - Internal: set MBQ as approver

### qaco.leave.condonation.processing
- `action_load_approved_condonations()` - Load approved condonations
- `action_confirm()` - Confirm processing
- `action_process()` - Mark as processed
- `action_cancel()` - Cancel processing
- `action_reset_to_draft()` - Reset to draft

## Search Filters

### Leave Condonation
- My Records
- Draft, Submitted, Approved, Rejected
- Group by: Application Date, Month, Employee, Status

### Processing
- Draft, Confirmed, Processed, Cancelled
- Group by: Processing Month, Status

## Sequences

| Model | Prefix | Example |
|-------|--------|---------|
| leave.condonation | (existing) | LC/2024/001 |
| qaco.leave.condonation.processing | LCP | LCP00001 |

## Dependencies

| Module | Reason |
|--------|--------|
| qaco_employees | Leave condonation form |
| qaco_payroll | Payroll data, processing |
| mail | Email notifications |
| hr | Employee data |

## Important Notes

⚠️ **Muhammad Bin Qasim user must exist** with login='mbqasim' or name containing 'Muhammad Bin Qasim'

⚠️ **Payroll must be processed first** with leave deductions before condonation can be requested

⚠️ **Email must be configured** for notifications to work

⚠️ **Transfer button** mentioned in requirements but not implemented in this version

## Testing Steps

1. Create payroll with leave deduction for test employee
2. Login as test employee
3. Create leave condonation, select month with deduction
4. Load deductions, write reason, submit
5. Check email sent to MBQ
6. Login as MBQ or admin
7. Approve the condonation
8. Check employee receives notification
9. Go to Payroll → Leave Condonation Processing
10. Create processing record, select month
11. Load approved condonations
12. Confirm and process
13. Mark lines as paid

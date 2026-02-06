# Peepl Weekly Report Module

## Overview
Comprehensive weekly reporting system for Odoo 19 with advanced project management, team oversight, and dynamic field customization capabilities.

---

## Table of Contents
1. [Features](#features)
2. [User Roles & Permissions](#user-roles--permissions)
3. [Core Modules](#core-modules)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage Guide](#usage-guide)
7. [Technical Architecture](#technical-architecture)

---

## Features

### 1. Weekly Report Management
- Create and track weekly reports with detailed task information
- Sequential numbering system (global database + department-based display)
- Status tracking: Not Started, In Progress, Completed, Delayed, Plan, Overdue
- Progress percentage tracking (0-100%)
- Notes and detailed descriptions (HTML editor)
- Date range tracking (start date, end date, deadline)
- Automatic overdue status detection via cron job

### 2. Dynamic Field System
- **Template-based custom fields** - Create fields without coding
- **Supported field types:**
  - Text (single line)
  - Multiline Text (textarea)
  - Integer
  - Decimal
  - Checkbox (boolean)
  - Date
  - DateTime
  - Dropdown (selection)
  - Many2one (relational)
- **Department-based field visibility** - Fields only appear for assigned departments
- **Auto-refresh** - Browser automatically reloads after field template changes
- **Dynamic view injection** - Fields automatically appear in forms and lists

### 3. PIC Overview & Statistics
- Real-time statistics per user (Person In Charge)
- Metrics tracked:
  - Total tasks
  - Completed tasks
  - In progress tasks
  - Not started tasks
  - Delayed tasks
  - Planned tasks
  - Overdue tasks
  - Average progress percentage
- Department and position information
- One-click statistics update

### 4. Interactive Dashboard
- Real-time analytics and visualizations
- Department-based filtering
- Task status distribution
- Progress tracking charts
- Quick access to reports
- Mobile-responsive design

### 5. Department-Based Access Control
- **BOD (Board of Directors):** Full access to all departments
- **Manager:** Access only to their department's data
- **Staff:** Access only to their own data
- Automatic filtering based on `hr.employee` department assignment
- Smart menu hiding (BOD sees department view, others see standard view)
- Context-aware PIC field filtering for managers

### 6. User Assignment System
- Link users to departments and positions
- Auto-populate department from HR employee records
- Position-based role assignment (Staff, Manager, BOD)
- Active/inactive status tracking
- Assignment history
- Batch synchronization of user groups
- Automatic group assignment based on position

### 7. Advanced UI Features
- **Column Resizing:** Interactive column width adjustment in list views
- **Auto-refresh:** Browser automatically reloads after field template changes
- **Smart Filtering:** Context-aware field visibility and user selection
- **Progress Bars:** Visual progress indicators in list views
- **Avatar Integration:** User avatars in employee fields
- **Responsive Design:** Mobile-friendly interface

### 8. Department Overview System
- **Kanban Department View:** Visual department cards for BOD
- **Department Statistics:** Real-time report counts per department
- **Department Configuration:** Integrated field template and user management
- **Department Filtering:** Context-aware data segregation
- **Manager Integration:** HR department manager display

### 9. Configuration & Settings
- **System Settings:** Email configuration and auto-send options
- **User Role Display:** Current user access level indicator
- **Default Field Reference:** Built-in field documentation
- **Demo Data:** Sample field templates for testing
- **Cron Job Management:** Automated overdue status updates

---

## User Roles & Permissions

### BOD (Board of Directors)
**Access Level:** Full System Access
- View all weekly reports across all departments
- View all PIC overviews
- View all field templates
- Manage user assignments for all departments
- Create/edit/delete all records
- Access all dashboard data

### Manager
**Access Level:** Department-Specific Access
- View weekly reports from their department only
- View PIC overview for users in their department
- View field templates assigned to their department
- Manage user assignments within their department
- Create/edit weekly reports for department users
- Access dashboard filtered by department

### Staff
**Access Level:** Personal Access Only
- View and manage only their own weekly reports
- View only their own PIC overview
- View field templates assigned to their department
- Cannot manage user assignments
- Create/edit their own weekly reports
- Access personal dashboard data

---

## Core Modules

### 1. Weekly Report (`peepl.weekly.report`)
**Purpose:** Main reporting entity

**Key Fields:**
- `name` - Global sequential number (e.g., WR001, WR002)
- `display_number` - Department-based sequential number (e.g., 1, 2, 3)
- `pic_id` - Person in charge (user)
- `project_task` - Project/task name
- `status` - Task status (selection)
- `progress` - Completion percentage (0-100)
- `deadline` - Task deadline
- `notes` - Additional information (HTML)
- `department_id` - Department assignment
- `allowed_pic_ids` - Computed field for PIC filtering
- Dynamic fields from templates (e.g., `x_field1_value`, `x_field2_value`)

**Special Features:**
- Dual numbering system (global + department-based)
- Inherits `peepl.field.template.mixin` for dynamic fields
- Auto-updates PIC overview on changes

### 2. Field Template (`peepl.field.template`)
**Purpose:** Define custom fields without coding

**Key Fields:**
- `name` - Field label
- `field_type` - Type of field (char, text, integer, etc.)
- `department_id` - Department assignment
- `sequence` - Display order
- `selection_values` - Options for dropdown (one per line)
- `relation_model` - Model name for Many2one fields
- `active` - Enable/disable field

**How It Works:**
1. Admin creates field template
2. System automatically creates `ir.model.fields` record
3. Database column created (e.g., `x_field5_value`)
4. Field injected into views dynamically
5. Browser auto-reloads to show new field

**Technical Implementation:**
- Uses `_sync_template_column()` to create database fields
- Uses `_patch_view()` to inject fields into XML views
- Naming pattern: `x_field{id}_value`
- Automatic indexing for performance

### 3. PIC Overview (`peepl.pic.overview`)
**Purpose:** User statistics and performance tracking

**Key Fields:**
- `user_id` - User reference
- `department_id` - User's department
- `position` - User's position
- `total_tasks` - Count of all tasks
- `completed`, `in_progress`, `not_started`, `delayed`, `plan`, `overdue` - Status counts
- `avg_progress` - Average completion percentage

**Update Mechanism:**
- Manual: Click "Update" button
- Automatic: Triggered on weekly report changes
- Batch: `update_all_stats()` recalculates all users

### 4. User Assignment (`peepl.user.assignment`)
**Purpose:** Link users to departments and positions

**Key Fields:**
- `user_id` - User reference
- `position_id` - Employment type (hr.contract.type)
- `department_id` - Department assignment
- `assigned_by` - Who created the assignment
- `active` - Status flag

**Auto-Population:**
- Reads department from `hr.employee` if available
- Falls back to existing assignments
- BOD positions automatically clear department

**Validation Rules:**
- Department required for non-BOD positions
- Manager can only assign Staff to their department
- BOD can assign anyone to any department

### 5. Dashboard (`peepl.dashboard`)
**Purpose:** Analytics and visualizations

**Features:**
- Real-time data aggregation
- Department-based filtering
- Status distribution charts
- Progress tracking
- Quick statistics
- Interactive widgets

### 6. BOD Weekly Report (`peepl.weekly.report.bod`)
**Purpose:** BOD-specific view with department filtering

**Features:**
- Inherits from main weekly report
- Department context filtering
- Dynamic field visibility based on department
- Same table structure (no separate storage)

### 7. Department View (`peepl.weekly.report.department`)
**Purpose:** Department-centric reporting interface

**Key Fields:**
- `department_id` - Department reference
- `manager_id` - Department manager
- `total_reports` - Report count
- `status` - Department status (draft/done)
- `field_template_ids` - Department field templates
- `user_assignment_ids` - Department user assignments

**Features:**
- SQL view for performance
- Kanban interface for BOD
- Integrated configuration management
- One-click report access

### 8. Default Field Reference (`peepl.default.field`)
**Purpose:** Documentation of built-in fields

**Features:**
- Read-only field reference
- Field type documentation
- Description explanations
- Integration with department configuration

### 9. HR Department Extension (`hr.department`)
**Purpose:** Integration with HR module

**Added Fields:**
- `weekly_report_ids` - Related weekly reports
- `weekly_report_count` - Computed report count

### 10. User Extension (`res.users`)
**Purpose:** Enhanced user selection for managers

**Features:**
- Context-aware name search
- Department-based filtering
- Manager-specific user lists
- Integration with user assignments

### 11. Settings Extension (`res.config.settings`)
**Purpose:** System configuration

**Added Fields:**
- `report_email` - Email configuration
- `auto_send` - Auto-send toggle
- `current_user_role` - Role display

---

## Installation

### Prerequisites
- Odoo 19.0+
- Python 3.10+
- PostgreSQL 12+

### Dependencies
- `base` - Odoo base module
- `web` - Web interface
- `hr` - Human Resources (for employee/department data)

### Installation Steps

1. **Copy module to addons directory:**
```bash
cp -r peepl_weekly_report /path/to/odoo/addons/
```

2. **Update apps list:**
```bash
odoo-bin -u all -d your_database
```

3. **Install module:**
- Go to Apps menu
- Remove "Apps" filter
- Search "Peepl Weekly Report"
- Click Install

4. **Configure user groups:**
- Go to Settings → Users & Companies → Users
- Assign users to groups: Staff, Manager, or BOD

---

## Configuration

### 1. User Assignment Setup

**For BOD:**
1. Navigate to: Weekly Report → Configuration → User Assignments
2. Click Create
3. Select user
4. Select position (must contain "BOD" in name)
5. Department will be auto-cleared for BOD
6. Save

**For Manager/Staff:**
1. Ensure user has `hr.employee` record with department
2. Navigate to: Weekly Report → Configuration → User Assignments
3. Click Create
4. Select user
5. Select position (Manager or Staff)
6. Department auto-populates from HR employee
7. Save

### 2. Field Template Configuration

**Create Custom Field:**
1. Navigate to: Weekly Report → Configuration → Field Templates
2. Click Create
3. Fill in:
   - **Name:** Field label (e.g., "Priority Level")
   - **Field Type:** Select type (e.g., Dropdown)
   - **Department:** Select department (field only visible to this department)
   - **Sequence:** Display order
   - **Selection Values:** (for Dropdown) One option per line
   - **Related Model:** (for Many2one) Model name (e.g., res.partner)
4. Save
5. Browser auto-reloads
6. Field appears in Weekly Report form/list

**Example - Priority Dropdown:**
```
Name: Priority Level
Field Type: Dropdown
Department: IT Department
Sequence: 10
Selection Values:
Low
Medium
High
Critical
```

**Example - Many2one Field:**
```
Name: Related Contact
Field Type: Many2one
Department: Sales
Sequence: 20
Related Model: res.partner
```

### 3. Dashboard Configuration
- Dashboard automatically shows data based on user role
- No manual configuration needed
- Filters apply automatically based on department

---

## Usage Guide

### Creating a Weekly Report

**As Staff:**
1. Navigate to: Weekly Report → Weekly Reports
2. Click Create
3. Fill in:
   - **PIC:** Auto-filled with your name
   - **Project:** Enter project name
   - **Task:** Describe the task
   - **Status:** Select current status
   - **Progress:** Enter percentage (0-100)
   - **Dates:** Set start, end, deadline
   - **Notes:** Additional details
   - **Custom Fields:** Fill any department-specific fields
4. Save
5. Record number auto-generated (e.g., WR001)

**As Manager:**
- Same as Staff, but can create reports for any user in department
- Can view all department reports in list view

**As BOD:**
- Can create reports for any user
- Can view all reports across all departments

### Viewing PIC Overview

**As Staff:**
1. Navigate to: Weekly Report → PIC Overview
2. See only your own statistics
3. Click "Update" to refresh data

**As Manager:**
1. Navigate to: Weekly Report → PIC Overview
2. See statistics for all users in your department
3. Click "Update" to refresh all statistics

**As BOD:**
1. Navigate to: Weekly Report → PIC Overview
2. See statistics for all users across all departments
3. Click "Update" to refresh all statistics

### Managing Field Templates

**As Manager/BOD:**
1. Navigate to: Weekly Report → Configuration → Field Templates
2. View existing templates (filtered by department for Manager)
3. Create/Edit/Delete templates
4. Changes auto-reload browser
5. New fields immediately available in reports

**Field Template Best Practices:**
- Use clear, descriptive names
- Set appropriate sequence for logical ordering
- Test dropdown values before deploying
- Use Many2one for relational data
- Deactivate instead of delete to preserve data

### Using the Dashboard

1. Navigate to: Weekly Report → Dashboard
2. View real-time statistics:
   - Total reports
   - Status distribution
   - Department breakdown (BOD only)
   - Progress charts
3. Click on widgets to drill down
4. Data auto-filters based on role

---

## Technical Architecture

### Database Schema

**Main Tables:**
- `peepl_weekly_report` - Weekly report records
- `peepl_field_template` - Field template definitions
- `peepl_pic_overview` - User statistics
- `peepl_user_assignment` - User-department-position mapping
- `peepl_dashboard` - Dashboard data

**Dynamic Fields:**
- Created as `ir.model.fields` records
- Column naming: `x_field{template_id}_value`
- Indexed for performance
- Automatically added to model

### Security Architecture

**Record Rules:**
- `rule_weekly_report_staff` - Staff sees own reports
- `rule_weekly_report_manager` - Manager sees department reports
- `rule_weekly_report_bod` - BOD sees all reports
- Similar rules for PIC Overview, User Assignment, Field Templates

**Access Rights (ir.model.access.csv):**
- Staff: Read/Write own data
- Manager: Read/Write/Create department data
- BOD: Full CRUD on all data

**Model-Level Filtering:**
- `peepl.user.assignment.search()` - Filters by `hr.employee` department
- Ensures Manager sees correct users even without assignment record
- Handles special characters in department names (e.g., "Research & Development")

### Dynamic Field System

**Field Creation Flow:**
```
1. User creates field template
2. create() method triggered
3. _sync_template_column() called
4. ir.model.fields record created
5. Database column added (x_field{id}_value)
6. Index created for performance
7. Registry cache cleared
8. Models reinitialized
9. Browser auto-reloads
10. Field appears in views
```

**View Patching:**
```
1. User opens form/list view
2. _get_view() intercepted
3. _patch_view() called
4. Field templates queried (filtered by department)
5. Fields injected into XML arch
6. View returned with dynamic fields
```

**Field Naming Convention:**
- Template ID: 5
- Field name: `x_field5_value`
- Database column: `x_field5_value`
- Display label: From template.name

### Numbering System

**Global Numbering (Database):**
- Stored in `name` field
- Format: WR001, WR002, WR003...
- Sequential across all departments
- Uses `sudo()` to bypass record rules
- Never resets

**Display Numbering (UI):**
- Computed field: `display_number`
- Sequential per department
- Starts at 1 for each department
- Shown in list/kanban views
- Recalculates on department change

**Example:**
```
Database (name)  | Department | Display (display_number)
WR001           | IT         | 1
WR002           | Sales      | 1
WR003           | IT         | 2
WR004           | IT         | 3
WR005           | Sales      | 2
```

### Performance Optimizations

1. **Indexed Fields:**
   - All dynamic fields auto-indexed
   - `department_id` indexed on all models
   - `user_id` indexed for quick filtering

2. **Caching:**
   - Registry cache for model definitions
   - View cache for XML structures
   - Cleared only when templates change

3. **Batch Operations:**
   - `update_all_stats()` processes all users at once
   - Bulk field creation in `_sync_template_column()`

4. **Lazy Loading:**
   - Dashboard data loaded on demand
   - PIC overview computed only when accessed

---

## API Reference

### Weekly Report Model

**Methods:**
- `_get_next_number()` - Generate next global number
- `_compute_display_number()` - Calculate department-based number
- `create(vals)` - Override to set number and update PIC overview
- `write(vals)` - Override to update PIC overview on changes

### Field Template Model

**Methods:**
- `_column_name()` - Returns field name (e.g., x_field5_value)
- `_sync_template_column(model)` - Create/update field on model
- `_sync_all_template_columns()` - Sync field on all mixin models
- `_patch_view(arch, view, view_type)` - Inject fields into view
- `create(vals)` - Override to sync fields and reload
- `write(vals)` - Override to sync fields on changes
- `unlink()` - Override to remove fields and reload

### PIC Overview Model

**Methods:**
- `update_all_stats()` - Recalculate statistics for all users
- `update_overview()` - Button action to refresh and reload
- `search()` - Override to filter by department (Manager/Staff)

### User Assignment Model

**Methods:**
- `_onchange_user_id()` - Auto-populate department from HR
- `_onchange_position_id()` - Clear department for BOD
- `_check_assignment_rules()` - Validate assignment constraints
- `search()` - Override to filter by `hr.employee` department
- `sync_all_assignments()` - Batch sync user groups

---

## Troubleshooting

### Issue: Field template not appearing in view
**Solution:**
1. Check if template is active
2. Verify department assignment matches user's department
3. Clear browser cache and reload
4. Check if field was created: Settings → Technical → Database Structure → Fields

### Issue: Manager cannot see department users
**Solution:**
1. Verify Manager has `hr.employee` record with department
2. Check if users have correct department in `hr.employee`
3. Verify user assignment records have correct department_id
4. Restart Odoo and upgrade module

### Issue: Display number not sequential
**Solution:**
1. Display number is computed per department
2. Check if records have correct department_id
3. Number recalculates automatically on save

### Issue: PIC Overview not updating
**Solution:**
1. Click "Update" button manually
2. Check if weekly reports exist for user
3. Verify user has active assignment record
4. Check if department_id is set correctly

### Issue: Special characters in department name (e.g., &)
**Solution:**
- System uses department ID, not name
- Should work automatically
- If issues persist, check `hr.employee` department assignment

---

## Workflows & Examples

### Workflow 1: Creating Weekly Report (Staff)
```
1. Staff logs in → Sees only own reports
2. Click "Create" → Form opens
3. PIC auto-filled with staff name (readonly)
4. Enter Project/Task name
5. Set Deadline date
6. Select Status (default: Not Started)
7. Set Progress (0-100%)
8. Fill custom fields (if any for department)
9. Add Notes (HTML editor)
10. Click Save → Number auto-generated
11. PIC Overview auto-updates
```

### Workflow 2: Manager Reviewing Department Reports
```
1. Manager logs in → Sees department reports only
2. Navigate to Weekly Reports list
3. Filter by Status/PIC/Date
4. View display_number (sequential per dept)
5. Click report to view details
6. Edit if needed (only dept reports)
7. Check PIC Overview for team stats
8. Update statistics if needed
```

### Workflow 3: BOD Creating Custom Field
```
1. BOD logs in → Full access
2. Navigate to Configuration → Field Templates
3. Click Create
4. Enter Name: "Project Priority"
5. Select Type: Dropdown
6. Select Department: IT
7. Set Sequence: 10
8. Enter Selection Values:
   Low
   Medium
   High
   Critical
9. Click Save
10. Browser auto-reloads
11. Field appears in IT dept reports
12. Other departments don't see this field
```

### Workflow 4: Auto Overdue Status Update
```
1. Cron job runs daily (configured in data/peepl_cron_data.xml)
2. System checks all reports with deadline < today
3. Reports with status != 'completed' and != 'overdue'
4. Auto-update status to 'overdue'
5. PIC Overview statistics updated
6. Users see updated status in list view
```

### Workflow 5: BOD Department Management
```
1. BOD logs in → Sees Department Kanban view
2. Each department card shows:
   - Department name
   - Manager with avatar
   - Total report count
3. Click department card → Opens department reports
4. Click settings → Department configuration
5. Configure field templates per department
6. Manage user assignments per department
7. View department-specific statistics
```

### Workflow 6: Column Resizing in List Views
```
1. User opens any list view
2. Hover over column borders
3. Drag to resize columns
4. Width persists during session
5. Minimum width enforced (60px)
6. All rows adjust automatically
```

### Workflow 5: Department-Based Filtering
```
Staff (IT Department):
- Sees: Own reports only
- Display Number: 1, 2, 3... (sequential in IT)
- Custom Fields: IT department fields only

Manager (Sales Department):
- Sees: All Sales dept reports
- Display Number: 1, 2, 3... (sequential in Sales)
- Custom Fields: Sales department fields only
- Can create reports for Sales team members

BOD:
- Sees: All reports (all departments)
- Display Number: Actual global number (WR001, WR002...)
- Custom Fields: All fields from all departments
- Can create reports for anyone
```

---

## Advanced Features

### 1. Automatic Status Management
**Overdue Detection:**
- System automatically sets status to 'overdue' when deadline passes
- Cannot change from 'overdue' to other status except 'completed'
- Cron job runs daily to update overdue reports (ir.cron)
- Manual status change prevented via onchange validation

**Cron Job Configuration:**
- Model: `peepl.weekly.report`
- Method: `update_overdue_status()`
- Frequency: Daily
- Auto-active on module install

**Status Workflow:**
```
Not Started → In Progress → Completed
     ↓              ↓
   Plan         Delayed
     ↓              ↓
  Overdue ← (deadline passed)
     ↓
  Completed (only allowed transition)
```

### 2. Progress Tracking
**Validation:**
- Progress must be between 0-100%
- Constraint check on save
- Visual progress bar in list view
- Average progress calculated in PIC Overview

**Progress Indicators:**
- 0-25%: Red (Critical)
- 26-50%: Orange (Warning)
- 51-75%: Yellow (In Progress)
- 76-100%: Green (Near Complete)

### 3. Number Gap Filling
**Smart Numbering:**
- System detects gaps in sequence
- Fills missing numbers first
- Example: If WR001, WR003 exist, next is WR002
- Prevents number waste from deleted records
- Uses `sudo()` to see all numbers globally

**Implementation:**
```python
def _get_next_number(self):
    existing = self.sudo().search([]).mapped('name')
    for i in range(1, max(existing) + 1):
        if i not in existing:
            return i  # Fill gap
    return max(existing) + 1  # No gap, use next
```

### 4. Dynamic Field Injection
**View Patching Process:**
```xml
<!-- Original View -->
<field name="notes"/>

<!-- After Patching (IT Dept) -->
<field name="notes"/>
<field name="x_field5_value" string="Priority"/>
<field name="x_field8_value" string="Complexity"/>

<!-- After Patching (Sales Dept) -->
<field name="notes"/>
<field name="x_field12_value" string="Lead Source"/>
<field name="x_field15_value" string="Deal Size"/>
```

**BOD Department Context Filtering:**
- BOD can see all fields from all departments
- When clicking specific department, only that department's fields show
- Uses `default_department_id` context
- Dynamic `column_invisible` attribute injection
- Preserves field data while hiding irrelevant fields

**Injection Points:**
- Form view: After 'notes' field
- List view: After 'notes' column
- Kanban view: Not injected (performance)

### 5. Department Isolation
**Data Segregation:**
- Record rules filter at database level
- Model search() override for hr.employee integration
- View domain filters for UI
- Computed fields for allowed users/departments

**Menu Visibility Control:**
- JavaScript-based menu hiding for non-BOD users
- BOD sees "Department Reports" menu
- Staff/Manager see standard "Weekly Reports" menu
- Dynamic style injection via MutationObserver
- Instant hiding without page reload

### 6. Enhanced User Experience
**Auto-Refresh System:**
- Field template changes trigger browser reload
- Form save/delete operations monitored
- 1-second delay for server synchronization
- Prevents stale view issues

**Column Resizing:**
- Interactive column width adjustment
- Real-time visual feedback
- Minimum width constraints
- Cross-row synchronization
- Mouse event handling

**Security Layers:**
```
Layer 1: Access Rights (ir.model.access.csv)
  → Can user access model?

Layer 2: Record Rules (peepl_record_rules.xml)
  → Which records can user see?

Layer 3: Model Override (search method)
  → Additional filtering by hr.employee

Layer 4: View Domain (allowed_user_ids)
  → UI-level restrictions
```

---

## Real-World Scenarios

### Scenario 1: Multi-Department Company
**Setup:**
- 3 Departments: IT, Sales, HR
- 1 BOD, 3 Managers (1 per dept), 15 Staff

**Usage:**
- IT Manager creates custom field "Bug Severity"
- Sales Manager creates "Deal Stage" field
- HR Manager creates "Employee Type" field
- Each department sees only their fields
- BOD sees all fields when creating reports
- Staff in IT only see IT reports with IT fields
- BOD uses department kanban view for overview
- Column resizing for better data visibility

### Scenario 2: Project Tracking
**Setup:**
- IT Department tracking software projects
- Custom fields: Priority, Complexity, Technology

**Workflow:**
1. Staff creates report for "Website Redesign"
2. Sets Priority: High, Complexity: Medium
3. Technology: React + Node.js
4. Manager reviews all IT project reports
5. PIC Overview shows team progress
6. BOD views cross-department project status

### Scenario 3: Client Management
**Setup:**
- Sales Department tracking client tasks
- Custom fields: Deal Size, Lead Source, Stage

**Workflow:**
1. Sales staff creates report per client
2. Tracks progress of client onboarding
3. Manager monitors all client tasks
4. Auto-overdue alerts for missed deadlines
5. PIC Overview shows sales team performance
6. BOD compares sales vs other departments

### Scenario 4: Compliance Reporting
**Setup:**
- HR Department tracking compliance tasks
- Custom fields: Regulation Type, Audit Date

**Workflow:**
1. HR staff creates compliance reports
2. Deadline set for audit dates
3. System auto-marks overdue if missed
4. Manager reviews compliance status
5. PIC Overview tracks completion rates
6. BOD ensures company-wide compliance

---

## Integration Guide

### Integrating with Other Modules

**1. Project Module Integration:**
```python
# Add project_id field to weekly report
project_id = fields.Many2one('project.project', string='Project')
task_id = fields.Many2one('project.task', string='Task')

# Auto-populate from project
@api.onchange('project_id')
def _onchange_project(self):
    if self.project_id:
        self.client_id = self.project_id.partner_id
```

**2. Timesheet Integration:**
```python
# Link to timesheet entries
timesheet_ids = fields.One2many('account.analytic.line', 'weekly_report_id')
total_hours = fields.Float(compute='_compute_total_hours')

@api.depends('timesheet_ids')
def _compute_total_hours(self):
    for record in self:
        record.total_hours = sum(record.timesheet_ids.mapped('unit_amount'))
```

**3. Email Notifications:**
```python
# Send email on overdue
def _send_overdue_notification(self):
    template = self.env.ref('peepl_weekly_report.email_template_overdue')
    for record in self.filtered(lambda r: r.status == 'overdue'):
        template.send_mail(record.id, force_send=True)
```

**4. Report Export:**
```python
# Export to Excel
def action_export_excel(self):
    return {
        'type': 'ir.actions.act_url',
        'url': f'/web/export/xlsx?model={self._name}&ids={self.ids}',
        'target': 'new',
    }
```

### API Endpoints (for external integration)

**Create Report via XML-RPC:**
```python
import xmlrpc.client

url = 'http://localhost:8069'
db = 'your_database'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Create weekly report
report_id = models.execute_kw(db, uid, password,
    'peepl.weekly.report', 'create',
    [{
        'pic_id': 2,
        'client_id': 1,
        'project_task': 'API Integration',
        'status': 'in_progress',
        'progress': 50,
        'deadline': '2024-12-31',
    }]
)
```

**Search Reports via JSON-RPC:**
```python
import requests
import json

url = 'http://localhost:8069/jsonrpc'
headers = {'Content-Type': 'application/json'}

data = {
    'jsonrpc': '2.0',
    'method': 'call',
    'params': {
        'service': 'object',
        'method': 'execute',
        'args': [
            'your_database',
            2,  # uid
            'password',
            'peepl.weekly.report',
            'search_read',
            [['status', '=', 'overdue']],
            ['name', 'project_task', 'deadline']
        ]
    },
    'id': 1
}

response = requests.post(url, data=json.dumps(data), headers=headers)
print(response.json())
```

---

## Performance Tuning

### Database Optimization

**1. Index Strategy:**
```sql
-- Automatically created indexes
CREATE INDEX peepl_weekly_report_pic_id_idx ON peepl_weekly_report(pic_id);
CREATE INDEX peepl_weekly_report_department_id_idx ON peepl_weekly_report(department_id);
CREATE INDEX peepl_weekly_report_status_idx ON peepl_weekly_report(status);
CREATE INDEX peepl_weekly_report_deadline_idx ON peepl_weekly_report(deadline);

-- Dynamic field indexes
CREATE INDEX peepl_weekly_report_x_field5_value_idx ON peepl_weekly_report(x_field5_value) WHERE x_field5_value IS NOT NULL;
```

**2. Query Optimization:**
- Use `search_count()` instead of `len(search())`
- Batch operations with `create()` multi-mode
- Use `mapped()` instead of loops
- Leverage `filtered()` for in-memory filtering

**3. Caching Strategy:**
```python
# Cache computed fields
@api.depends('pic_id')
@tools.ormcache('pic_id')
def _compute_department(self):
    # Expensive computation cached
    pass
```

### Frontend Optimization

**1. Lazy Loading:**
- Dashboard widgets load on demand
- PIC Overview computed only when accessed
- Field templates cached in browser

**2. Asset Bundling:**
```python
'assets': {
    'web.assets_backend': [
        # Minified and bundled
        'peepl_weekly_report/static/src/js/**/*.js',
        'peepl_weekly_report/static/src/css/**/*.css',
    ],
}
```

**3. View Optimization:**
- Limit list view to 80 records per page
- Use `column_invisible` for hidden fields
- Avoid heavy computations in tree views

---

## Security Best Practices

### 1. Data Access Control
- Always use record rules for data segregation
- Never rely solely on UI domain filters
- Use `sudo()` sparingly and document why
- Validate user permissions in business logic

### 2. Input Validation
```python
@api.constrains('progress')
def _check_progress(self):
    for record in self:
        if not 0 <= record.progress <= 100:
            raise ValidationError("Invalid progress value")

@api.constrains('deadline')
def _check_deadline(self):
    for record in self:
        if record.deadline and record.deadline < date.today():
            raise ValidationError("Deadline cannot be in the past")
```

### 3. SQL Injection Prevention
- Use ORM methods instead of raw SQL
- If raw SQL needed, use parameterized queries
- Sanitize user inputs in domain filters

### 4. XSS Prevention
- HTML fields auto-sanitized by Odoo
- Use `escape()` for user-generated content
- Validate field template names and values

---

## Development Notes

### Adding New Field Types
1. Add type to `field_type` selection in `peepl_field_template.py`
2. Update `_sync_template_column()` to handle new type
3. Update `_patch_view()` to add appropriate widget
4. Test field creation and display

### Extending Dynamic Fields
- Inherit `peepl.field.template.mixin` in your model
- Fields automatically available
- Override `_patch_view()` for custom view injection

### Custom Widgets
- Add widget in `_patch_view()` method
- Example: `widget="many2many_tags"` for Many2many fields
- Register custom widgets in assets

---

## Version History

**v19.0.1.0.5** (Current)
- Dynamic field template system
- Department-based field visibility
- Auto-refresh on template changes
- Dual numbering system (global + department)
- Enhanced access control using hr.employee
- PIC Overview with real-time statistics
- Interactive dashboard
- User assignment management
- BOD department kanban interface
- Column resizing in list views
- Smart menu hiding system
- Context-aware field filtering
- HTML notes editor
- Request form tracking
- Automated overdue detection
- Department configuration interface
- User role display in settings
- Enhanced UI/UX features

---

## Support & Contact

**Developer:** Peepl  
**Website:** https://peepl.tech  
**License:** LGPL-3  
**Odoo Version:** 19.0+

---

## License

This module is licensed under LGPL-3. See LICENSE file for details.

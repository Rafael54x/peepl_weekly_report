/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { NotesRenderer } from "./render_notes";

class WeeklyReportCustomView extends Component {
    static template = "peepl_weekly_report.WeeklyReportCustomView";
    static props = ["*"];
    static components = { NotesRenderer };
    
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        
        this.state = useState({
            records: [],
            loading: true,
            searchTerm: "",
            sortField: "display_number",
            sortOrder: "asc",
            currentPage: 1,
            recordsPerPage: 20,
            totalRecords: 0,
            selectedRecords: new Set(),
            selectAll: false,
            dynamicFields: [],
            uniqueNames: [],
            visibleColumns: {
                pic_id: true,
                project_task: true,
                deadline: true,
                status: true,
                progress: true,
                notes: true
            }
        });
        
        this.userDepartmentId = null;
        this.isManager = false;
        this.isSupervisor = false;
        this.isStaff = false;
        this.isBOD = false;
        
        onWillStart(async () => {
            // Load saved column visibility from localStorage
            const savedColumns = localStorage.getItem('weekly_report_visible_columns');
            if (savedColumns) {
                this.state.visibleColumns = JSON.parse(savedColumns);
            }
            
            // Load user department and role first
            await this.loadUserDepartment();
            await this.loadUserRole();
            
            // Get department filter from URL params or context
            const urlParams = new URLSearchParams(window.location.search);
            const deptFromUrl = urlParams.get('dept_filter');
            const deptNameFromUrl = urlParams.get('dept_name');
            const nameFilterFromUrl = urlParams.get('name_filter');
            
            // Use context values if available, otherwise use URL params
            const contextDeptId = this.props.action?.context?.dept_filter;
            const contextDeptName = this.props.action?.context?.dept_name;
            
            let finalDeptId = contextDeptId || deptFromUrl;
            let finalDeptName = contextDeptName || deptNameFromUrl;
            
            // Set name filter from URL
            if (nameFilterFromUrl) {
                this.state.searchTerm = nameFilterFromUrl;
            }
            
            // Auto-redirect Manager/Supervisor/Staff to their department if no filter specified
            if (!finalDeptId && this.userDepartmentId && (this.isManager || this.isSupervisor || this.isStaff)) {
                finalDeptId = this.userDepartmentId;
                // Get department name
                try {
                    const dept = await this.orm.searchRead(
                        "hr.department",
                        [["id", "=", this.userDepartmentId]],
                        ["name"],
                        { limit: 1 }
                    );
                    if (dept.length > 0) {
                        finalDeptName = dept[0].name;
                    }
                } catch (error) {
                    console.warn("Could not load department name:", error);
                }
                
                // Redirect to department filtered URL
                if (finalDeptId && finalDeptName) {
                    const newUrl = new URL(window.location);
                    newUrl.searchParams.set('dept_filter', finalDeptId);
                    newUrl.searchParams.set('dept_name', finalDeptName);
                    if (nameFilterFromUrl) {
                        newUrl.searchParams.set('name_filter', nameFilterFromUrl);
                    }
                    window.location.href = newUrl.toString();
                    return; // Stop execution, page will reload
                }
            }
            
            // Update URL and context with detected department
            if (finalDeptId && finalDeptName) {
                const url = new URL(window.location);
                url.searchParams.set('dept_filter', finalDeptId);
                url.searchParams.set('dept_name', finalDeptName);
                if (nameFilterFromUrl) {
                    url.searchParams.set('name_filter', nameFilterFromUrl);
                }
                window.history.replaceState({}, '', url);
                
                // Update context
                if (this.props.action?.context) {
                    this.props.action.context.dept_filter = parseInt(finalDeptId);
                    this.props.action.context.dept_name = finalDeptName;
                }
            }
            
            await this.loadDynamicFields();
            await this.loadRecords();
        });
        
        onMounted(() => {
            this.setupEventListeners();
            this.renderNotesContent();
            // Don't call preserveUrlParams here - it overrides name_filter
            this.applyColumnVisibility();
        });
    }

    injectDynamicColumns() {
        setTimeout(() => {
            // Remove existing dynamic columns first
            document.querySelectorAll('th[data-name^="x_field"], td[name^="x_field"]').forEach(el => el.remove());
            
            const thead = document.querySelector('.o_list_table thead tr');
            const tbody = document.querySelector('.o_list_table tbody');
            
            if (!thead || !tbody) return;
            
            this.state.dynamicFields.forEach(field => {
                const anchorTh = thead.querySelector(`th[data-anchor="${field.anchor}"]`);
                if (!anchorTh) return;
                
                const th = document.createElement('th');
                th.setAttribute('data-tooltip-delay', '1000');
                th.setAttribute('tabindex', '-1');
                th.setAttribute('data-name', field.name);
                th.className = 'align-middle o_column_sortable position-relative cursor-pointer opacity-trigger-hover w-print-auto';
                th.style.width = '150px';
                th.innerHTML = `
                    <div class="d-flex align-items-center">
                        <span class="d-block min-w-0 text-truncate flex-grow-1 flex-shrink-1">${field.label}</span>
                        <i class="o_list_sortable_icon fa fa-sort opacity-0 opacity-100-hover"></i>
                    </div>
                `;
                th.addEventListener('click', () => this.onSort(field.name));
                
                if (field.position === 'before') {
                    anchorTh.parentNode.insertBefore(th, anchorTh);
                } else {
                    anchorTh.parentNode.insertBefore(th, anchorTh.nextSibling);
                }
                
                tbody.querySelectorAll('tr').forEach(tr => {
                    const anchorTd = tr.querySelector(`td[data-anchor="${field.anchor}"]`);
                    if (!anchorTd) return;
                    
                    const td = document.createElement('td');
                    td.className = 'o_data_cell cursor-pointer o_field_cell o_list_char';
                    td.setAttribute('data-tooltip-delay', '1000');
                    td.setAttribute('tabindex', '-1');
                    td.setAttribute('name', field.name);
                    
                    const recordId = tr.getAttribute('data-id')?.replace('datapoint_', '');
                    const record = this.state.records.find(r => r.id == recordId);
                    const value = record?.[field.name] || '';
                    td.textContent = value;
                    td.setAttribute('data-tooltip', value);
                    
                    if (field.position === 'before') {
                        anchorTd.parentNode.insertBefore(td, anchorTd);
                    } else {
                        anchorTd.parentNode.insertBefore(td, anchorTd.nextSibling);
                    }
                });
            });
            
            // Apply column visibility after injection
            this.applyColumnVisibility();
        }, 100);
    }
    

    async loadUserRole() {
        try {
            // Check user groups to determine role
            const userGroups = await this.orm.call(
                "res.users",
                "has_group",
                ["peepl_weekly_report.group_peepl_bod"]
            );
            
            if (userGroups) {
                this.isBOD = true;
                return;
            }
            
            const isManager = await this.orm.call(
                "res.users",
                "has_group",
                ["peepl_weekly_report.group_peepl_manager"]
            );
            
            if (isManager) {
                this.isManager = true;
                return;
            }
            
            const isSupervisor = await this.orm.call(
                "res.users",
                "has_group",
                ["peepl_weekly_report.group_peepl_supervisor"]
            );
            
            if (isSupervisor) {
                this.isSupervisor = true;
                return;
            }
            
            const isStaff = await this.orm.call(
                "res.users",
                "has_group",
                ["peepl_weekly_report.group_peepl_staff"]
            );
            
            if (isStaff) {
                this.isStaff = true;
            }
        } catch (error) {
            console.warn("Could not load user role:", error);
        }
    }
    
    async loadUserDepartment() {
        try {
            const currentUser = await this.orm.searchRead(
                "peepl.user.assignment",
                [["user_id", "=", this.env.user.userId], ["active", "=", true]],
                ["department_id"],
                { limit: 1 }
            );
            if (currentUser.length > 0 && currentUser[0].department_id) {
                this.userDepartmentId = currentUser[0].department_id[0];
            }
        } catch (error) {
            console.warn("Could not load user department:", error);
        }
    }
    
    preserveUrlParams() {
        // Get current department from context (newly clicked department)
        const contextDeptId = this.props.action?.context?.dept_filter;
        const contextDeptName = this.props.action?.context?.dept_name;
        
        // Get name filter from URL
        const urlParams = new URLSearchParams(window.location.search);
        const nameFilter = urlParams.get('name_filter');
        
        // Monitor URL changes and preserve current department params
        const observer = new MutationObserver(() => {
            const currentUrl = new URL(window.location);
            const urlDeptId = currentUrl.searchParams.get('dept_filter');
            const urlNameFilter = currentUrl.searchParams.get('name_filter');
            
            // Only update URL if it doesn't match current context
            if (contextDeptId && (!urlDeptId || urlDeptId != contextDeptId)) {
                currentUrl.searchParams.set('dept_filter', contextDeptId);
                currentUrl.searchParams.set('dept_name', contextDeptName || '');
                if (nameFilter) {
                    currentUrl.searchParams.set('name_filter', nameFilter);
                }
                window.history.replaceState({}, '', currentUrl);
            } else if (nameFilter && !urlNameFilter) {
                // Preserve name filter if it's missing
                currentUrl.searchParams.set('name_filter', nameFilter);
                window.history.replaceState({}, '', currentUrl);
            }
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
        
        // Handle popstate events
        window.addEventListener('popstate', () => {
            setTimeout(() => this.preserveUrlParams(), 100);
        });
    }
    
    get departmentId() {
        // Check URL params first, then context
        const urlParams = new URLSearchParams(window.location.search);
        const deptFromUrl = urlParams.get('dept_filter');
        if (deptFromUrl) {
            return parseInt(deptFromUrl);
        }
        
        const contextDept = this.props.action?.context?.dept_filter;
        if (contextDept) {
            return contextDept;
        }
        
        // For Manager/Staff, return their department ID if available
        if (this.userDepartmentId) {
            return this.userDepartmentId;
        }
        
        return null;
    }
    
    get domain() {
        let domain = [];
        if (this.departmentId) {
            domain.push(["department_id", "=", this.departmentId]);
        }
        
        // Check URL params for filter
        const urlParams = new URLSearchParams(window.location.search);
        const nameFilter = urlParams.get('name_filter') || this.state.searchTerm;
        
        if (nameFilter) {
            domain.push(["pic_id.name", "=", nameFilter]);
        }
        
        console.log("Search domain:", domain, "Name filter:", nameFilter);
        return domain;
    }
    
    async loadDynamicFields() {
        try {
            const deptId = this.departmentId;
            console.log("loadDynamicFields - departmentId:", deptId);
            console.log("loadDynamicFields - userDepartmentId:", this.userDepartmentId);
            
            if (deptId) {
                const templates = await this.orm.searchRead(
                    "peepl.field.template",
                    [["department_id", "=", deptId], ["active", "=", true]],
                    ["name", "field_type", "anchor_field", "position", "sequence"],
                    { order: "sequence" }
                );
                console.log("loadDynamicFields - templates found:", templates);
                
                this.state.dynamicFields = templates.map(t => ({
                    name: `x_field${t.id}_value`,
                    label: t.name,
                    type: t.field_type,
                    anchor: t.anchor_field,
                    position: t.position,
                    sequence: t.sequence
                }));
                console.log("loadDynamicFields - dynamicFields:", this.state.dynamicFields);
            } else {
                console.log("loadDynamicFields - no deptId, setting empty array");
                this.state.dynamicFields = [];
            }
        } catch (error) {
            console.error("Error loading dynamic fields:", error);
            this.state.dynamicFields = [];
        }
    }
    
    async loadRecords() {
        this.state.loading = true;
        try {
            const domain = this.domain;
            const context = {};
            
            if (this.departmentId) {
                context.dept_filter = this.departmentId;
            }
            
            // Load basic fields first
            const basicFields = [
                "display_number", "pic_id", 
                "project_task", "deadline", "status", "progress", "notes", "department_id"
            ];
            
            // Only add dynamic fields that actually exist
            const availableFields = [...basicFields];
            for (const field of this.state.dynamicFields) {
                try {
                    // Test if field exists by doing a small search
                    await this.orm.searchRead(
                        "peepl.weekly.report",
                        [],
                        [field.name],
                        { limit: 1 }
                    );
                    availableFields.push(field.name);
                } catch (error) {
                    console.warn(`Field ${field.name} not available:`, error);
                }
            }
            
            const records = await this.orm.searchRead(
                "peepl.weekly.report",
                domain,
                availableFields,
                { 
                    limit: this.state.recordsPerPage,
                    offset: (this.state.currentPage - 1) * this.state.recordsPerPage,
                    context 
                }
            );
            
            const totalCount = await this.orm.searchCount(
                "peepl.weekly.report",
                domain
            );
            
            records.forEach((record, index) => {
                record.display_number = index + 1;
            });
            
            // Get ALL names from department for dropdown (not just filtered)
            let allNamesDomain = [];
            const urlParams = new URLSearchParams(window.location.search);
            const deptFilter = urlParams.get('dept_filter');
            if (deptFilter) {
                allNamesDomain.push(["department_id", "=", parseInt(deptFilter)]);
            }
            
            const allRecords = await this.orm.searchRead(
                "peepl.weekly.report",
                allNamesDomain,
                ["pic_id"],
                {}
            );
            
            const uniqueNamesSet = new Set();
            allRecords.forEach(record => {
                if (record.pic_id && record.pic_id[1]) {
                    uniqueNamesSet.add(record.pic_id[1]);
                }
            });
            this.state.uniqueNames = Array.from(uniqueNamesSet).sort();
            
            this.state.records = records;
            this.state.totalRecords = totalCount;
            
            setTimeout(() => this.renderNotesContent(), 50);
            setTimeout(() => this.injectDynamicColumns(), 100);
        } catch (error) {
            console.error("Error loading records:", error);
            this.state.records = [];
            this.state.totalRecords = 0;
        } finally {
            this.state.loading = false;
        }
    }
    
    renderNotesContent() {
        setTimeout(() => {
            const notesCells = document.querySelectorAll('td[data-notes] .js-notes-content');
            notesCells.forEach(container => {
                const td = container.closest('td[data-notes]');
                const notes = td.getAttribute('data-notes');
                if (notes) {
                    container.innerHTML = notes;
                }
            });
            
            const progressCells = document.querySelectorAll('td[data-progress] .js-progress-content');
            progressCells.forEach(container => {
                const td = container.closest('td[data-progress]');
                const progress = parseInt(td.getAttribute('data-progress')) || 0;
                
                let colorClass = '#dc3545'; // Red for 0-29%
                if (progress >= 30 && progress <= 89) {
                    colorClass = '#ffc107'; // Yellow for 30-89%
                } else if (progress >= 90) {
                    colorClass = '#198754'; // Green for 90-100%
                }
                
                container.innerHTML = `
                    <div class="o_progressbar w-100 d-flex align-items-center">
                        <div class="o_progress align-middle overflow-hidden" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progress}">
                            <div class="h-100" style="width: ${progress}%; background-color: ${colorClass};"></div>
                        </div>
                        <div class="o_progressbar_value d-flex">
                            <span class="mx-1">${progress}</span>
                            <span>%</span>
                        </div>
                    </div>
                `;
            });
        }, 100);
    }
    
    getDepartmentTitle() {
        // Check URL params first, then context
        const urlParams = new URLSearchParams(window.location.search);
        let deptName = urlParams.get('dept_name') || this.props.action?.context?.dept_name;
        
        // If no dept_name but we have dept_filter, try to get department name
        if (!deptName && this.departmentId) {
            // Find department name from records if available
            const recordWithDept = this.state.records.find(r => r.department_id);
            if (recordWithDept && Array.isArray(recordWithDept.department_id)) {
                deptName = recordWithDept.department_id[1];
            }
        }
        
        if (deptName) {
            return `Weekly Reports - ${deptName}`;
        }
        return 'Weekly Reports';
    }
    
    setupEventListeners() {
        const searchInput = this.el?.querySelector(".o_searchview_input");
        if (searchInput) {
            let timeout;
            searchInput.addEventListener("input", (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.state.searchTerm = e.target.value;
                    this.state.currentPage = 1;
                    this.loadRecords();
                }, 300);
            });
        }
    }
    
    async onSort(field) {
        if (this.state.sortField === field) {
            this.state.sortOrder = this.state.sortOrder === "asc" ? "desc" : "asc";
        } else {
            this.state.sortField = field;
            this.state.sortOrder = "asc";
        }
        
        // Sort records locally
        this.state.records.sort((a, b) => {
            let aVal, bVal;
            
            if (field === 'display_number') {
                // Sort by actual display number
                aVal = parseInt(a.display_number) || 0;
                bVal = parseInt(b.display_number) || 0;
            } else {
                aVal = a[field];
                bVal = b[field];
                
                // Handle many2one fields
                if (Array.isArray(aVal)) aVal = aVal[1] || '';
                if (Array.isArray(bVal)) bVal = bVal[1] || '';
                
                // Handle null/undefined
                aVal = aVal || '';
                bVal = bVal || '';
            }
            
            if (this.state.sortOrder === "asc") {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
        
        // Don't re-number - keep original display_number with each record
    }
    
    async onPageChange(page) {
        this.state.currentPage = page;
        await this.loadRecords();
    }
    
    onNameFilter(name) {
        const url = new URL(window.location);
        if (name) {
            url.searchParams.set('name_filter', name);
            this.state.searchTerm = name;
        } else {
            url.searchParams.delete('name_filter');
            this.state.searchTerm = "";
        }
        window.history.replaceState({}, '', url);
        
        this.state.currentPage = 1;
        this.loadRecords();
    }
    
    clearFilter() {
        const url = new URL(window.location);
        url.searchParams.delete('name_filter');
        window.history.replaceState({}, '', url);
        
        this.state.searchTerm = "";
        this.state.currentPage = 1;
        
        this.loadRecords();
    }
    
    onSelectRecord(recordId) {
        if (this.state.selectedRecords.has(recordId)) {
            this.state.selectedRecords.delete(recordId);
        } else {
            this.state.selectedRecords.add(recordId);
        }
        this.state.selectAll = this.state.selectedRecords.size === this.state.records.length;
    }
    
    onSelectAll() {
        this.state.selectAll = !this.state.selectAll;
        if (this.state.selectAll) {
            this.state.records.forEach(record => this.state.selectedRecords.add(record.id));
        } else {
            this.state.selectedRecords.clear();
        }
    }
    
    async openRecord(recordId) {
        const context = { ...this.props.action?.context };
        if (this.departmentId) {
            context.dept_filter = this.departmentId;
        }
        
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "peepl.weekly.report",
            res_id: recordId,
            views: [[false, "form"]],
            target: "current",
            context
        });
    }
    
    async createRecord() {
        const context = { ...this.props.action?.context };
        if (this.departmentId) {
            context.dept_filter = this.departmentId;
            context.default_department_id = this.departmentId;
        }
        
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "peepl.weekly.report",
            views: [[false, "form"]],
            target: "current",
            context
        });
    }
    
    goBack() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "peepl.weekly.report.department",
            view_mode: "kanban,list",
            views: [[false, "kanban"], [false, "list"]],
            target: "current",
            name: "Weekly Reports by Department"
        });
    }
    
    get totalPages() {
        return Math.ceil(this.state.totalRecords / this.state.recordsPerPage);
    }
    
    get pagerStart() {
        return (this.state.currentPage - 1) * this.state.recordsPerPage + 1;
    }
    
    get pagerEnd() {
        return Math.min(this.state.currentPage * this.state.recordsPerPage, this.state.totalRecords);
    }
    
    formatDate(dateStr) {
        if (!dateStr) return "";
        const date = new Date(dateStr);
        return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }
    
    getStatusBadge(status) {
        const statusMap = {
            'completed': 'success',
            'in_progress': 'info', 
            'not_started': 'secondary',
            'delayed': 'warning',
            'plan': 'primary',
            'overdue': 'danger'
        };
        return statusMap[status] || 'secondary';
    }
    
    getStatusLabel(status) {
        const statusMap = {
            'completed': 'Completed',
            'in_progress': 'In Progress',
            'not_started': 'Not Started', 
            'delayed': 'Delayed',
            'plan': 'Plan',
            'overdue': 'Overdue'
        };
        return statusMap[status] || status;
    }
    
    getSortIcon(field) {
        if (this.state.sortField !== field) return "fa-sort";
        return this.state.sortOrder === "asc" ? "fa-sort-up" : "fa-sort-down";
    }
    
    formatHtmlField(htmlContent) {
        if (!htmlContent) return '';
        // Decode HTML entities and clean up
        const textarea = document.createElement('textarea');
        textarea.innerHTML = htmlContent;
        let decoded = textarea.value;
        
        // Remove data-oe-version and other editor attributes
        decoded = decoded.replace(/data-oe-version="[^"]*"/g, '');
        decoded = decoded.replace(/data-last-history-steps="[^"]*"/g, '');
        
        // Clean up empty divs with only br tags
        decoded = decoded.replace(/<div[^>]*>\s*<br>\s*<\/div>/g, '');
        
        return decoded;
    }
    
    renderNotesField(htmlContent) {
        if (!htmlContent) return '';
        
        // Decode HTML entities properly
        const div = document.createElement('div');
        div.innerHTML = htmlContent;
        const decoded = div.innerHTML;
        
        // Clean up editor attributes
        return decoded.replace(/data-oe-version="[^"]*"/g, '')
                     .replace(/data-last-history-steps="[^"]*"/g, '');
    }
    
    renderProgressBar(progress) {
        const percentage = progress || 0;
        let colorClass = '#dc3545'; // Red for 0-29%
        if (percentage >= 30 && percentage <= 89) {
            colorClass = '#ffc107'; // Yellow for 30-89%
        } else if (percentage >= 90) {
            colorClass = '#198754'; // Green for 90-100%
        }
        
        return `
            <div class="o_progressbar w-100 d-flex align-items-center">
                <div class="o_progress align-middle overflow-hidden" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${percentage}">
                    <div class="h-100" style="width: min(${percentage}%, 100%); background-color: ${colorClass};"></div>
                </div>
                <div class="o_progressbar_value d-flex">
                    <span class="mx-1">${percentage}</span>
                    <span>%</span>
                </div>
            </div>
        `;
    }
    
    toggleColumn(columnName, visible) {
        this.state.visibleColumns[columnName] = visible;
        localStorage.setItem('weekly_report_visible_columns', JSON.stringify(this.state.visibleColumns));
        const columns = document.querySelectorAll(`th[data-name="${columnName}"], td[name="${columnName}"]`);
        columns.forEach(col => {
            col.style.display = visible ? '' : 'none';
        });
    }
    
    applyColumnVisibility() {
        Object.keys(this.state.visibleColumns).forEach(columnName => {
            if (!this.state.visibleColumns[columnName]) {
                const columns = document.querySelectorAll(`th[data-name="${columnName}"], td[name="${columnName}"]`);
                columns.forEach(col => {
                    col.style.display = 'none';
                });
            }
        });
    }
}

registry.category("actions").add("weekly_report_custom_view", WeeklyReportCustomView);
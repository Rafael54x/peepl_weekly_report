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
            recordsPerPage: 80,
            totalRecords: 0,
            selectedRecords: new Set(),
            selectAll: false,
            dynamicFields: []
        });
        
        onWillStart(async () => {
            // Get department filter from URL params or context
            const urlParams = new URLSearchParams(window.location.search);
            const deptFromUrl = urlParams.get('dept_filter');
            const deptNameFromUrl = urlParams.get('dept_name');
            
            // Always preserve URL params
            if (this.props.action?.context?.dept_filter || deptFromUrl) {
                const url = new URL(window.location);
                const deptId = deptFromUrl || this.props.action.context.dept_filter;
                const deptName = deptNameFromUrl || this.props.action.context.dept_name || '';
                
                url.searchParams.set('dept_filter', deptId);
                url.searchParams.set('dept_name', deptName);
                
                // Only replace if URL changed
                if (url.toString() !== window.location.toString()) {
                    window.history.replaceState({}, '', url);
                }
                
                // Update context
                if (this.props.action?.context) {
                    this.props.action.context.dept_filter = parseInt(deptId);
                    this.props.action.context.dept_name = deptName;
                }
            }
            
            await this.loadDynamicFields();
            await this.loadRecords();
        });
        
        onMounted(() => {
            this.setupEventListeners();
            this.renderNotesContent();
            this.preserveUrlParams();
        });
    }
    
    preserveUrlParams() {
        // Monitor URL changes and preserve search params
        const observer = new MutationObserver(() => {
            const currentUrl = new URL(window.location);
            const hasParams = currentUrl.searchParams.has('dept_filter');
            
            if (!hasParams && (this.props.action?.context?.dept_filter || this.departmentId)) {
                const deptId = this.departmentId || this.props.action.context.dept_filter;
                const deptName = this.props.action?.context?.dept_name || '';
                
                currentUrl.searchParams.set('dept_filter', deptId);
                currentUrl.searchParams.set('dept_name', deptName);
                
                window.history.replaceState({}, '', currentUrl);
            }
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
        
        // Also handle popstate events
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
        return this.props.action?.context?.dept_filter || null;
    }
    
    get domain() {
        let domain = [];
        if (this.departmentId) {
            domain.push(["department_id", "=", this.departmentId]);
        }
        if (this.state.searchTerm) {
            domain.push([
                "|", "|", "|",
                ["project_task", "ilike", this.state.searchTerm],
                ["pic_id.name", "ilike", this.state.searchTerm],
                ["client_id.name", "ilike", this.state.searchTerm],
                ["status", "ilike", this.state.searchTerm]
            ]);
        }
        return domain;
    }
    
    async loadDynamicFields() {
        try {
            const deptId = this.departmentId;
            if (deptId) {
                const templates = await this.orm.searchRead(
                    "peepl.field.template",
                    [["department_id", "=", deptId], ["active", "=", true]],
                    ["name", "field_type"],
                    { order: "sequence" }
                );
                
                this.state.dynamicFields = templates.map(t => ({
                    name: `x_field${t.id}_value`,
                    label: t.name,
                    type: t.field_type
                }));
            } else {
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
            const domain = this.domain; // Use the computed domain that includes department filter
            const context = {};
            
            // Set department filter in context for field filtering
            if (this.departmentId) {
                context.dept_filter = this.departmentId;
            }
            
            const fields = [
                "display_number", "pic_id", "client_id", "request_form", "project_task", "deadline", "status", "progress", "notes", "department_id",
                ...this.state.dynamicFields.map(f => f.name)
            ];
            
            const records = await this.orm.searchRead(
                "peepl.weekly.report",
                domain,
                fields,
                { limit: 50, context }
            );
            
            // Add sequential display numbers starting from 1
            records.forEach((record, index) => {
                record.display_number = index + 1;
            });
            
            this.state.records = records;
            this.state.totalRecords = records.length;
        } catch (error) {
            console.error("Error loading records:", error);
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
                container.innerHTML = `
                    <div class="o_progressbar w-100 d-flex align-items-center">
                        <div class="o_progress align-middle overflow-hidden" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progress}">
                            <div class="bg-primary h-100" style="width: ${progress}%"></div>
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
        return `
            <div class="o_progressbar w-100 d-flex align-items-center">
                <div class="o_progress align-middle overflow-hidden" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${percentage}">
                    <div class="bg-primary h-100" style="width: min(${percentage}%, 100%)"></div>
                </div>
                <div class="o_progressbar_value d-flex">
                    <span class="mx-1">${percentage}</span>
                    <span>%</span>
                </div>
            </div>
        `;
    }
}

registry.category("actions").add("weekly_report_custom_view", WeeklyReportCustomView);
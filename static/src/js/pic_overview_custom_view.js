/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class PicOverviewCustomView extends Component {
    static template = "peepl_weekly_report.PicOverviewCustomView";
    static props = ["*"];
    
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        
        this.state = useState({
            records: [],
            loading: true,
            searchTerm: "",
            departmentFilter: "",
            sortField: "user_id",
            sortOrder: "asc",
            currentPage: 1,
            recordsPerPage: 20,
            totalRecords: 0,
            updating: false,
            uniqueNames: [],
            uniqueDepartments: []
        });
        
        onWillStart(async () => {
            await this.loadRecords();
        });
        
        onMounted(() => {
            this.setupEventListeners();
        });
    }
    
    async loadRecords() {
        this.state.loading = true;
        try {
            // Apply filters
            let domain = [];
            const urlParams = new URLSearchParams(window.location.search);
            const nameFilter = urlParams.get('name_filter') || this.state.searchTerm;
            const deptFilter = urlParams.get('dept_filter_pic') || this.state.departmentFilter;
            
            if (nameFilter) {
                domain.push(["user_id.name", "=", nameFilter]);
            }
            if (deptFilter) {
                domain.push(["department_id.name", "=", deptFilter]);
            }
            
            const fields = [
                "user_id", "department_id", "job_position", "total_tasks", 
                "completed", "in_progress", "not_started", "delayed", 
                "plan", "overdue", "avg_progress"
            ];
            
            const records = await this.orm.searchRead(
                "peepl.pic.overview",
                domain,
                fields,
                { 
                    order: `${this.state.sortField} ${this.state.sortOrder}`,
                    limit: this.state.recordsPerPage,
                    offset: (this.state.currentPage - 1) * this.state.recordsPerPage
                }
            );
            
            // Get total count for pagination
            const totalCount = await this.orm.searchCount(
                "peepl.pic.overview",
                domain
            );
            
            // Extract unique names and departments for filter dropdowns
            const uniqueNamesSet = new Set();
            const uniqueDepartmentsSet = new Set();
            records.forEach(record => {
                if (record.user_id && record.user_id[1]) {
                    uniqueNamesSet.add(record.user_id[1]);
                }
                if (record.department_id && record.department_id[1]) {
                    uniqueDepartmentsSet.add(record.department_id[1]);
                }
            });
            this.state.uniqueNames = Array.from(uniqueNamesSet).sort();
            this.state.uniqueDepartments = Array.from(uniqueDepartmentsSet).sort();
            
            this.state.records = records;
            this.state.totalRecords = totalCount;
            
            // Render progress bars after records are loaded
            this.renderProgressBars();
        } catch (error) {
            console.error("Error loading PIC overview records:", error);
        } finally {
            this.state.loading = false;
        }
    }
    
    setupEventListeners() {
        const searchInput = this.el?.querySelector(".o_searchview_input");
        if (searchInput) {
            let timeout;
            searchInput.addEventListener("input", (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.state.searchTerm = e.target.value;
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
        
        await this.loadRecords();
    }
    
    async updateStats() {
        this.state.updating = true;
        try {
            await this.orm.call("peepl.pic.overview", "update_all_stats", []);
            await this.loadRecords();
            this.notification.add("Statistics updated successfully!", { type: "success" });
        } catch (error) {
            console.error("Error updating statistics:", error);
            this.notification.add("Error updating statistics", { type: "danger" });
        } finally {
            this.state.updating = false;
        }
    }
    
    getSortIcon(field) {
        if (this.state.sortField !== field) return "fa-sort";
        return this.state.sortOrder === "asc" ? "fa-sort-up" : "fa-sort-down";
    }
    
    getProgressBarClass(progress) {
        if (progress >= 80) return "bg-success";
        if (progress >= 60) return "bg-info";
        if (progress >= 40) return "bg-warning";
        return "bg-danger";
    }
    
    renderProgressBar(progress) {
        const percentage = Math.round(progress || 0);
        let colorClass = '#dc3545'; // Red for 0-29%
        if (percentage >= 30 && percentage <= 89) {
            colorClass = '#ffc107'; // Yellow for 30-89%
        } else if (percentage >= 90) {
            colorClass = '#198754'; // Green for 90-100%
        }
        
        return `
            <div class="o_progressbar w-100 d-flex align-items-center">
                <div class="o_progress align-middle overflow-hidden" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${percentage}">
                    <div class="h-100" style="width: ${percentage}%; background-color: ${colorClass};"></div>
                </div>
                <div class="o_progressbar_value d-flex">
                    <span class="mx-1">${percentage}</span>
                    <span>%</span>
                </div>
            </div>
        `;
    }
    
    async onPageChange(page) {
        this.state.currentPage = page;
        await this.loadRecords();
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
    
    onNameFilter(name) {
        const url = new URL(window.location);
        if (name) {
            url.searchParams.set('name_filter', name);
        } else {
            url.searchParams.delete('name_filter');
        }
        window.history.replaceState({}, '', url);
        
        this.state.searchTerm = name;
        this.state.currentPage = 1;
        this.loadRecords();
    }
    
    onDepartmentFilter(dept) {
        const url = new URL(window.location);
        if (dept) {
            url.searchParams.set('dept_filter_pic', dept);
        } else {
            url.searchParams.delete('dept_filter_pic');
        }
        window.history.replaceState({}, '', url);
        
        this.state.departmentFilter = dept;
        this.state.currentPage = 1;
        this.loadRecords();
    }
    
    clearFilters() {
        const url = new URL(window.location);
        url.searchParams.delete('name_filter');
        url.searchParams.delete('dept_filter_pic');
        window.history.replaceState({}, '', url);
        
        this.state.searchTerm = "";
        this.state.departmentFilter = "";
        this.state.currentPage = 1;
        
        // Reset dropdowns
        const selects = this.el?.querySelectorAll('select');
        if (selects) {
            selects.forEach(select => select.value = "");
        }
        
        this.loadRecords();
    }
    
    renderProgressBars() {
        setTimeout(() => {
            const progressCells = document.querySelectorAll('td[data-progress] .js-progress-content');
            progressCells.forEach(container => {
                const td = container.closest('td[data-progress]');
                const progress = parseFloat(td.getAttribute('data-progress')) || 0;
                container.innerHTML = this.renderProgressBar(progress);
            });
        }, 100);
    }
    

}

registry.category("actions").add("pic_overview_custom_view", PicOverviewCustomView);
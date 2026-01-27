/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onPatched, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class PeeplDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.chartRefs = {};
        this.chartInstances = {};
        this.state = useState({
            sidebarOpen: true,
            activeView: 'dashboard',
            picData: [],
            filteredPicData: [],
            departments: [],
            chartData: [],
            selectedDept: null,
            searchQuery: '',
            filterDepartment: '',
            filterRole: '',
            filterStatus: '',
            selectedDeptDetail: null,
            deptDetailData: null,
            currentPage: 1,
            itemsPerPage: 10,
            sortField: '',
            sortOrder: 'asc',
            deptSortField: '',
            deptSortOrder: 'asc',
            totalStats: {
                total_tasks: 0,
                completed: 0,
                in_progress: 0,
                not_started: 0,
                delayed: 0,
                plan: 0,
                overdue: 0
            }
        });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadData();
        });

        onMounted(() => {
            if (this.state.activeView === 'dashboard') {
                this.renderCharts();
            }
        });

        onPatched(() => {
            if (this.state.activeView === 'dashboard' && !this.chartsRendered) {
                this.renderCharts();
            }
        });
    }

    async loadData() {
        // Simplified approach - load all data first, then filter in frontend
        await this.loadAllData();
        
        // Check if user has BOD access by trying to load all departments
        try {
            const allDepts = await this.orm.searchRead(
                "hr.department",
                [["active", "=", true]],
                ["name"]
            );
            
            // If we can load all departments, user is BOD - keep all data
            if (allDepts.length > this.state.departments.length) {
                this.state.departments = allDepts;
                this.setupCommonData(this.state.allAssignments);
            }
        } catch (error) {
            // If error, user is Manager/Staff - data already filtered by record rules
        }
    }

    async loadManagerData(departmentId) {
        // Get users from same department
        const assignments = await this.orm.searchRead(
            "peepl.user.assignment",
            [["department_id", "=", departmentId], ["active", "=", true]],
            ["user_id", "department_id"]
        );
        
        const userIds = assignments.map(a => a.user_id[0]);
        
        // Load PIC data for department users only
        this.state.picData = await this.orm.searchRead(
            "peepl.pic.overview",
            [["user_id", "in", userIds]],
            ["user_id", "position", "total_tasks", "completed", "in_progress", "not_started", "delayed", "plan", "overdue"]
        );
        
        // Load department
        this.state.departments = await this.orm.searchRead(
            "hr.department",
            [["id", "=", departmentId]],
            ["name"]
        );
        
        this.setupCommonData(assignments);
    }

    async loadAllData() {
        // Load all PIC data (filtered by record rules)
        this.state.picData = await this.orm.searchRead(
            "peepl.pic.overview",
            [],
            ["user_id", "position", "total_tasks", "completed", "in_progress", "not_started", "delayed", "plan", "overdue"]
        );
        
        // Load all departments (filtered by record rules)
        this.state.departments = await this.orm.searchRead(
            "hr.department",
            [["active", "=", true]],
            ["name"]
        );
        
        // Load all assignments (filtered by record rules)
        const assignments = await this.orm.searchRead(
            "peepl.user.assignment",
            [["active", "=", true]],
            ["user_id", "department_id"]
        );
        
        this.state.allAssignments = assignments;
        this.setupCommonData(assignments);
    }

    setupCommonData(assignments) {
        // Map department to picData
        this.state.picData.forEach(pic => {
            const assignment = assignments.find(a => a.user_id[0] === pic.user_id[0]);
            pic.department_name = assignment && assignment.department_id ? assignment.department_id[1] : '-';
        });

        this.state.filteredPicData = [...this.state.picData];

        // Calculate total stats for BOD/Manager
        this.calculateTotalStats();

        // Calculate department stats
        this.state.departments.forEach(dept => {
            const deptUsers = assignments.filter(a => a.department_id[0] === dept.id);
            const deptPics = this.state.picData.filter(pic => pic.department_name === dept.name);
            
            dept.total_users = deptUsers.length;
            dept.total_tasks = deptPics.reduce((sum, pic) => sum + pic.total_tasks, 0);
        });

        this.loadChartData();
    }

    async loadChartData() {
        const reports = await this.orm.searchRead(
            "peepl.weekly.report",
            [],
            ["pic_id"]
        );

        const chartData = {};
        for (const dept of this.state.departments) {
            const deptPics = this.state.picData.filter(pic => pic.department_name === dept.name);
            chartData[dept.id] = {
                users: [],
                tasks: []
            };
            
            for (const pic of deptPics) {
                const userReports = reports.filter(r => r.pic_id[0] === pic.user_id[0]);
                chartData[dept.id].users.push(pic.user_id[1]);
                chartData[dept.id].tasks.push(userReports.length);
            }
        }
        this.state.chartData = chartData;
    }

    renderCharts() {
        if (!window.Chart || this.chartsRendered) {
            return;
        }
        
        // Destroy all existing charts first
        this.destroyAllCharts();
        
        setTimeout(() => {
            for (const dept of this.state.departments) {
                const canvasId = `chart_${dept.id}`;
                const canvas = document.getElementById(canvasId);
                
                if (!canvas || !this.state.chartData[dept.id]) continue;

                // Clear canvas before creating new chart
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                const data = this.state.chartData[dept.id];
                
                try {
                    this.chartInstances[dept.id] = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.users,
                            datasets: [
                                { 
                                    label: 'Total Tasks', 
                                    data: data.tasks, 
                                    backgroundColor: '#051847', 
                                    borderColor: '#051847', 
                                    borderWidth: 1,
                                    hoverBackgroundColor: '#0a2a6e',
                                    hoverBorderColor: '#0a2a6e'
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: { beginAtZero: true, ticks: { stepSize: 1 } }
                            },
                            plugins: {
                                legend: { display: false },
                                tooltip: { enabled: true }
                            },
                            onClick: (event, elements) => {
                                if (elements.length > 0) {
                                    const index = elements[0].index;
                                    const userName = data.users[index];
                                    this.filterByUserName(userName);
                                }
                            }
                        }
                    });
                } catch (error) {
                    console.error(`Error creating chart for department ${dept.id}:`, error);
                }
            }
            this.chartsRendered = true;
        }, 200);
    }

    destroyAllCharts() {
        Object.keys(this.chartInstances).forEach(deptId => {
            if (this.chartInstances[deptId]) {
                try {
                    this.chartInstances[deptId].destroy();
                } catch (error) {
                    console.error(`Error destroying chart for department ${deptId}:`, error);
                }
                delete this.chartInstances[deptId];
            }
        });
    }

    toggleSidebar() {
        this.state.sidebarOpen = !this.state.sidebarOpen;
    }

    setView(view) {
        // Destroy charts when leaving dashboard view
        if (this.state.activeView === 'dashboard' && view !== 'dashboard') {
            this.destroyAllCharts();
        }
        
        this.state.activeView = view;
        if (view === 'dashboard') {
            this.chartsRendered = false;
        }
    }

    selectDepartment(dept) {
        this.state.selectedDept = dept;
    }

    onSearchChange(ev) {
        this.state.searchQuery = ev.target.value.toLowerCase();
        this.filterData();
    }

    filterData() {
        const query = this.state.searchQuery;
        const dept = this.state.filterDepartment;
        const role = this.state.filterRole;
        const status = this.state.filterStatus;
        
        this.state.filteredPicData = this.state.picData.filter(pic => {
            const matchName = pic.user_id[1].toLowerCase().includes(query);
            const matchDept = !dept || pic.department_name === dept;
            const matchRole = !role || pic.position === role;
            const matchStatus = !status || this.hasStatus(pic, status);
            return matchName && matchDept && matchRole && matchStatus;
        });
        this.state.currentPage = 1;
    }

    changeItemsPerPage(ev) {
        this.state.itemsPerPage = parseInt(ev.target.value);
        this.state.currentPage = 1;
    }

    onDepartmentFilter(ev) {
        this.state.filterDepartment = ev.target.value;
        this.filterData();
    }

    onRoleFilter(ev) {
        this.state.filterRole = ev.target.value;
        this.filterData();
    }

    get uniqueDepartments() {
        return [...new Set(this.state.picData.map(p => p.department_name).filter(d => d !== '-'))];
    }

    get uniqueRoles() {
        return [...new Set(this.state.picData.map(p => p.position).filter(r => r && r !== 'No Position'))];
    }

    get paginatedData() {
        const start = (this.state.currentPage - 1) * this.state.itemsPerPage;
        const end = start + this.state.itemsPerPage;
        return this.state.filteredPicData.slice(start, end);
    }

    get totalPages() {
        return Math.ceil(this.state.filteredPicData.length / this.state.itemsPerPage);
    }

    goToPage(page) {
        if (page >= 1 && page <= this.totalPages) {
            this.state.currentPage = page;
        }
    }

    nextPage() {
        if (this.state.currentPage < this.totalPages) {
            this.state.currentPage++;
        }
    }

    prevPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
        }
    }

    showDeptDetails(dept) {
        this.state.selectedDeptDetail = dept;
        this.loadDeptDetailData(dept);
    }

    async loadDeptDetailData(dept) {
        // Load weekly reports for this department
        const assignments = await this.orm.searchRead(
            "peepl.user.assignment",
            [["department_id", "=", dept.id], ["active", "=", true]],
            ["user_id"]
        );
        
        const userIds = assignments.map(a => a.user_id[0]);
        
        // Always fetch fresh data from database
        const reports = await this.orm.call(
            "peepl.weekly.report",
            "search_read",
            [[["pic_id", "in", userIds]]],
            {
                fields: ["name", "pic_id", "client_id", "project_task", "deadline", "status", "progress", "request_form", "notes"]
            }
        );
        
        // Process notes to extract text content
        reports.forEach(report => {
            if (report.notes) {
                // Create temporary div to parse HTML and extract text
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = report.notes;
                report.notes_text = tempDiv.textContent || tempDiv.innerText || '';
            } else {
                report.notes_text = '';
            }
        });
        
        this.state.deptDetailData = {
            department: dept,
            reports: reports,
            users: assignments
        };
    }

    closeDeptDetails() {
        this.state.selectedDeptDetail = null;
        this.state.deptDetailData = null;
    }

    calculateTotalStats() {
        // Calculate total stats from all visible PIC data
        this.state.totalStats = {
            total_tasks: this.state.picData.reduce((sum, pic) => sum + (pic.total_tasks || 0), 0),
            completed: this.state.picData.reduce((sum, pic) => sum + (pic.completed || 0), 0),
            in_progress: this.state.picData.reduce((sum, pic) => sum + (pic.in_progress || 0), 0),
            not_started: this.state.picData.reduce((sum, pic) => sum + (pic.not_started || 0), 0),
            delayed: this.state.picData.reduce((sum, pic) => sum + (pic.delayed || 0), 0),
            plan: this.state.picData.reduce((sum, pic) => sum + (pic.plan || 0), 0),
            overdue: this.state.picData.reduce((sum, pic) => sum + (pic.overdue || 0), 0)
        };
    }

    filterByStatus(status) {
        this.state.filterStatus = status;
        this.filterData();
    }

    hasStatus(pic, status) {
        return pic[status] > 0;
    }

    resetFilters() {
        this.state.searchQuery = '';
        this.state.filterDepartment = '';
        this.state.filterRole = '';
        this.state.filterStatus = '';
        this.state.filteredPicData = [...this.state.picData];
        this.state.currentPage = 1;
    }

    filterByUserName(userName) {
        this.state.searchQuery = userName.toLowerCase();
        this.filterData();
    }

    get hasActiveFilters() {
        return this.state.searchQuery || 
               this.state.filterDepartment || 
               this.state.filterRole || 
               this.state.filterStatus;
    }

    sortData(field) {
        if (this.state.sortField === field) {
            this.state.sortOrder = this.state.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            this.state.sortField = field;
            this.state.sortOrder = 'asc';
        }
        
        this.state.filteredPicData.sort((a, b) => {
            let aVal = a[field];
            let bVal = b[field];
            
            if (field === 'user_id') {
                aVal = a.user_id[1];
                bVal = b.user_id[1];
            }
            
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }
            
            if (this.state.sortOrder === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
        
        this.state.currentPage = 1;
    }

    sortDeptData(field) {
        if (this.state.deptSortField === field) {
            this.state.deptSortOrder = this.state.deptSortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            this.state.deptSortField = field;
            this.state.deptSortOrder = 'asc';
        }
        
        this.state.deptDetailData.reports.sort((a, b) => {
            let aVal = a[field];
            let bVal = b[field];
            
            if (field === 'pic_id') {
                aVal = a.pic_id[1];
                bVal = b.pic_id[1];
            } else if (field === 'client_id') {
                aVal = a.client_id ? a.client_id[1] : '';
                bVal = b.client_id ? b.client_id[1] : '';
            }
            
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }
            
            if (this.state.deptSortOrder === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
    }
}

PeeplDashboard.template = "peepl_weekly_report.Dashboard";

registry.category("actions").add("peepl_dashboard", PeeplDashboard);

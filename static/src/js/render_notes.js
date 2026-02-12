/** @odoo-module **/

import { Component, onMounted } from "@odoo/owl";

export class NotesRenderer extends Component {
    setup() {
        onMounted(() => {
            this.renderNotesFields();
        });
    }
    
    renderNotesFields() {
        const notesCells = document.querySelectorAll('td[data-notes] .js-notes-content');
        notesCells.forEach(container => {
            const td = container.closest('td[data-notes]');
            const notes = td.getAttribute('data-notes');
            if (notes && notes !== 'false') {
                // Decode HTML entities
                const textarea = document.createElement('textarea');
                textarea.innerHTML = notes;
                const decoded = textarea.value;
                container.innerHTML = decoded;
                
                // Find and render file boxes
                const fileBoxes = container.querySelectorAll('[data-embedded="file"]');
                fileBoxes.forEach(fileBox => {
                    try {
                        const propsAttr = fileBox.getAttribute('data-embedded-props');
                        if (propsAttr) {
                            const props = JSON.parse(propsAttr.replace(/&quot;/g, '"').replace(/&amp;/g, '&'));
                            const fileData = props.fileData;
                            
                            if (fileData) {
                                const downloadUrl = fileData.url || `/web/content/${fileData.id}?access_token=${fileData.access_token}&filename=${encodeURIComponent(fileData.filename)}&download=true`;
                                const previewUrl = downloadUrl.replace('&download=true', '');
                                
                                // Create clickable file link
                                const fileLink = document.createElement('a');
                                fileLink.href = previewUrl;
                                fileLink.className = 'badge bg-primary text-white text-decoration-none';
                                fileLink.innerHTML = `<i class="fa fa-file-${fileData.extension === 'pdf' ? 'pdf' : 'o'}"></i> ${fileData.filename}`;
                                fileLink.style.cssText = 'padding: 5px 10px; display: inline-block; margin: 2px;';
                                
                                fileLink.addEventListener('click', (e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    
                                    // Open in modal
                                    const modal = document.createElement('div');
                                    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:9999;display:flex;align-items:center;justify-content:center;';
                                    modal.innerHTML = `
                                        <div style="width:90%;height:90%;background:white;position:relative;">
                                            <button onclick="this.closest('div[style*=fixed]').remove()" style="position:absolute;top:10px;right:10px;z-index:10000;padding:5px 10px;background:red;color:white;border:none;cursor:pointer;">Close</button>
                                            <iframe src="${previewUrl}" style="width:100%;height:100%;border:none;"></iframe>
                                        </div>
                                    `;
                                    document.body.appendChild(modal);
                                    modal.addEventListener('click', (e) => {
                                        if (e.target === modal) modal.remove();
                                    });
                                });
                                
                                fileBox.innerHTML = '';
                                fileBox.appendChild(fileLink);
                            }
                        }
                    } catch (e) {
                        console.error('Error parsing file data:', e);
                    }
                });
                
                // Make other links clickable
                const links = container.querySelectorAll('a:not([data-file-rendered])');
                links.forEach(link => {
                    link.addEventListener('click', (e) => {
                        e.stopPropagation();
                    });
                });
            }
        });
    }
}
import { app } from "../../scripts/app.js";

export class ArtifactList {
    constructor(container) {
        this.container = container;
        this.init();
    }

    init() {
        // 添加 Tailwind CSS
        if (!document.querySelector('#tailwind-css')) {
            const link = document.createElement('link');
            link.id = 'tailwind-css';
            link.href = 'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css';
            link.rel = 'stylesheet';
            document.head.appendChild(link);
        }

        // 构建界面 HTML
        this.container.innerHTML = `
            <div class="flex flex-col h-full bg-gray-900 text-gray-100 text-xs">
                <!-- 搜索和过滤区域 -->
                <div class="p-2 border-b border-gray-700">
                    <div class="flex space-x-2">
                        <!-- 日期选择 -->
                        <div class="flex-1">
                            <input type="date" class="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
                        </div>
                        <!-- 状态过滤 -->
                        <select class="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500">
                            <option value="">全部</option>
                            <option value="1">已完成</option>
                            <option value="0">处理中</option>
                            <option value="2">失败</option>
                        </select>
                    </div>
                </div>

                <!-- 图片列表区域 -->
                <div class="flex-1 overflow-y-auto" id="artifactList">
                    <div class="grid grid-cols-1 gap-2 p-2">
                        <!-- 图片项将在这里动态生成 -->
                    </div>
                </div>
            </div>
        `;

        this.dateInput = this.container.querySelector('input[type="date"]');
        this.statusSelect = this.container.querySelector('select');
        this.artifactList = this.container.querySelector('#artifactList > div');

        this.bindEvents();
        this.loadArtifacts();
    }

    bindEvents() {
        this.dateInput.addEventListener('change', () => {
            this.loadArtifacts(this.dateInput.value, this.statusSelect.value);
        });

        this.statusSelect.addEventListener('change', () => {
            this.loadArtifacts(this.dateInput.value, this.statusSelect.value);
        });

        // 添加滚动加载
        let isLoading = false;
        let offset = 0;
        const limit = 20;

        this.artifactList.parentElement.addEventListener('scroll', async (e) => {
            const { scrollTop, scrollHeight, clientHeight } = e.target;
            if (scrollHeight - scrollTop - clientHeight < 50 && !isLoading) {
                isLoading = true;
                offset += limit;
                await this.loadMoreArtifacts(offset);
                isLoading = false;
            }
        });
    }

    async loadArtifacts(date = '', status = '') {
        try {
            const response = await fetch('/bt/artifacts/list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    date,
                    status,
                    limit: 20,
                    offset: 0
                })
            });
            
            if (!response.ok) throw new Error('加载失败');
            
            const result = await response.json();
            if (result.code !== 0) {
                throw new Error(result.msg || '加载失败');
            }
            
            this.renderArtifacts(result.data, true);
        } catch (error) {
            console.error('加载历史记录失败:', error);
            app.ui.showToast('加载历史记录失败', 'error');
        }
    }

    async loadMoreArtifacts(offset) {
        try {
            const response = await fetch('/bt/artifacts/list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    date: this.dateInput.value,
                    status: this.statusSelect.value,
                    limit: 20,
                    offset
                })
            });
            
            if (!response.ok) throw new Error('加载失败');
            
            const result = await response.json();
            if (result.code !== 0) {
                throw new Error(result.msg || '加载失败');
            }
            
            if (result.data.length > 0) {
                this.renderArtifacts(result.data, false);
            }
        } catch (error) {
            console.error('加载更多记录失败:', error);
            app.ui.showToast('加载更多记录失败', 'error');
        }
    }

    renderArtifacts(artifacts, clear = true) {
        const html = artifacts.map(artifact => this.createArtifactCard(artifact)).join('');
        if (clear) {
            this.artifactList.innerHTML = html;
        } else {
            this.artifactList.insertAdjacentHTML('beforeend', html);
        }
    }

    createArtifactCard(artifact) {
        const imageUrl = this.getImageUrl(artifact);
        return `
            <div class="relative bg-gray-800 rounded overflow-hidden hover:bg-gray-700 transition-colors" data-id="${artifact.id}">
                <div class="aspect-w-16 aspect-h-9">
                    <img src="${imageUrl}" class="object-cover w-full h-full" alt="生成图片" 
                         onerror="this.onerror=null; this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 1 1%22><rect width=%221%22 height=%221%22 fill=%22%23333%22/></svg>'" />
                </div>
                <div class="p-2">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-1">
                            <span class="px-1.5 py-0.5 text-xs rounded-full ${this.getStatusClass(artifact.result_status)}">
                                ${this.getStatusText(artifact.result_status)}
                            </span>
                            <span class="text-xs text-gray-400">${this.formatDate(artifact.created_at)}</span>
                        </div>
                        <div class="flex space-x-1">
                            <button class="p-1 hover:bg-gray-600 rounded" onclick="app.artifactList.viewDetails('${artifact.id}')">
                                <i class="pi pi-eye text-xs"></i>
                            </button>
                            <button class="p-1 hover:bg-gray-600 rounded" onclick="app.artifactList.downloadImage('${imageUrl}')">
                                <i class="pi pi-download text-xs"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getStatusClass(status) {
        switch(status) {
            case '1': return 'bg-green-600';
            case '0': return 'bg-yellow-600';
            case '2': return 'bg-red-600';
            default: return 'bg-gray-600';
        }
    }

    getStatusText(status) {
        switch(status) {
            case '1': return '已完成';
            case '0': return '处理中';
            case '2': return '失败';
            default: return '未知';
        }
    }

    formatDate(dateStr) {
        return new Date(dateStr).toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    getImageUrl(artifact) {
        const outputs = JSON.parse(artifact.outputs || '{}');
        for (const nodeId in outputs) {
            const output = outputs[nodeId];
            if (output.images && output.images.length > 0) {
                return `/view?filename=${output.images[0].filename}`;
            }
        }
        return '';
    }

    async viewDetails(id) {
        try {
            const response = await fetch(`/bt/artifacts/${id}`);
            if (!response.ok) throw new Error('获取详情失败');
            
            const result = await response.json();
            if (result.code !== 0) {
                throw new Error(result.msg || '获取详情失败');
            }
            
            app.ui.dialog.show(`生成详情 #${id}`, {
                element: this.createDetailsView(result.data),
                class: "artifact-details-dialog"
            });
        } catch (error) {
            console.error('获取详情失败:', error);
            app.ui.showToast('获取详情失败', 'error');
        }
    }

    createDetailsView(artifact) {
        const container = document.createElement('div');
        container.className = 'p-3 bg-gray-900 text-gray-100 text-xs';
        container.innerHTML = `
            <div class="grid grid-cols-1 gap-3">
                <div class="aspect-w-16 aspect-h-9">
                    <img src="${this.getImageUrl(artifact)}" class="object-contain rounded" alt="生成图片" />
                </div>
                <div class="space-y-3">
                    <div>
                        <h3 class="text-sm font-semibold mb-1">提示词</h3>
                        <pre class="bg-gray-800 p-2 rounded overflow-auto max-h-32 text-xs">${JSON.stringify(artifact.prompt, null, 2)}</pre>
                    </div>
                    <div>
                        <h3 class="text-sm font-semibold mb-1">元数据</h3>
                        <pre class="bg-gray-800 p-2 rounded overflow-auto max-h-32 text-xs">${JSON.stringify(artifact.meta, null, 2)}</pre>
                    </div>
                    <div class="text-xs text-gray-400">
                        创建时间: ${this.formatDate(artifact.created_at)}
                    </div>
                </div>
            </div>
        `;
        return container;
    }

    async downloadImage(url) {
        try {
            const response = await fetch(url);
            const blob = await response.blob();
            const blobUrl = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = url.split('/').pop() || 'image.png';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(blobUrl);
        } catch (error) {
            console.error('下载图片失败:', error);
            app.ui.showToast('下载图片失败', 'error');
        }
    }
} 
import { app } from "../../scripts/app.js";
import { ImagePreview } from "./image-preview.js";

export class ArtifactList {
    constructor(container) {
        this.container = container;
        // 确保容器占满高度
        this.container.style.height = '100%';
        this.container.style.display = 'flex';
        this.container.style.flexDirection = 'column';
        this.pageSize = 5;
        this.currentPage = 1;
        this.total = 0;

        // 初始化图片预览组件
        this.imagePreview = new ImagePreview();
        this.init();
    }


    showImagePreview(artifact) {
        const imageUrls = this.getAllImageUrls(artifact).map(item => item.url);
        this.imagePreview.showPreview(imageUrls);
    }

    init() {
        // 创建 iframe
        this.frame = document.createElement('iframe');
        this.frame.style.cssText = `
            width: 100%;
            height: 100%;
            border: none;
            background-color: transparent;
            flex: 1;
            display: block;
        `;
        this.container.appendChild(this.frame);

        // 等待 iframe 加载完成
        this.frame.onload = () => {
            this.initFrame();
        };

        const cssPath = import.meta.resolve('./tailwindcss.4.1.7.css');
        
        // 写入基础 HTML 结构
        this.frame.srcdoc = `
            <!DOCTYPE html>
            <html class="dark h-full">
            <head>
                <link rel="stylesheet" href="${cssPath}">
                <style>
                    :root {
                        color-scheme: dark;
                    }

                    html, body {
                        height: 100%;
                        margin: 0;
                        overflow: hidden;
                    }

                    body {
                        font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
                        display: flex;
                        flex-direction: column;
                    }
                    

                    /* 暗色模式下的滚动条样式 */
                    .dark .custom-scrollbar {
                        scrollbar-width: thin;
                        scrollbar-color: var(--color-dark-700) var(--color-dark-900);
                    }

                    .dark .custom-scrollbar::-webkit-scrollbar {
                        width: 6px;
                        height: 6px;
                    }

                    .dark .custom-scrollbar::-webkit-scrollbar-track {
                        background: var(--color-dark-900);
                    }

                    .dark .custom-scrollbar::-webkit-scrollbar-thumb {
                        background-color: var(--color-dark-700);
                        border-radius: 3px;
                    }

                    .dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                        background-color: var(--color-dark-600);
                    }


                    .dark input[type="date"]:hover::after {
                        opacity: 1;
                    }

                    .dark select {
                        background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%23525252' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
                    }

                    /* 图标样式 */
                    .icon {
                        width: 14px;
                        height: 14px;
                        display: inline-block;
                        vertical-align: middle;
                    }

                    /* 分页按钮样式 */
                    .pagination-btn {
                        min-width: 32px;
                        height: 32px;
                        padding: 0 6px;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 6px;
                        font-size: 14px;
                        transition: all 0.2s;
                    }

                    .pagination-btn:disabled {
                        opacity: 0.5;
                        cursor: not-allowed;
                    }

                    .artifact-item .bt-prev-image-btn{
                        top: calc(50% - var(--spacing) * 4);
                        left: calc(var(--spacing) * 2);
                    }
                    .artifact-item .bt-next-image-btn {
                        top: calc(50% - var(--spacing) * 4);
                        right: calc(var(--spacing) * 2);
                    }
                </style>
            </head>
            <body class="dark bg-black text-gray-100 h-full">
                <div class="flex flex-col h-full min-h-0 bg-black p-2">
                    <!-- 搜索和过滤区域 -->
                    <div class="border-gray-800 pb-1.5 flex-none shadow-[0_4px_6px_-1px_rgba(0,0,0,0.3)]">
                        <div class="flex items-center gap-1.5">
                            <input type="date" 
                                class="h-7 rounded bg-gray-900 px-1.5 text-xs text-gray-100 border-0 focus:ring-1 focus:ring-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:ring-gray-700" />
                            <span class="text-gray-600 dark:text-gray-500 text-xs">|</span>
                            <select class="h-7 rounded bg-gray-900 px-1.5 text-xs text-gray-100 border-0 focus:ring-1 focus:ring-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:ring-gray-700 appearance-none cursor-pointer">
                                <option value="">全部状态</option>
                                <option value="1">已完成</option>
                                <option value="0">处理中</option>
                                <option value="2">失败</option>
                            </select>
                            <span class="text-gray-600 dark:text-gray-500 text-xs">|</span>
                            <button class="search-btn h-7 w-7 rounded bg-gray-900 hover:bg-gray-800 active:bg-gray-700 cursor-pointer flex items-center justify-center text-gray-400 hover:text-gray-300">
                                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="11" cy="11" r="7"></circle>
                                    <path d="M21 21l-4.35-4.35"></path>
                                </svg>
                            </button>
                        </div>
                    </div>

                    <!-- 图片列表区域 -->
                    <div class="flex-1 min-h-0 overflow-y-auto pt-1.5 mt-1 custom-scrollbar" id="artifactList">
                        <div class="grid grid-cols-1 gap-2">
                            <!-- 图片项将在这里动态生成 -->
                        </div>
                    </div>

                    <!-- 分页区域 -->
                    <div class="flex-none mt-2 py-2 flex items-center justify-between border-t border-gray-800">
                        <div class="text-sm text-gray-500">
                            共 <span id="totalCount">0</span> 条 / <span id="totalPages">0</span> 页
                        </div>
                        <div class="flex items-center gap-1">
                            <button id="prevPage" class="pagination-btn bg-gray-900 text-gray-400 hover:bg-gray-800 hover:text-gray-300 active:bg-gray-700 disabled:hover:bg-gray-900 disabled:hover:text-gray-400" disabled>
                                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
                                </svg>
                            </button>
                            <span class="text-sm text-gray-400">第 <span id="currentPage">1</span> 页</span>
                            <button id="nextPage" class="pagination-btn bg-gray-900 text-gray-400 hover:bg-gray-800 hover:text-gray-300 active:bg-gray-700 disabled:hover:bg-gray-900 disabled:hover:text-gray-400" disabled>
                                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </body>
            </html>
        `;
    }

    initFrame() {
        const doc = this.frame.contentDocument;
        this.dateInput = doc.querySelector('input[type="date"]');
        this.statusSelect = doc.querySelector('select');
        this.artifactList = doc.querySelector('#artifactList > div');
        this.totalCountEl = doc.querySelector('#totalCount');
        this.totalPagesEl = doc.querySelector('#totalPages');
        this.currentPageEl = doc.querySelector('#currentPage');
        this.prevPageBtn = doc.querySelector('#prevPage');
        this.nextPageBtn = doc.querySelector('#nextPage');

        this.bindEvents();
        this.loadArtifacts();
    }

    bindEvents() {
        const doc = this.frame.contentDocument;
        
        // 查询按钮点击事件
        const searchBtn = doc.querySelector('.search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.loadArtifacts(this.dateInput.value, this.statusSelect.value);
            });
        }

        // 分页按钮事件
        if (this.prevPageBtn) {
            this.prevPageBtn.addEventListener('click', () => {
                if (this.currentPage > 1) {
                    this.currentPage--;
                    this.loadArtifacts(this.dateInput.value, this.statusSelect.value);
                }
            });
        }

        if (this.nextPageBtn) {
            this.nextPageBtn.addEventListener('click', () => {
                const totalPages = Math.ceil(this.total / this.pageSize);
                if (this.currentPage < totalPages) {
                    this.currentPage++;
                    this.loadArtifacts(this.dateInput.value, this.statusSelect.value);
                }
            });
        }

        // 修改日期和状态选择的事件处理
        if (this.dateInput) {
            this.dateInput.addEventListener('change', () => {
                this.currentPage = 1;
                this.loadArtifacts(this.dateInput.value, this.statusSelect.value);
            });
        }

        if (this.statusSelect) {
            this.statusSelect.addEventListener('change', () => {
                this.currentPage = 1;
                this.loadArtifacts(this.dateInput.value, this.statusSelect.value);
            });
        }
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
                    limit: this.pageSize,
                    offset: (this.currentPage - 1) * this.pageSize
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.code === 0) {
                const { list, total } = result.data;
                this.total = total;
                this.artifacts = list;
                this.renderArtifacts(list);
                this.renderPagination();
            } else {
                console.error('加载失败:', result.msg);
                throw new Error(result.msg);
            }
        } catch (error) {
            console.error('请求失败:', error);
            const doc = this.frame.contentDocument;
            if (doc) {
                this.artifactList.innerHTML = `
                    <div class="text-gray-500 dark:text-gray-400 text-center py-8">
                        加载失败: ${error.message}
                    </div>
                `;
            }
        }
    }

    renderArtifacts(artifacts, clear = true) {
        if (clear) {
            this.artifactList.innerHTML = '';
        }
        
        artifacts.forEach(artifact => {
            const card = this.createArtifactCard(artifact);
            this.artifactList.appendChild(card);
        });
    }

    createArtifactCard(artifact) {
        const imageUrls = this.getAllImageUrls(artifact);
        const imageCount = imageUrls.length;
        const imageUrl = imageUrls[0].url || '';
        const card = document.createElement('div');
        card.className = 'artifact-item group rounded-lg bg-gray-900 p-1.5 hover:bg-gray-800 transition-colors duration-200 dark:bg-gray-900 dark:hover:bg-gray-800';
        card.setAttribute('data-id', artifact.id);
        
        card.innerHTML = `
                <div class="relative aspect-[4/3] overflow-hidden rounded">
                    <img src="${imageUrl}" 
                         class="h-full w-full object-cover cursor-zoom-in bt-artifact-preview-trigger artifact-image" 
                         alt="生成图片" 
                         data-current-index="0"
                         onerror="this.onerror=null; this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 1 1%22><rect width=%221%22 height=%221%22 fill=%22%23262626%22/></svg>'" />
                    <div class="absolute bottom-2 right-2 bg-black rounded-md w-8 h-8 flex items-center justify-center">
                        <span class="text-[15px] font-medium text-blue-400">${imageCount}</span>
                    </div>
                    ${imageCount > 1 ? `
                    <div class="absolute top-2 left-2 bg-black rounded-md w-8 h-8 flex items-center justify-center bt-prev-image-btn">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
                        </svg>
                    </div>
                    <div class="absolute top-2 right-2 bg-black rounded-md w-8 h-8 flex items-center justify-center bt-next-image-btn">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                    </div>
                    ` : ''}
                </div>
                <div class="mt-1.5">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-1.5">
                            <span class="inline-flex items-center rounded-full px-1.5 py-0.5 text-[11px] font-medium ${this.getStatusClass(artifact.result_status)}">
                                ${this.getStatusText(artifact.result_status)}
                            </span>
                            <span class="text-[11px] text-gray-500 dark:text-gray-400">${this.formatDate(artifact.created_at)}</span>
                        </div>
                        <div class="flex gap-0.5">
                            <!--<button class="view-btn rounded p-1 text-gray-500 hover:bg-gray-800 hover:text-gray-300 active:bg-gray-700 active:scale-95 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200 cursor-pointer group-hover:text-gray-300 transition-all" 
                                    title="查看详情">
                                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                </svg>
                            </button>-->
                            <button class="download-btn rounded p-1 text-gray-500 hover:bg-gray-800 hover:text-gray-300 active:bg-gray-700 active:scale-95 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200 cursor-pointer group-hover:text-gray-300 transition-all" 
                                    title="下载图片">
                                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                            </button>
                            <button class="delete-btn rounded p-1 text-gray-500 hover:bg-gray-800 hover:text-rose-300 active:bg-gray-700 active:scale-95 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-rose-300 cursor-pointer group-hover:text-gray-300 transition-all" 
                                    title="删除记录">
                                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                            </button>
                            <button class="load-btn rounded p-1 text-gray-500 hover:bg-gray-800 hover:text-emerald-300 active:bg-gray-700 active:scale-95 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-emerald-300 cursor-pointer group-hover:text-gray-300 transition-all" 
                                    title="加载工作流">
                                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
        `;

        // 使用业务性的class绑定点击事件
        const previewTrigger = card.querySelector('.bt-artifact-preview-trigger');
        previewTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showImagePreview(artifact);
        });

        // 如果有多张图片，绑定切换事件
        if (imageCount > 1) {
            const img = card.querySelector('.artifact-image');
            const prevBtn = card.querySelector('.bt-prev-image-btn');
            const nextBtn = card.querySelector('.bt-next-image-btn');
            
            prevBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const currentIndex = parseInt(img.dataset.currentIndex);
                if (currentIndex > 0) {
                    img.dataset.currentIndex = currentIndex - 1;
                    img.src = imageUrls[currentIndex - 1].url;
                }
            });
            
            nextBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const currentIndex = parseInt(img.dataset.currentIndex);
                if (currentIndex < imageUrls.length - 1) {
                    img.dataset.currentIndex = currentIndex + 1;
                    img.src = imageUrls[currentIndex + 1].url;
                }
            });
        }

        // 绑定事件监听
        // const viewBtn = card.querySelector('.view-btn');
        const downloadBtn = card.querySelector('.download-btn');
        const deleteBtn = card.querySelector('.delete-btn');
        const loadBtn = card.querySelector('.load-btn');

        // viewBtn.addEventListener('click', (e) => {
        //     e.stopPropagation();
        //     this.viewDetails(artifact);
        // });

        downloadBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const img = card.querySelector('.artifact-image');
            const currentIndex = parseInt(img.dataset.currentIndex);
            const currentImageInfo = imageUrls[currentIndex];
            this.downloadImage(currentImageInfo);
        });

        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteArtifact(artifact);
        });

        loadBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.loadWorkflow(artifact);
        });

        return card;
    }

    getStatusClass(status) {
        switch(status) {
            case '1': return 'bg-emerald-900/20 text-emerald-400 dark:bg-emerald-900/20 dark:text-emerald-400';
            case '0': return 'bg-amber-900/20 text-amber-400 dark:bg-amber-900/20 dark:text-amber-400';
            case '2': return 'bg-rose-900/20 text-rose-400 dark:bg-rose-900/20 dark:text-rose-400';
            default: return 'bg-gray-800/20 text-gray-400 dark:bg-gray-800/20 dark:text-gray-400';
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
        const outputs = artifact.outputs || {};
        const imageMap = {};
        for (const nodeId in outputs) {
            const output = outputs[nodeId];
            if (output.images && output.images.length > 0) {
                output.images.forEach(image => {
                    const url = `/api/view?filename=${image.filename}&type=${image.type}`;
                    if (!imageMap[image.type]) { 
                        imageMap[image.type] = [];
                    }
                    imageMap[image.type].push(url);
                });
            }
        }
        if(imageMap['output']) {
            return imageMap['output'][0];
        }
        if(imageMap['temp']) {
            return imageMap['temp'][0];
        }
        return '';
    }

    async downloadImage(imageInfo) {
        try {
            const {url,filename} = imageInfo;
            const response = await fetch(url);
            const blob = await response.blob();
            const blobUrl = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = filename || 'image.png';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(blobUrl);
        } catch (error) {
            console.error('下载图片失败:', error);
            app.ui.showToast('下载图片失败', 'error');
        }
    }

    async deleteArtifact(artifact) {
        if (!confirm('确定要删除这条记录吗？')) {
            return;
        }
        
        try {
            const response = await fetch('/bt/artifacts/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    id: artifact.id
                })
            });
            
            if (!response.ok) throw new Error('删除失败');
            
            const result = await response.json();
            if (result.code !== 0) {
                throw new Error(result.msg || '删除失败');
            }
            
            // 从界面上移除该元素
            const card = this.frame.contentDocument.querySelector(`[data-id="${artifact.id}"]`);
            if (card) {
                card.remove();
            }
            
            app.ui.showToast('删除成功', 'success');
            
            // 重新加载当前页面的数据
            await this.loadArtifacts(this.dateInput.value, this.statusSelect.value);
        } catch (error) {
            console.error('删除记录失败:', error);
            app.ui.showToast('删除记录失败', 'error');
        }
    }

    async loadWorkflow(artifact) {
        try {
            const imageUrl = this.getImageUrl(artifact);
            if (!artifact.prompt) {
                throw new Error('找不到对应的生成信息!');
            }

            const workflow = artifact.prompt[3].extra_pnginfo.workflow;
            if(!workflow) {
                throw new Error('找不到工作流!');
            }
            // 从图片加载工作流
            await app.loadGraphData(JSON.parse(JSON.stringify(workflow)))
            if (artifact.outputs) {
                app.nodeOutputs = JSON.parse(JSON.stringify(artifact.outputs))
            }
            app.ui.showToast('工作流加载成功', 'success');
        } catch (error) {
            console.error('加载工作流失败:', error);
            app.ui.showToast('加载工作流失败', 'error');
        }
    }

    renderPagination() {
        const totalPages = Math.ceil(this.total / this.pageSize);
        
        if (this.totalCountEl) {
            this.totalCountEl.textContent = `${this.total}`;
        }
        if (this.totalPagesEl) {
            this.totalPagesEl.textContent = `${totalPages}`;
        }
        if (this.currentPageEl) {
            this.currentPageEl.textContent = `${this.currentPage}`;
        }
        if (this.prevPageBtn) {
            this.prevPageBtn.disabled = this.currentPage <= 1;
        }
        if (this.nextPageBtn) {
            this.nextPageBtn.disabled = this.currentPage >= totalPages;
        }
    }

    getAllImageUrls(artifact) {
        if (!artifact || !artifact.outputs) {
            return [];
        }
        
        const outputs = artifact.outputs;
        const urls = [];
        
        // 首先添加输出图片
        for (const nodeId in outputs) {
            const output = outputs[nodeId];
            if (output.images && output.images.length > 0) {
                output.images
                    .filter(image => image.type === 'output')
                    .forEach(image => {
                        if (image && image.filename) {
                            const url = `/api/view?filename=${image.filename}&type=${image.type}`;
                            urls.push({url: url, filename: image.filename});
                        }
                    });
            }
        }
        
        // 如果没有找到任何图片，返回一个默认的空图片
        if (urls.length === 0) {
            return [{
                url: 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 1 1%22><rect width=%221%22 height=%221%22 fill=%22%23262626%22/></svg>',
                filename: 'empty.png'
            }];
        }
        
        return urls;
    }
} 
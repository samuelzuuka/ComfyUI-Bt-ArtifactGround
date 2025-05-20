console.log("====top====bt-artifact-ground====top====");
import { app } from "../../scripts/app.js";
import { ComfyDialog,$el } from "../../scripts/ui.js";

import {
	manager_instance, rebootAPI, install_via_git_url,
	fetchData, md5, icons, show_message, customConfirm, customAlert, customPrompt,
	sanitizeHTML, infoToast, showTerminal, setNeedRestart,
	storeColumnWidth, restoreColumnWidth, getTimeAgo, copyText, loadCss,
	showPopover, hidePopover
} from "./common.js";

loadCss("./style.css");

console.log("====begin====bt-artifact-ground====begin====");
console.log(app);
console.log($el);

class ArtifactGroundDialog extends ComfyDialog {
    constructor() {
        super();
        this.element.classList.add("artifact-ground-dialog");
        this.artifacts = [];
        this.currentPage = 0;
        this.pageSize = 20;
    }

    createContent() {
        // 创建对话框内容
        const content = document.createElement("div");
        content.innerHTML = `
            <div class="artifact-list"></div>
            <div class="pagination">
                <button class="prev-page">上一页</button>
                <span class="page-info"></span>
                <button class="next-page">下一页</button>
            </div>
        `;

        // 绑定事件
        const prevBtn = content.querySelector(".prev-page");
        const nextBtn = content.querySelector(".next-page");
        prevBtn.addEventListener("click", () => this.prevPage());
        nextBtn.addEventListener("click", () => this.nextPage());

        return content;
    }

    async show() {
        super.show();
        await this.loadArtifacts();
    }

    async loadArtifacts() {
        const response = await fetch(`/artifact_ground/artifacts?limit=${this.pageSize}&offset=${this.currentPage * this.pageSize}`);
        const data = await response.json();
        this.artifacts = data.artifacts;
        this.renderArtifacts();
    }

    renderArtifacts() {
        const listElement = this.element.querySelector(".artifact-list");
        listElement.innerHTML = "";

        this.artifacts.forEach(artifact => {
            const [id, imagePath, workflow, parameters, createdAt] = artifact;
            const artifactElement = document.createElement("div");
            artifactElement.classList.add("artifact-item");
            artifactElement.innerHTML = `
                <img src="${imagePath}" alt="Generated Image">
                <div class="artifact-info">
                    <div class="artifact-time">${new Date(createdAt).toLocaleString()}</div>
                    <button class="delete-btn" data-id="${id}">删除</button>
                    <button class="view-btn" data-id="${id}">查看详情</button>
                </div>
            `;

            // 绑定删除事件
            artifactElement.querySelector(".delete-btn").addEventListener("click", async () => {
                if (confirm("确定要删除这条记录吗？")) {
                    await this.deleteArtifact(id);
                }
            });

            // 绑定查看详情事件
            artifactElement.querySelector(".view-btn").addEventListener("click", () => {
                this.showDetails(artifact);
            });

            listElement.appendChild(artifactElement);
        });

        // 更新分页信息
        this.element.querySelector(".page-info").textContent = `第 ${this.currentPage + 1} 页`;
    }

    async deleteArtifact(id) {
        const response = await fetch(`/artifact_ground/artifacts/${id}`, {
            method: "DELETE"
        });
        const data = await response.json();
        if (data.success) {
            await this.loadArtifacts();
        }
    }

    showDetails(artifact) {
        const [id, imagePath, workflow, parameters, createdAt] = artifact;
        const detailsDialog = new ComfyDialog();
        detailsDialog.element.classList.add("artifact-details-dialog");
        detailsDialog.element.innerHTML = `
            <div class="details-content">
                <h3>生成详情</h3>
                <img src="${imagePath}" alt="Generated Image">
                <div class="details-info">
                    <h4>工作流配置</h4>
                    <pre>${JSON.parse(workflow)}</pre>
                    <h4>参数配置</h4>
                    <pre>${JSON.parse(parameters)}</pre>
                    <div class="created-time">生成时间: ${new Date(createdAt).toLocaleString()}</div>
                </div>
            </div>
        `;
        detailsDialog.show();
    }

    prevPage() {
        if (this.currentPage > 0) {
            this.currentPage--;
            this.loadArtifacts();
        }
    }

    nextPage() {
        this.currentPage++;
        this.loadArtifacts();
    }
}

// 添加菜单按钮
app.ui.menuContainer.appendChild((() => {
    const button = document.createElement("button");
    button.textContent = "生成记录";
    button.onclick = () => {
        const dialog = new ArtifactGroundDialog();
        dialog.show();
    };
    return button;
})());

// 注册插件
app.registerExtension({
    name: "Comfy.ArtifactGround",
    async setup() {
        // 监听新生成记录的消息
        app.api.addEventListener("artifact_ground_update", (event) => {
            // 可以在这里添加提示或自动刷新等功能
            app.ui.showMessage(`新的生成记录已保存: ${event.detail.data.timestamp}`, "success");
        });
    }
}); 

// app.registerExtension({
//     name: 'TestExtension',
//     // Define commands
//     commands: [
//         { 
//         id: "btArtifactGround", 
//         label: "历史构建", 
//         function: () => { alert("Command executed!"); } 
//         }
//     ],
//     // Add commands to menu
//     menuCommands: [
//         { 
//         // path: ["Extensions", "My Extension"], 
//         path: ["Extensions"], 
//         commands: ["btArtifactGround"] 
//         }
//     ],
//     bottomPanelTabs: [
//         {
//         id: 'TestTab',
//         title: 'Test Tab',
//         type: 'custom',
//         render: (el) => {
//             el.innerHTML = '<div>Custom tab</div>'
//         }
//         }
//     ]
// })

app.extensionManager.registerSidebarTab({
  id: "btArtifactGroupdSidebar",
  icon: "pi pi-compass",
  title: "构建记录",
  tooltip: "永久保存的生成历史记录",
  type: "custom",
  render: (el) => {
    // 添加 Tailwind CSS
    const link = document.createElement('link');
    link.href = 'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css';
    link.rel = 'stylesheet';
    document.head.appendChild(link);

    // 构建界面 HTML
    el.innerHTML = `
      <div class="flex flex-col h-full bg-gray-900 text-gray-100">
        <!-- 搜索和过滤区域 -->
        <div class="p-4 border-b border-gray-700">
          <div class="flex space-x-4 mb-4">
            <!-- 日期选择 -->
            <div class="flex-1">
              <input type="date" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <!-- 状态过滤 -->
            <select class="px-3 py-2 bg-gray-800 border border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">全部状态</option>
              <option value="1">已完成</option>
              <option value="0">处理中</option>
              <option value="2">失败</option>
            </select>
          </div>
        </div>

        <!-- 图片列表区域 -->
        <div class="flex-1 overflow-y-auto" id="artifactList">
          <!-- 图片项模板 -->
          <div class="relative p-4 border-b border-gray-700 hover:bg-gray-800">
            <div class="aspect-w-16 aspect-h-9 mb-2">
              <img src="" class="object-cover rounded-lg" alt="生成图片" />
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <span class="px-2 py-1 text-xs rounded-full bg-green-600">已完成</span>
                <span class="text-sm text-gray-400">2024-03-12 15:30</span>
              </div>
              <button class="p-2 hover:bg-gray-700 rounded-full">
                <i class="pi pi-download"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    // 初始化功能
    initArtifactList(el);
  }
});

// 初始化历史记录列表
function initArtifactList(el) {
  const dateInput = el.querySelector('input[type="date"]');
  const statusSelect = el.querySelector('select');
  const artifactList = el.querySelector('#artifactList');

  // 加载历史记录数据
  async function loadArtifacts(date = '', status = '') {
    try {
      const response = await fetch('/bt/artifacts/list?' + new URLSearchParams({
        date: date,
        status: status,
        limit: 20,
        offset: 0
      }));
      
      if (!response.ok) throw new Error('加载失败');
      
      const data = await response.json();
      renderArtifacts(data);
    } catch (error) {
      console.error('加载历史记录失败:', error);
    }
  }

  // 渲染历史记录列表
  function renderArtifacts(artifacts) {
    artifactList.innerHTML = artifacts.map(artifact => `
      <div class="relative p-4 border-b border-gray-700 hover:bg-gray-800" data-id="${artifact.id}">
        <div class="aspect-w-16 aspect-h-9 mb-2">
          <img src="${getImageUrl(artifact)}" class="object-cover rounded-lg" alt="生成图片" />
        </div>
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <span class="px-2 py-1 text-xs rounded-full ${getStatusClass(artifact.result_status)}">
              ${getStatusText(artifact.result_status)}
            </span>
            <span class="text-sm text-gray-400">${formatDate(artifact.created_at)}</span>
          </div>
          <button class="p-2 hover:bg-gray-700 rounded-full" onclick="downloadImage('${artifact.id}')">
            <i class="pi pi-download"></i>
          </button>
        </div>
      </div>
    `).join('');
  }

  // 获取状态样式
  function getStatusClass(status) {
    switch(status) {
      case '1': return 'bg-green-600';
      case '0': return 'bg-yellow-600';
      case '2': return 'bg-red-600';
      default: return 'bg-gray-600';
    }
  }

  // 获取状态文本
  function getStatusText(status) {
    switch(status) {
      case '1': return '已完成';
      case '0': return '处理中';
      case '2': return '失败';
      default: return '未知';
    }
  }

  // 格式化日期
  function formatDate(dateStr) {
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  // 获取图片URL
  function getImageUrl(artifact) {
    const outputs = JSON.parse(artifact.outputs || '{}');
    for (const nodeId in outputs) {
      const output = outputs[nodeId];
      if (output.images && output.images.length > 0) {
        return `/view?filename=${output.images[0].filename}`;
      }
    }
    return '';
  }

  // 事件监听
  dateInput.addEventListener('change', () => {
    loadArtifacts(dateInput.value, statusSelect.value);
  });

  statusSelect.addEventListener('change', () => {
    loadArtifacts(dateInput.value, statusSelect.value);
  });

  // 初始加载
  loadArtifacts();
}
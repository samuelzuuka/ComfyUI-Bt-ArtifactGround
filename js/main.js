console.log("====top====bt-artifact-ground====top====");
import { app } from "../../scripts/app.js";
import { ComfyDialog,$el } from "../../scripts/ui.js";
import { ArtifactList } from "./artifact-list.js";

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

app.extensionManager.registerSidebarTab({
    id: "btArtifactGroupdSidebar",
    icon: "pi pi-compass",
    title: "构建记录",
    tooltip: "永久保存的生成历史记录",
    type: "custom",
    render: (el) => {
        // 初始化历史记录列表
        app.artifactList = new ArtifactList(el);
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


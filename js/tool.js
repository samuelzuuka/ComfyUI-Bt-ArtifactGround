import { app } from "../../scripts/app.js";

// 注册扩展
app.registerExtension({
    name: "Bt-ArtifactGround-Tool",
    async setup() {
        // 监听 WebSocket 消息
        const messageHandler = (event) => {
            const data = event.detail || {};
            console.log("messageHandler", event, data);
            const event_type = event.type;
            if (event_type === "bt_toast") {
                // 显示 Toast 消息
                app.extensionManager.toast.add({
                    severity: data.severity || 'info',  // 消息类型：info, success, warn, error
                    summary: data.summary || '',        // 标题
                    detail: data.detail || '',          // 详细内容
                    life: data.life || 3000            // 显示时长（毫秒）
                });
            } else if (event_type === "bt_alert") {
                app.extensionManager.toast.addAlert(data.detail || "发生错误");
            }
        };

        // 注册消息处理器
        app.api.addEventListener("bt_toast", messageHandler);
        app.api.addEventListener("bt_alert", messageHandler);
    }
});


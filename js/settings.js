import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "BtArtifactGround.Settings",
    async setup() {
        const settings = [
            {
                id: "BtArtifactGround.server.enabled",
                name: "启用上传服务",
                type: "boolean",
                defaultValue: true,
                tooltip: "是否启用图片上传服务"
            },
            {
                id: "BtArtifactGround.server.url",
                name: "服务器地址",
                type: "text",
                defaultValue: "",
                tooltip: "图片上传服务器的地址"
            },
            {
                id: "BtArtifactGround.server.token",
                name: "认证令牌",
                type: "text",
                defaultValue: "",
                attrs: {
                    type: "password"
                },
                tooltip: "访问服务器所需的认证令牌,会放到:请求头-\"token\"中,后台接口需根据此token进行鉴权"
            },
            {
                id: "BtArtifactGround.upload.auto",
                name: "自动上传",
                type: "boolean",
                defaultValue: true,
                tooltip: "是否在生成图片后自动上传"
            },
            // {
            //     id: "BtArtifactGround.upload.deleteLocal",
            //     name: "上传后删除本地文件",
            //     type: "boolean",
            //     defaultValue: false,
            //     tooltip: "上传成功后是否删除本地文件"
            // },
            {
                id: "BtArtifactGround.upload.timeout",
                name: "超时时间(毫秒)",
                type: "number",
                defaultValue: 30000,
                attrs: {
                    min: 1000,
                    max: 300000,
                    step: 1000,
                    showButtons: true
                },
                tooltip: "上传请求的超时时间"
            },
            {
                id: "BtArtifactGround.upload.retryCount",
                name: "重试次数",
                type: "number",
                defaultValue: 3,
                attrs: {
                    min: 0,
                    max: 10,
                    step: 1,
                    showButtons: true
                },
                tooltip: "上传失败后的重试次数"
            },
            {
                id: "BtArtifactGround.upload.concurrent",
                name: "并发上传数",
                type: "number",
                defaultValue: 3,
                attrs: {
                    min: 1,
                    max: 10,
                    step: 1,
                    showButtons: true
                },
                tooltip: "同时上传的最大文件数"
            }
        ];

        // 注册所有设置
        for (const setting of settings) {
            app.ui.settings.addSetting(setting);
        }
    }
});

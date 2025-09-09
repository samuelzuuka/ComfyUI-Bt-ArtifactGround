import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "BtArtifactGround.Settings",
    async setup() {
        const settings = [
            {
                id: "BtArtifactGround.server.url",
                name: "服务器地址",
                type: "text",
                defaultValue: "",
                category: ["BtArtifactGround", "服务器配置", "服务器地址"],
                tooltip: "图片上传服务器的地址"
            },
            {
                id: "BtArtifactGround.server.tokenField",
                name: "Token字段",
                type: "text",
                defaultValue: "token",
                category: ["BtArtifactGround", "服务器配置", "Token字段"],
                tooltip: "访问服务器所需的鉴权Token对应的字段,默认为:'token',需要使用Http请求头支持的合法字段"
            },
            {
                id: "BtArtifactGround.server.token",
                name: "Token值",
                type: "text",
                defaultValue: "",
                category: ["BtArtifactGround", "服务器配置", "Token值"],
                attrs: {
                    type: "password"
                },
                tooltip: "访问服务器所需的鉴权Token,会放到:请求头-<Token字段>中,后台接口需根据此token进行鉴权"
            },

            {
                id: "BtArtifactGround.upload.method",
                name: "上传方式",
                type: "combo",
                defaultValue: "http",
                options: [
                    { text: "服务器上传", value: "http" },
                    { text: "阿里云OSS", value: "oss" }
                ],
                category: ["BtArtifactGround", "上传配置", "上传方式"],
                tooltip: "选择文件上传的方式,服务器上传:直接通过http请求上传到对应服务器;阿里云OSS:通过阿里云OSS上传到指定Bucket,再把url推送到服务器(oss带宽足够大)"
            },
            {
                id: "BtArtifactGround.oss.accessKeyId",
                name: "阿里云OSS AccessKeyId",
                type: "text",
                defaultValue: "",
                category: ["BtArtifactGround", "OSS配置", "AccessKeyId"],
                tooltip: "阿里云OSS的AccessKeyId"
            },
            {
                id: "BtArtifactGround.oss.accessKeySecret",
                name: "阿里云OSS AccessKeySecret",
                type: "text",
                defaultValue: "",
                category: ["BtArtifactGround", "OSS配置", "AccessKeySecret"],
                tooltip: "阿里云OSS的AccessKeySecret"
            },
            {
                id: "BtArtifactGround.oss.endpoint",
                name: "阿里云OSS自定义Endpoint",
                type: "text",
                defaultValue: "",
                category: ["BtArtifactGround", "OSS配置", "自定义Endpoint"],
                tooltip: "阿里云OSS的自定义Endpoint,用于对外提供地址"
            },
            {
                id: "BtArtifactGround.oss.regionEndpoint",
                name: "阿里云OSS地域Endpoint",
                type: "text",
                defaultValue: "",
                category: ["BtArtifactGround", "OSS配置", "地域Endpoint"],
                tooltip: "阿里云OSS的地域Endpoint,用于上传文件"
            },
            {
                id: "BtArtifactGround.oss.region",
                name: "阿里云OSS Region",
                type: "text",
                defaultValue: "",
                category: ["BtArtifactGround", "OSS配置", "Region"],
                tooltip: "阿里云OSS的Region"
            },
            {
                id: "BtArtifactGround.oss.bucket",
                name: "阿里云OSS Bucket",
                type: "text",
                defaultValue: "",
                category: ["BtArtifactGround", "OSS配置", "Bucket"],
                tooltip: "阿里云OSS的Bucket"
            },
            {
                id: "BtArtifactGround.oss.directory", 
                name: "阿里云OSS 默认目录",
                type: "text",
                defaultValue: "comfyui",
                category: ["BtArtifactGround", "OSS配置", "默认目录"],
                tooltip: "阿里云OSS的默认上传目录,文件将上传到此目录下"
            },
            {
                id: "BtArtifactGround.upload.timeout",
                name: "超时时间(毫秒)",
                type: "number",
                defaultValue: 30000,
                category: ["BtArtifactGround", "上传配置", "超时时间"],
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
                category: ["BtArtifactGround", "上传配置", "重试次数"],
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
                category: ["BtArtifactGround", "上传配置", "并发上传数"],
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

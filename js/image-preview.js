export class ImagePreview {
    constructor() {
        this.createPreviewOverlay();
    }

    createPreviewOverlay() {
        // 检查是否已存在预览组件
        const existingOverlay = document.querySelector('#bt-image-preview-overlay');
        if (existingOverlay) {
            this.previewOverlay = existingOverlay;
            return;
        }

        // 创建样式
        const style = document.createElement('style');
        style.textContent = `
            #bt-image-preview-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(0, 0, 0, 0.9);
                z-index: 10000;
                display: none;
                align-items: center;
                justify-content: center;
                cursor: zoom-out;
            }

            #bt-image-preview-overlay.active {
                display: flex;
            }

            .bt-image-preview-container {
                position: relative;
                max-width: 90vw;
                max-height: 90vh;
            }

            .bt-image-preview-container img {
                max-width: 100%;
                max-height: 90vh;
                object-fit: contain;
            }

            .bt-image-preview-close {
                position: absolute;
                top: -40px;
                right: 0;
                color: white;
                cursor: pointer;
                padding: 8px;
                font-size: 28px;
                background: rgba(0, 0, 0, 0.5);
                border-radius: 50%;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .bt-image-preview-nav {
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                color: white;
                cursor: pointer;
                font-size: 28px;
                background: rgba(0, 0, 0, 0.5);
                border-radius: 50%;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .bt-image-preview-prev {
                left: -60px;
            }

            .bt-image-preview-next {
                right: -60px;
            }

            .bt-image-preview-counter {
                position: absolute;
                bottom: -30px;
                left: 50%;
                transform: translateX(-50%);
                color: white;
                font-size: 14px;
            }
        `;
        document.head.appendChild(style);

        // 创建预览组件
        const overlay = document.createElement('div');
        overlay.id = 'bt-image-preview-overlay';
        overlay.innerHTML = `
            <div class="bt-image-preview-container">
                <div class="bt-image-preview-close">&times;</div>
                <img src="" alt="预览图片" />
                <div class="bt-image-preview-nav bt-image-preview-prev">&lt;</div>
                <div class="bt-image-preview-nav bt-image-preview-next">&gt;</div>
                <div class="bt-image-preview-counter"></div>
            </div>
        `;
        document.body.appendChild(overlay);
        this.previewOverlay = overlay;
    }

    showPreview(imageUrls) {
        const overlay = this.previewOverlay;
        const previewImg = overlay.querySelector('img');
        const closeBtn = overlay.querySelector('.bt-image-preview-close');
        const prevBtn = overlay.querySelector('.bt-image-preview-prev');
        const nextBtn = overlay.querySelector('.bt-image-preview-next');
        const counter = overlay.querySelector('.bt-image-preview-counter');

        let currentIndex = 0;

        const updatePreviewImage = () => {
            previewImg.src = imageUrls[currentIndex];
            // 更新导航按钮状态
            prevBtn.style.display = currentIndex > 0 ? 'flex' : 'none';
            nextBtn.style.display = currentIndex < imageUrls.length - 1 ? 'flex' : 'none';
            // 更新计数器
            counter.textContent = `${currentIndex + 1} / ${imageUrls.length}`;
        };

        // 初始化预览图片
        updatePreviewImage();

        // 显示预览
        overlay.classList.add('active');

        // 绑定关闭事件
        const closePreview = () => {
            overlay.classList.remove('active');
        };

        closeBtn.onclick = closePreview;
        overlay.onclick = (e) => {
            if (e.target === overlay) {
                closePreview();
            }
        };

        // 绑定键盘事件
        const handleKeydown = (e) => {
            if (e.key === 'Escape') {
                closePreview();
            } else if (e.key === 'ArrowLeft' && currentIndex > 0) {
                currentIndex--;
                updatePreviewImage();
            } else if (e.key === 'ArrowRight' && currentIndex < imageUrls.length - 1) {
                currentIndex++;
                updatePreviewImage();
            }
        };

        document.addEventListener('keydown', handleKeydown);

        // 绑定导航按钮事件
        prevBtn.onclick = (e) => {
            e.stopPropagation();
            if (currentIndex > 0) {
                currentIndex--;
                updatePreviewImage();
            }
        };

        nextBtn.onclick = (e) => {
            e.stopPropagation();
            if (currentIndex < imageUrls.length - 1) {
                currentIndex++;
                updatePreviewImage();
            }
        };

        // 清理事件监听
        overlay.addEventListener('transitionend', () => {
            if (!overlay.classList.contains('active')) {
                document.removeEventListener('keydown', handleKeydown);
            }
        });
    }
} 
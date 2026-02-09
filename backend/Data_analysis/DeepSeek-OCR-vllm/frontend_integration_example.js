/**
 * 前端集成示例 - 调用后端OCR API
 *
 * 基于你的test文件，展示如何与后端API进行交互
 */

// 配置
const API_BASE_URL = 'http://localhost:8708';

/**
 * 上传文件进行OCR处理
 * @param {File} file - 上传的文件
 * @param {Object} options - 处理选项
 * @returns {Promise} - 处理结果
 */
async function uploadFileForOCR(file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('enable_description', options.enableDescription || false);
    formData.append('use_real_service', options.useRealService || false);

    try {
        const response = await fetch(`${API_BASE_URL}/ocr`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('OCR上传失败:', error);
        throw error;
    }
}

/**
 * 直接调用真实OCR服务
 * @param {File} file - 上传的文件
 * @param {boolean} enableDescription - 是否启用图片描述
 * @returns {Promise} - 处理结果
 */
async function callRealOCR(file, enableDescription = false) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('enable_description', enableDescription);

    try {
        const response = await fetch(`${API_BASE_URL}/ocr/real`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('真实OCR调用失败:', error);
        throw error;
    }
}

/**
 * 获取处理结果列表
 * @returns {Promise} - 结果列表
 */
async function getResultsList() {
    try {
        const response = await fetch(`${API_BASE_URL}/results`);

        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('获取结果列表失败:', error);
        throw error;
    }
}

/**
 * 下载处理结果文件
 * @param {string} filename - 文件名
 */
async function downloadResult(filename) {
    try {
        const response = await fetch(`${API_BASE_URL}/download/${filename}`);

        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('下载失败:', error);
        throw error;
    }
}

/**
 * 检查服务健康状态
 * @returns {Promise} - 健康状态
 */
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return await response.json();
    } catch (error) {
        console.error('健康检查失败:', error);
        throw error;
    }
}

// ==================== 使用示例 ====================

/**
 * 示例1: 基本文件上传和OCR处理
 */
async function example1_BasicUpload() {
    console.log('=== 示例1: 基本文件上传 ===');

    // 模拟文件选择
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.jpg,.jpeg,.png,.pdf,.txt,.md';

    // 在实际使用中，这样获取文件:
    // fileInput.onchange = async (e) => {
    //     const file = e.target.files[0];
    //     if (file) {
    //         try {
    //             const result = await uploadFileForOCR(file, {
    //                 enableDescription: true,
    //                 useRealService: false  // 使用模拟服务
    //             });
    //             console.log('OCR结果:', result);
    //         } catch (error) {
    //             console.error('处理失败:', error);
    //         }
    //     }
    // };

    console.log('请参考注释中的代码了解如何使用');
}

/**
 * 示例2: 批量文件处理
 */
async function example2_BatchProcessing() {
    console.log('=== 示例2: 批量文件处理 ===');

    // 获取多个文件
    const files = [
        { name: 'document1.pdf', size: 1024000 },
        { name: 'image1.jpg', size: 512000 },
        { name: 'report.txt', size: 25600 }
    ];

    console.log('批量处理示例代码:');
    console.log(`
    const files = fileInput.files;
    const results = [];

    for (let i = 0; i < files.length; i++) {
        try {
            const result = await uploadFileForOCR(files[i], {
                enableDescription: true,
                useRealService: false
            });
            results.push(result);
            console.log(\`文件 \${i+1}/\${files.length} 处理完成\`);
        } catch (error) {
            console.error(\`文件 \${files[i].name} 处理失败:\`, error);
        }
    }

    console.log('批量处理完成，结果:', results);
    `);
}

/**
 * 示例3: 真实OCR服务调用
 */
async function example3_RealOCRService() {
    console.log('=== 示例3: 真实OCR服务调用 ===');

    console.log('调用真实OCR服务示例:');
    console.log(`
    // 调用真实的DeepSeek-OCR服务
    try {
        const result = await callRealOCR(file, true); // 启用图片描述
        console.log('真实OCR结果:', result);

        // 保存结果
        if (result.saved_files) {
            await downloadResult(result.saved_files.json_file.split('/').pop());
            await downloadResult(result.saved_files.md_file.split('/').pop());
        }
    } catch (error) {
        console.error('真实OCR调用失败:', error);

        // 如果真实服务失败，可以降级到模拟服务
        console.log('降级到模拟服务...');
        const fallbackResult = await uploadFileForOCR(file, {
            enableDescription: true,
            useRealService: false
        });
        console.log('模拟服务结果:', fallbackResult);
    }
    `);
}

/**
 * 示例4: 结果管理和下载
 */
async function example4_ResultManagement() {
    console.log('=== 示例4: 结果管理和下载 ===');

    try {
        // 获取结果列表
        const resultsList = await getResultsList();
        console.log('处理结果列表:', resultsList);

        // 下载指定结果
        if (resultsList.results.length > 0) {
            const firstResult = resultsList.results[0];
            console.log(`下载第一个结果: ${firstResult.filename}`);
            // await downloadResult(firstResult.filename);
        }

        console.log(`
        // 获取结果列表的完整示例
        const resultsList = await getResultsList();
        console.log(\`共有 \${resultsList.total} 个处理结果\`);

        // 显示结果列表
        resultsList.results.forEach(result => {
            console.log(\`- \${result.original_name} (\${result.page_count}页)\`);
        });

        // 下载所有JSON结果
        for (const result of resultsList.results) {
            await downloadResult(result.filename);
        }
        `);

    } catch (error) {
        console.error('结果管理失败:', error);
    }
}

/**
 * 示例5: 完整的文件处理流程
 */
async function example5_CompleteWorkflow() {
    console.log('=== 示例5: 完整处理流程 ===');

    console.log(`
    // 完整的前端处理流程
    async function completeWorkflow(file) {
        try {
            // 1. 检查服务状态
            const health = await checkHealth();
            console.log('服务状态:', health);

            // 2. 显示处理进度
            showProgress('正在上传文件...');

            // 3. 先尝试模拟处理（快速响应）
            const mockResult = await uploadFileForOCR(file, {
                enableDescription: true,
                useRealService: false
            });

            console.log('模拟处理完成:', mockResult);
            showProgress('模拟处理完成，开始真实OCR处理...');

            // 4. 后台进行真实OCR处理
            const realResult = await callRealOCR(file, true);
            console.log('真实处理完成:', realResult);

            // 5. 保存和显示结果
            displayResults(realResult);

            // 6. 提供下载选项
            enableDownloads(realResult.saved_files);

        } catch (error) {
            console.error('处理失败:', error);
            showError(error.message);
        }
    }

    // 辅助函数
    function showProgress(message) {
        console.log('进度:', message);
        // 更新UI显示进度
    }

    function displayResults(result) {
        console.log('显示结果:', result);
        // 在页面上显示OCR结果
    }

    function enableDownloads(savedFiles) {
        console.log('启用下载:', savedFiles);
        // 添加下载按钮和功能
    }

    function showError(message) {
        console.error('错误:', message);
        // 显示错误信息给用户
    }
    `);
}

// ==================== 工具函数 ====================

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 验证文件类型
 */
function validateFileType(file) {
    const allowedTypes = [
        'image/jpeg', 'image/jpg', 'image/png',
        'application/pdf', 'text/plain', 'text/markdown'
    ];
    return allowedTypes.includes(file.type) ||
           file.name.match(/\.(jpg|jpeg|png|pdf|txt|md)$/i);
}

/**
 * 验证文件大小
 */
function validateFileSize(file, maxSizeMB = 100) {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    return file.size <= maxSizeBytes;
}

// 导出函数供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        uploadFileForOCR,
        callRealOCR,
        getResultsList,
        downloadResult,
        checkHealth,
        formatFileSize,
        validateFileType,
        validateFileSize
    };
}

// ==================== 自动运行示例 ====================
console.log('🚀 前端集成示例已加载');
console.log('📖 可用的API端点:', {
    base: API_BASE_URL,
    ocr: `${API_BASE_URL}/ocr`,
    realOCR: `${API_BASE_URL}/ocr/real`,
    results: `${API_BASE_URL}/results`,
    download: `${API_BASE_URL}/download/{filename}`,
    health: `${API_BASE_URL}/health`
});

// 在浏览器中运行示例
if (typeof window !== 'undefined') {
    example1_BasicUpload();
    example2_BatchProcessing();
    example3_RealOCRService();
    example4_ResultManagement();
    example5_CompleteWorkflow();
}
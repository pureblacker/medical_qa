let sessionId = null;

// 初始化会话
async function initSession() {
    const res = await fetch('/init_session');
    const data = await res.json();
    sessionId = data.session_id;
    document.getElementById('session_id').value = sessionId;
}

// 提交问题
document.getElementById('ask-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const questionInput = document.getElementById('question');
    const askButton = document.getElementById('ask-button');
    const loading = document.getElementById('loading');
    const thinking = document.getElementById('thinking');

    const question = questionInput.value.trim();
    if (!question) return;

    // 禁用按钮 + 显示加载动画
    askButton.disabled = true;
    loading.style.display = 'inline-block';
    thinking.style.display = 'block';

    try {
        const res = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `question=${encodeURIComponent(question)}&session_id=${encodeURIComponent(sessionId)}`
        });

        const data = await res.json();

        // 清空输入框
        questionInput.value = '';

        // 显示回答
        const historySection = document.getElementById('chat-history');
        historySection.innerHTML += `
            <div class="message user">${data.question}</div>
            <div class="message ai">
                <div class="markdown-content" data-markdown="${data.answer}"></div>
            </div>
        `;

        // 渲染 Markdown
        document.querySelectorAll('[data-markdown]').forEach(el => {
            el.innerHTML = marked.parse(el.getAttribute('data-markdown'));
        });

        // 显示 RAG/KG 内容框
        const contextSection = document.getElementById('context-section');
        contextSection.style.display = 'block';

        // 显示 RAG 内容
        const ragContext = document.getElementById('rag-context');
        ragContext.innerHTML = '';
        data.rag_context.forEach(ctx => {
            ragContext.innerHTML += `<li>${ctx}</li>`;
        });

        // 显示 KG 内容
        const kgContext = document.getElementById('kg-context');
        kgContext.innerHTML = '';
        data.kg_context.forEach(ctx => {
            kgContext.innerHTML += `<li>${ctx}</li>`;
        });
    } catch (error) {
        console.error('请求失败:', error);
        alert('请求失败，请稍后再试');
    } finally {
        // 启用按钮 + 隐藏加载动画
        askButton.disabled = false;
        loading.style.display = 'none';
        thinking.style.display = 'none';
    }
});

// 初始化
initSession();
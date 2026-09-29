// mermaid 初始化——Material 只注入库, 不会自动调用 initialize/run。
// 必须显式初始化并渲染所有 .mermaid 容器(由 pymdownx.superfences fence_div_format 生成)。
(function () {
  if (typeof window.mermaid === 'undefined') return;

  window.mermaid.initialize({
    startOnLoad: false, // 我们手动 run, 避免重复渲染
    securityLevel: 'loose',
    theme: 'default',
    flowchart: { htmlLabels: true, curve: 'basis' },
    sequence: { useMaxWidth: true }
  });

  function render() {
    var blocks = document.querySelectorAll('div.mermaid, span.mermaid');
    if (blocks.length === 0) return;
    window.mermaid.run({
      nodes: blocks,
      suppressErrors: true
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', render);
  } else {
    render();
  }
})();
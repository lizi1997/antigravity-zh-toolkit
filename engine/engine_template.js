// Antigravity Client Modern Chinese Localization Engine v3.1
// Sandboxed Electron compatible with embedded dictionary and real-time DOM translation

(function() {
    let currentLang = 'zh';
    try {
        currentLang = localStorage.getItem('antigravity_lang') || 'zh';
    } catch (e) {
        console.error('[AG-ZH] Failed to read lang preference:', e);
    }

    const translations = __TRANSLATIONS_JSON__;
    const rawPatterns = __PATTERNS_JSON__;

    const lowerTranslations = {};
    for (const key in translations) {
        lowerTranslations[key.toLowerCase()] = translations[key];
    }

    const patterns = rawPatterns.map(p => ({
        regex: new RegExp(p.pattern, p.flags || 'i'),
        replace: p.replacement
    }));

    // Proxy native dialogs
    if (typeof window !== 'undefined') {
        const _alert = window.alert;
        window.alert = function(msg) {
            if (typeof msg === 'string') {
                const translated = translateText(msg);
                _alert(translated !== null ? translated : msg);
            } else {
                _alert(msg);
            }
        };

        const _confirm = window.confirm;
        window.confirm = function(msg) {
            if (typeof msg === 'string') {
                const translated = translateText(msg);
                return _confirm(translated !== null ? translated : msg);
            } else {
                return _confirm(msg);
            }
        };
    }

    const TRANSLATABLE_ATTRS = [
        'placeholder',
        'title',
        'aria-label',
        'aria-description',
        'aria-placeholder',
        'data-tooltip',
        'tooltip',
        'data-tip',
        'data-title',
        'data-placeholder',
        'alt'
    ];

    // Untranslated tracker
    const untranslatedSet = new Set();
    try {
        const existing = JSON.parse(localStorage.getItem('ag_untranslated') || '[]');
        existing.forEach(item => untranslatedSet.add(item));
    } catch (e) {}

    function recordUntranslated(str) {
        if (!str || str.length < 2 || str.length > 300) return;
        if (/^[0-9\s:._\-/\+$,#&'"\[\]{}()\\<>=!*?|`@%]+$/.test(str)) return;
        if (/[一-鿿]/.test(str)) return;
        if (!untranslatedSet.has(str)) {
            untranslatedSet.add(str);
            try {
                localStorage.setItem('ag_untranslated', JSON.stringify(Array.from(untranslatedSet)));
            } catch (e) {}
        }
    }

    function translateText(text, node) {
        if (currentLang === 'en') return null;
        if (!text) return null;
        const trimmed = text.trim();
        if (!trimmed) return null;

        // Skip if already contains Chinese
        if (/[一-鿿]/.test(trimmed)) return null;
        if (trimmed.length > 500) return null;

        // 1. Exact match
        if (translations[trimmed]) {
            return text.replace(trimmed, translations[trimmed]);
        }

        // 2. Case-insensitive match
        const lower = trimmed.toLowerCase();
        if (lowerTranslations[lower]) {
            return text.replace(trimmed, lowerTranslations[lower]);
        }

        // 3. Dynamic regex patterns
        for (const p of patterns) {
            if (p.regex.test(trimmed)) {
                const replaced = trimmed.replace(p.regex, p.replace);
                return text.replace(trimmed, replaced);
            }
        }

        // Record as untranslated
        recordUntranslated(trimmed);
        return null;
    }

    function translateElementAttrs(node) {
        if (!node || node.nodeType !== 1) return;
        for (const attr of TRANSLATABLE_ATTRS) {
            const val = node.getAttribute(attr);
            if (val) {
                const translated = translateText(val, node);
                if (translated !== null && val !== translated) {
                    node.setAttribute(attr, translated);
                }
            }
        }
    }

    const observedRoots = new WeakSet();

    function translateDOM(root) {
        if (!root) return;

        // Try injecting switcher
        if (root.nodeType === 1) {
            try { injectLanguageSwitcher(); } catch (e) {}
        }

        // Handle Shadow DOM if present
        if (root.shadowRoot && !observedRoots.has(root.shadowRoot)) {
            observedRoots.add(root.shadowRoot);
            translateDOM(root.shadowRoot);
            observeSubtree(root.shadowRoot);
        }

        // Handle Text Node
        if (root.nodeType === 3) {
            const val = root.nodeValue;
            const translated = translateText(val, root);
            if (translated !== null && val !== translated) {
                root.nodeValue = translated;
            }
            return;
        }

        // Handle Element Node
        if (root.nodeType === 1) {
            translateElementAttrs(root);

            if (nodeIsInputButton(root)) {
                const val = root.value;
                const translated = translateText(val, root);
                if (translated !== null && val !== translated) {
                    root.value = translated;
                }
            }
        }

        // Walk DOM Subtree
        try {
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
            let node;
            while ((node = walker.nextNode())) {
                if (node.shadowRoot && !observedRoots.has(node.shadowRoot)) {
                    observedRoots.add(node.shadowRoot);
                    translateDOM(node.shadowRoot);
                    observeSubtree(node.shadowRoot);
                }

                if (node.nodeType === 3) {
                    const val = node.nodeValue;
                    const translated = translateText(val, node);
                    if (translated !== null && val !== translated) {
                        node.nodeValue = translated;
                    }
                } else if (node.nodeType === 1) {
                    translateElementAttrs(node);
                    if (nodeIsInputButton(node)) {
                        const val = node.value;
                        const translated = translateText(val, node);
                        if (translated !== null && val !== translated) {
                            node.value = translated;
                        }
                    }
                }
            }
        } catch (e) {}
    }

    function nodeIsInputButton(node) {
        return node.tagName === 'INPUT' && (node.type === 'button' || node.type === 'submit' || node.type === 'reset');
    }

    function observeSubtree(target) {
        if (!target) return;
        const obs = new MutationObserver((mutations) => {
            obs.disconnect();
            for (const mutation of mutations) {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(n => translateDOM(n));
                } else if (mutation.type === 'characterData') {
                    const node = mutation.target;
                    const val = node.nodeValue;
                    const translated = translateText(val, node);
                    if (translated !== null && val !== translated) {
                        node.nodeValue = translated;
                    }
                }
            }
            obs.observe(target, { childList: true, subtree: true, characterData: true });
        });
        obs.observe(target, { childList: true, subtree: true, characterData: true });
    }

    function startMainObserver() {
        if (!document.body) return;
        observeSubtree(document.body);
    }

    function startPeriodicScan() {
        setInterval(() => {
            if (document.body) {
                try { injectLanguageSwitcher(); } catch (e) {}
                translateDOM(document.body);
            }
        }, 2000);
    }

    function injectLanguageSwitcher() {
        if (document.getElementById('antigravity-lang-switcher')) return;

        // Search for titlebar or menu container
        const menuItems = Array.from(document.querySelectorAll('*'));
        let targetEl = null;
        for (const el of menuItems) {
            if (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3) {
                const text = el.textContent.trim();
                if (text === 'Window' || text === '窗口' || text === 'Help' || text === '帮助') {
                    targetEl = el;
                    break;
                }
            }
        }

        if (!targetEl && document.body) {
            // Fallback floating toggle if menu item not found
            const floatBtn = document.createElement('div');
            floatBtn.id = 'antigravity-lang-switcher';
            floatBtn.textContent = currentLang === 'zh' ? '中/EN' : 'EN/中';
            floatBtn.title = '点击切换语言 (Switch Language)';
            floatBtn.style.position = 'fixed';
            floatBtn.style.top = '6px';
            floatBtn.style.right = '140px';
            floatBtn.style.zIndex = '999999';
            floatBtn.style.padding = '2px 8px';
            floatBtn.style.fontSize = '11px';
            floatBtn.style.background = 'rgba(128,128,128,0.2)';
            floatBtn.style.border = '1px solid rgba(128,128,128,0.3)';
            floatBtn.style.borderRadius = '4px';
            floatBtn.style.cursor = 'pointer';
            floatBtn.style.userSelect = 'none';
            floatBtn.style.color = 'inherit';
            floatBtn.addEventListener('click', () => {
                const nextLang = currentLang === 'zh' ? 'en' : 'zh';
                localStorage.setItem('antigravity_lang', nextLang);
                location.reload();
            });
            document.body.appendChild(floatBtn);
            return;
        }

        if (targetEl && targetEl.parentNode) {
            const btn = document.createElement(targetEl.tagName || 'div');
            btn.className = targetEl.className;
            if (targetEl.getAttribute('style')) {
                btn.setAttribute('style', targetEl.getAttribute('style'));
            }
            btn.id = 'antigravity-lang-switcher';
            btn.textContent = currentLang === 'zh' ? 'EN' : '中文';
            btn.title = currentLang === 'zh' ? '点击切换为英文 (Switch to English)' : '点击切换为中文 (Switch to Chinese)';
            btn.style.cursor = 'pointer';
            btn.style.userSelect = 'none';
            btn.style.marginLeft = '8px';
            btn.style.marginRight = '8px';
            btn.style.padding = '0 8px';
            btn.style.display = 'inline-flex';
            btn.style.alignItems = 'center';
            btn.style.justifyContent = 'center';
            btn.style.fontWeight = '500';
            btn.style.opacity = '0.85';
            btn.style.transition = 'all 0.2s ease';

            btn.addEventListener('mouseenter', () => {
                btn.style.opacity = '1';
                btn.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
            });
            btn.addEventListener('mouseleave', () => {
                btn.style.opacity = '0.85';
                btn.style.backgroundColor = 'transparent';
            });
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const nextLang = currentLang === 'zh' ? 'en' : 'zh';
                localStorage.setItem('antigravity_lang', nextLang);
                location.reload();
            });

            targetEl.parentNode.insertBefore(btn, targetEl.nextSibling);
        }
    }

    // Global shortcut Ctrl+Alt+L to export untranslated text
    window.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.altKey && (e.key === 'l' || e.key === 'L')) {
            const list = Array.from(untranslatedSet);
            const jsonStr = JSON.stringify(list, null, 2);
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(jsonStr).then(() => {
                    showToast(`已复制 ${list.length} 条待翻译词汇到剪贴板！`);
                }).catch(() => {
                    showToast(`提取到 ${list.length} 条待翻译词汇 (已存入 localStorage)`);
                });
            } else {
                showToast(`提取到 ${list.length} 条待翻译词汇 (已存入 localStorage)`);
            }
        }
    });

    function showToast(msg) {
        const toast = document.createElement('div');
        toast.textContent = msg;
        toast.style.position = 'fixed';
        toast.style.bottom = '24px';
        toast.style.right = '24px';
        toast.style.background = '#1e8e3e';
        toast.style.color = '#ffffff';
        toast.style.padding = '10px 18px';
        toast.style.borderRadius = '8px';
        toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
        toast.style.zIndex = '999999';
        toast.style.fontSize = '14px';
        toast.style.fontWeight = '500';
        toast.style.transition = 'opacity 0.4s ease';
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 400);
        }, 3000);
    }

    // Initialize
    function init() {
        try {
            injectLanguageSwitcher();
            if (document.body) {
                translateDOM(document.body);
                startMainObserver();
                startPeriodicScan();
            }
        } catch (e) {
            console.error('[AG-ZH] Init error:', e);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

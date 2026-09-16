// Antigravity Client Modern Chinese Localization Engine v1.0.0
// Sandboxed Electron compatible with embedded dictionary and real-time DOM translation
// Supports external dictionaries from the Antigravity locales directory:
// the patcher splices them in at injection time, and when the preload has fs
// access (non-sandboxed) they are also hot-reloaded at runtime.

(function() {
    let currentLang = 'zh';
    try {
        currentLang = localStorage.getItem('antigravity_lang') || 'zh';
    } catch (e) {
        console.error('[AG-ZH] Failed to read lang preference:', e);
    }

    // ---------------------------------------------------------------------------
    // Dictionary state: embedded base (spliced in by build.py / patcher) plus
    // optional external overrides from the user-editable locales directory.
    // ---------------------------------------------------------------------------
    const EMBEDDED_TRANSLATIONS = /*AG_ZH_ZH_START*/__TRANSLATIONS_JSON__/*AG_ZH_ZH_END*/;
    const EMBEDDED_PATTERNS = /*AG_ZH_PATTERNS_START*/__PATTERNS_JSON__/*AG_ZH_PATTERNS_END*/;

    let translations = EMBEDDED_TRANSLATIONS;
    let rawPatterns = EMBEDDED_PATTERNS;
    let lowerTranslations = {};
    let patterns = [];

    function rebuildIndexes() {
        lowerTranslations = {};
        for (const key in translations) {
            lowerTranslations[key.toLowerCase()] = translations[key];
        }
        patterns = rawPatterns.map(p => ({
            regex: new RegExp(p.pattern, p.flags || 'i'),
            replace: p.replacement
        }));
    }
    rebuildIndexes();

    // ---------------------------------------------------------------------------
    // External dictionary hot loading. Only works in non-sandboxed preloads;
    // sandboxed ones silently fall back to the embedded dictionary (which the
    // patcher already merged with the external files at injection time).
    // ---------------------------------------------------------------------------
    let _fs;
    function nodeFs() {
        if (_fs !== undefined) return _fs;
        _fs = null;
        try {
            if (typeof require === 'function') _fs = require('fs');
        } catch (e) {
            _fs = null;
        }
        return _fs;
    }

    function externalLocalesDir() {
        try {
            if (typeof process === 'undefined' || !process.platform) return null;
            if (typeof require !== 'function') return null;
            const os = require('os');
            const home = os.homedir();
            if (process.platform === 'win32') {
                return (process.env.APPDATA || (home + '/AppData/Roaming')) + '/Antigravity/locales';
            }
            if (process.platform === 'darwin') {
                return home + '/Library/Application Support/Antigravity/locales';
            }
            return home + '/.config/Antigravity/locales';
        } catch (e) {
            return null;
        }
    }

    let externalStamp = null;

    function applyExternalDicts(zh, pats) {
        const merged = {};
        for (const k in EMBEDDED_TRANSLATIONS) merged[k] = EMBEDDED_TRANSLATIONS[k];
        if (zh) for (const k in zh) merged[k] = zh[k];
        translations = merged;
        rawPatterns = (pats && pats.length) ? pats : EMBEDDED_PATTERNS;
        rebuildIndexes();
    }

    function tryLoadExternalDicts() {
        const fs = nodeFs();
        const dir = externalLocalesDir();
        if (!fs || !dir) return;
        try {
            let zh = null, pats = null, stamp = '';
            try {
                const p = dir + '/zh-CN.json';
                zh = JSON.parse(fs.readFileSync(p, 'utf8'));
                stamp += String(fs.statSync(p).mtimeMs) + '|';
            } catch (e) { /* missing or unreadable */ }
            try {
                const p = dir + '/patterns.json';
                pats = JSON.parse(fs.readFileSync(p, 'utf8'));
                stamp += String(fs.statSync(p).mtimeMs);
            } catch (e) { /* missing or unreadable */ }
            if (stamp !== externalStamp) {
                externalStamp = stamp;
                applyExternalDicts(zh, pats);
            }
        } catch (e) {
            // Corrupt external dictionaries must never take the client down.
        }
    }

    // ---------------------------------------------------------------------------
    // Translation core
    // ---------------------------------------------------------------------------
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

    // Untranslated tracker. Persisting is debounced: writing the whole array to
    // localStorage on every new string is O(n^2) and floods storage with code
    // editor content on slower machines.
    const untranslatedSet = new Set();
    try {
        const existing = JSON.parse(localStorage.getItem('ag_untranslated') || '[]');
        existing.forEach(item => untranslatedSet.add(item));
    } catch (e) {}

    let persistTimer = null;
    function persistUntranslated() {
        if (persistTimer) {
            clearTimeout(persistTimer);
            persistTimer = null;
        }
        try {
            localStorage.setItem('ag_untranslated', JSON.stringify(Array.from(untranslatedSet)));
        } catch (e) {}
    }
    function schedulePersistUntranslated() {
        if (persistTimer) return;
        persistTimer = setTimeout(() => {
            persistTimer = null;
            persistUntranslated();
        }, 3000);
    }
    window.addEventListener('beforeunload', persistUntranslated);

    function recordUntranslated(str) {
        if (!str || str.length < 2 || str.length > 300) return;
        if (untranslatedSet.size >= 1000) return;
        if (/^[0-9\s:._\-/\+$,#&'"\[\]{}()\\<>=!*?|`@%]+$/.test(str)) return;
        if (/[一-鿿]/.test(str)) return;
        if (!untranslatedSet.has(str)) {
            untranslatedSet.add(str);
            schedulePersistUntranslated();
        }
    }

    function translateText(text) {
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
                const translated = translateText(val);
                if (translated !== null && val !== translated) {
                    node.setAttribute(attr, translated);
                }
            }
        }
    }

    // ---------------------------------------------------------------------------
    // Skip zones: code editors, preformatted blocks and anything editable must
    // never be rewritten - both to protect displayed code and to keep editor
    // content out of the untranslated-words capture.
    // ---------------------------------------------------------------------------
    function isSkipElement(el) {
        if (!el || el.nodeType !== 1) return false;
        const tag = el.tagName;
        if (tag === 'PRE' || tag === 'CODE' || tag === 'TEXTAREA') return true;
        if (el.isContentEditable) return true;
        const cls = el.classList;
        if (cls && (cls.contains('monaco-editor') || cls.contains('CodeMirror')
                 || cls.contains('cm-editor') || cls.contains('view-lines')
                 || cls.contains('xterm') || cls.contains('terminal'))) return true;
        return false;
    }

    function insideSkipZone(el) {
        let cur = el, depth = 0;
        while (cur && cur !== document.body && depth < 25) {
            if (isSkipElement(cur)) return true;
            cur = cur.parentElement || (cur.parentNode && cur.parentNode.host);
            depth++;
        }
        return false;
    }

    const observedRoots = new WeakSet();

    function skipSubtree(walker, node) {
        // Move the walker past `node`'s entire subtree in document order.
        walker.currentNode = node;
        let next = walker.nextSibling();
        while (next === null && walker.parentNode() !== null) {
            next = walker.nextSibling();
        }
        return next;
    }

    function translateDOM(root) {
        if (!root) return;

        if (root.nodeType === 1) {
            if (isSkipElement(root)) return;
        } else if (root.nodeType === 3 && insideSkipZone(root.parentElement)) {
            return;
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
            const translated = translateText(val);
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
                const translated = translateText(val);
                if (translated !== null && val !== translated) {
                    root.value = translated;
                }
            }
        }

        // Walk DOM Subtree
        try {
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
            let node = walker.nextNode();
            while (node) {
                if (node.nodeType === 1 && isSkipElement(node)) {
                    node = skipSubtree(walker, node);
                    continue;
                }

                if (node.shadowRoot && !observedRoots.has(node.shadowRoot)) {
                    observedRoots.add(node.shadowRoot);
                    translateDOM(node.shadowRoot);
                    observeSubtree(node.shadowRoot);
                }

                if (node.nodeType === 3) {
                    const val = node.nodeValue;
                    const translated = translateText(val);
                    if (translated !== null && val !== translated) {
                        node.nodeValue = translated;
                    }
                } else if (node.nodeType === 1) {
                    translateElementAttrs(node);
                    if (nodeIsInputButton(node)) {
                        const val = node.value;
                        const translated = translateText(val);
                        if (translated !== null && val !== translated) {
                            node.value = translated;
                        }
                    }
                }
                node = walker.nextNode();
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
            try {
                for (const mutation of mutations) {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach(n => {
                            if (n.nodeType === 1 && isSkipElement(n)) return;
                            if (n.nodeType === 3 && insideSkipZone(n.parentElement)) return;
                            translateDOM(n);
                        });
                    } else if (mutation.type === 'characterData') {
                        const node = mutation.target;
                        if (!insideSkipZone(node.parentElement)) {
                            const val = node.nodeValue;
                            const translated = translateText(val);
                            if (translated !== null && val !== translated) {
                                node.nodeValue = translated;
                            }
                        }
                    }
                }
            } finally {
                obs.observe(target, { childList: true, subtree: true, characterData: true });
            }
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
                try { tryLoadExternalDicts(); } catch (e) {}
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
            persistUntranslated();
            const list = Array.from(untranslatedSet);
            const jsonStr = JSON.stringify(list, null, 2);
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(jsonStr).then(() => {
                    showToast(`已复制 ${list.length} 条待翻译词汇到剪贴板！`);
                }).catch(() => {
                    showCopyOverlay(jsonStr, list.length);
                });
            } else {
                showCopyOverlay(jsonStr, list.length);
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

    function showCopyOverlay(text, count) {
        // Clipboard unavailable (e.g. non-secure context): surface the data in
        // a selectable box instead of only pointing at localStorage.
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.bottom = '24px';
        overlay.style.right = '24px';
        overlay.style.maxWidth = '420px';
        overlay.style.background = '#2d2f31';
        overlay.style.color = '#ffffff';
        overlay.style.padding = '12px';
        overlay.style.borderRadius = '8px';
        overlay.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
        overlay.style.zIndex = '999999';
        overlay.style.fontSize = '12px';
        overlay.style.display = 'flex';
        overlay.style.flexDirection = 'column';
        overlay.style.gap = '8px';

        const hint = document.createElement('div');
        hint.textContent = `剪贴板不可用：已捕获 ${count} 条词汇，请手动复制（Ctrl+C 后点击关闭）`;
        const box = document.createElement('textarea');
        box.value = text;
        box.style.width = '380px';
        box.style.height = '160px';
        box.style.fontSize = '11px';
        box.readOnly = true;
        const close = document.createElement('button');
        close.textContent = '关闭';
        close.style.alignSelf = 'flex-end';
        close.style.cursor = 'pointer';
        close.addEventListener('click', () => overlay.remove());
        overlay.appendChild(hint);
        overlay.appendChild(box);
        overlay.appendChild(close);
        document.body.appendChild(overlay);
        box.focus();
        box.select();
    }

    // Initialize
    function init() {
        try {
            tryLoadExternalDicts();
            if (currentLang === 'en') {
                // English mode: keep only the language switcher alive; no DOM
                // scanning, no observers, no dictionary matching.
                injectLanguageSwitcher();
                return;
            }
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

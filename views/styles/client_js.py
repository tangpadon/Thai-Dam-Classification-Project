"""Client-side JavaScript for smooth scrolling, search icon replacement, and section padding."""


def get_client_js() -> str:
    """Return the client-side JavaScript script block for dashboard interactivity."""
    return """
    <script>
    (function() {
        const parentDoc = window.parent.document;

        // 1. Replace dropdown icons with search icons (Section 1 only)
        function replaceDropdownIcons() {
            const svgs = parentDoc.querySelectorAll('.st-key-dam_select [aria-label="Open"] svg, .st-key-dam_select [data-baseweb="select"] svg, .st-key-dam_select svg');
            svgs.forEach(svg => {
                if (!svg.dataset.searchIcon) {
                    svg.dataset.searchIcon = "true";
                    svg.innerHTML = '<circle cx="11" cy="11" r="7.5" fill="none" stroke="currentColor" stroke-width="2.2"></circle><line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"></line>';
                    svg.setAttribute('viewBox', '0 0 24 24');
                    svg.style.width = '18px';
                    svg.style.height = '18px';
                    svg.style.color = '#64748b';
                }
            });
        }

        // 2. Smooth scrolling
        function findScrollableContainer(el) {
            let curr = el.parentElement;
            while (curr && curr !== parentDoc.body && curr !== parentDoc.documentElement) {
                const style = window.parent.getComputedStyle(curr);
                const overflowY = style.overflowY;
                if ((overflowY === 'auto' || overflowY === 'scroll') && curr.scrollHeight > curr.clientHeight) {
                    return curr;
                }
                curr = curr.parentElement;
            }
            return parentDoc.querySelector('[data-testid="stAppViewContainer"]') ||
                   parentDoc.querySelector('section.main') ||
                   parentDoc.querySelector('[data-testid="stMain"]') ||
                   window.parent;
        }

        function scrollToTarget(targetId) {
            const targetEl = parentDoc.getElementById(targetId);
            if (!targetEl) return;

            const scrollContainer = findScrollableContainer(targetEl);
            if (scrollContainer && scrollContainer !== window.parent && scrollContainer.scrollTo) {
                const targetRect = targetEl.getBoundingClientRect();
                const containerRect = scrollContainer.getBoundingClientRect();
                const currentScrollTop = scrollContainer.scrollTop;
                const offsetPosition = targetRect.top - containerRect.top + currentScrollTop - 70;
                scrollContainer.scrollTo({
                    top: Math.max(0, offsetPosition),
                    behavior: 'smooth'
                });
            } else {
                targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }

        function updateActiveState(clickedLink) {
            const allLinks = parentDoc.querySelectorAll('.sidebar-nav .nav-link');
            allLinks.forEach(el => {
                el.classList.remove('active');
                el.style.backgroundColor = '';
                el.style.color = '#475569';
                el.style.fontWeight = 'normal';
                const svg = el.querySelector('svg');
                if (svg) svg.style.stroke = '#475569';
            });
            clickedLink.classList.add('active');
            clickedLink.style.backgroundColor = '#e0f2fe';
            clickedLink.style.color = '#0284c7';
            clickedLink.style.fontWeight = '600';
            const activeSvg = clickedLink.querySelector('svg');
            if (activeSvg) activeSvg.style.stroke = '#0284c7';
        }

        function triggerHighlight(targetId) {
            // Do not highlight for home/top
            if (!targetId || targetId === 'section-top') return;

            let targetEl = parentDoc.getElementById(targetId);
            if (!targetEl) return;

            let highlightEl = targetEl;

            // Flashing highlight on the section title/header/about box
            highlightEl.classList.remove('section-flash');
            void highlightEl.offsetWidth; // Force reflow to restart animation
            highlightEl.classList.add('section-flash');

            // Flashing border on the container
            const container = highlightEl.closest(
                '.st-key-sec_dam_select, .st-key-sec_overview, .st-key-sec_forecast, ' +
                '.st-key-sec_trend, .st-key-sec_history, .st-key-sec_summary'
            );
            if (container) {
                container.classList.remove('container-flash');
                void container.offsetWidth; // Force reflow
                container.classList.add('container-flash');
            } else if (targetId === 'section-about') {
                highlightEl.classList.remove('container-flash');
                void highlightEl.offsetWidth;
                highlightEl.classList.add('container-flash');
            }
        }

        function autoCloseMobileSidebar() {
            if (window.parent.innerWidth <= 768) {
                // Find collapse/close button in Streamlit sidebar on mobile
                const collapseBtn = parentDoc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                                    parentDoc.querySelector('[data-testid="stSidebar"] button[kind="header"]') ||
                                    parentDoc.querySelector('button[aria-label="Close sidebar"]') ||
                                    parentDoc.querySelector('button[data-testid="baseButton-header"]');
                if (collapseBtn) {
                    setTimeout(() => {
                        collapseBtn.click();
                    }, 280);
                }
            }
        }

        function handleNavClick(e) {
            const link = e.target.closest('.sidebar-nav .nav-link');
            if (!link) return;
            e.preventDefault();
            e.stopPropagation();

            const targetId = link.getAttribute('data-target');
            if (targetId) {
                scrollToTarget(targetId);
                triggerHighlight(targetId);
                updateActiveState(link);
                autoCloseMobileSidebar();
            }
        }

        function handleNavKey(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                const link = e.target.closest('.sidebar-nav .nav-link');
                if (link) {
                    e.preventDefault();
                    handleNavClick(e);
                }
            }
        }

        if (window.parent.__sidebarNavHandler) {
            parentDoc.removeEventListener('click', window.parent.__sidebarNavHandler, true);
        }
        window.parent.__sidebarNavHandler = handleNavClick;
        parentDoc.addEventListener('click', handleNavClick, true);

        if (window.parent.__sidebarNavKeyHandler) {
            parentDoc.removeEventListener('keydown', window.parent.__sidebarNavKeyHandler, true);
        }
        window.parent.__sidebarNavKeyHandler = handleNavKey;
        parentDoc.addEventListener('keydown', handleNavKey, true);

        // 3. Guarantee section bottom padding across all sections (responsive)
        function fixSectionPadding() {
            const isMobile = window.parent.innerWidth <= 768;
            const paddingBottom = isMobile ? '22px' : '26px';
            const secKeys = [
                'st-key-sec_dam_select',
                'st-key-sec_overview',
                'st-key-sec_forecast',
                'st-key-sec_trend',
                'st-key-sec_history',
                'st-key-sec_summary'
            ];
            secKeys.forEach(k => {
                const els = parentDoc.getElementsByClassName(k);
                for (let i = 0; i < els.length; i++) {
                    els[i].style.setProperty('padding-bottom', paddingBottom, 'important');
                    els[i].style.setProperty('box-sizing', 'border-box', 'important');
                }
            });
        }

        // Run search icon replacement, section padding, and observe DOM mutations
        replaceDropdownIcons();
        fixSectionPadding();
        if (window.parent.__dropdownIconObserver) {
            window.parent.__dropdownIconObserver.disconnect();
        }
        window.parent.__dropdownIconObserver = new MutationObserver(() => {
            replaceDropdownIcons();
            fixSectionPadding();
        });
        window.parent.__dropdownIconObserver.observe(parentDoc.body, { childList: true, subtree: true });
    })();
    </script>
    """


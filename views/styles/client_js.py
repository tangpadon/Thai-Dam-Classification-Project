def get_client_js() -> str:
    return """
    <script>
    (function() {
        let parentDoc = document;
        let parentWin = window;
        try {
            if (window.parent && window.parent.document) {
                parentDoc = window.parent.document;
                parentWin = window.parent;
            }
        } catch (e) {
            parentDoc = document;
            parentWin = window;
        }

        // Smooth scrolling
        function findScrollableContainer(el) {
            let curr = el.parentElement;
            while (curr && curr !== parentDoc.body && curr !== parentDoc.documentElement) {
                const style = parentWin.getComputedStyle(curr);
                const overflowY = style.overflowY;
                if ((overflowY === 'auto' || overflowY === 'scroll') && curr.scrollHeight > curr.clientHeight) {
                    return curr;
                }
                curr = curr.parentElement;
            }
            return parentDoc.querySelector('[data-testid="stAppViewContainer"]') ||
                   parentDoc.querySelector('section.main') ||
                   parentDoc.querySelector('[data-testid="stMain"]') ||
                   parentWin;
        }

        function scrollToTarget(targetId) {
            const targetEl = parentDoc.getElementById(targetId);
            if (!targetEl) return;

            const scrollContainer = findScrollableContainer(targetEl);
            if (scrollContainer && scrollContainer !== parentWin && scrollContainer.scrollTo) {
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
            if (parentWin.innerWidth <= 768) {
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

        if (parentWin.__sidebarNavHandler) {
            parentDoc.removeEventListener('click', parentWin.__sidebarNavHandler, true);
        }
        parentWin.__sidebarNavHandler = handleNavClick;
        parentDoc.addEventListener('click', handleNavClick, true);

        if (parentWin.__sidebarNavKeyHandler) {
            parentDoc.removeEventListener('keydown', parentWin.__sidebarNavKeyHandler, true);
        }
        parentWin.__sidebarNavKeyHandler = handleNavKey;
        parentDoc.addEventListener('keydown', handleNavKey, true);

        // Equalize side-by-side section heights on desktop
        function equalizeSectionPairs() {
            const pairs = [
                ['.st-key-sec_dam_select', '.st-key-sec_overview']
            ];
            const secSummary = parentDoc.querySelector('.st-key-sec_summary');
            if (secSummary) secSummary.style.removeProperty('min-height');
            const isMobile = parentWin.innerWidth <= 768;

            pairs.forEach(([selA, selB]) => {
                const elA = parentDoc.querySelector(selA);
                const elB = parentDoc.querySelector(selB);
                if (!elA || !elB) return;

                elA.style.removeProperty('min-height');
                elB.style.removeProperty('min-height');

                if (isMobile) return;

                const hA = elA.getBoundingClientRect().height;
                const hB = elB.getBoundingClientRect().height;
                const maxH = Math.ceil(Math.max(hA, hB));
                if (maxH > 0) {
                    elA.style.setProperty('min-height', maxH + 'px', 'important');
                    elB.style.setProperty('min-height', maxH + 'px', 'important');
                }
            });
        }

        if (parentWin.__secResizeHandler) {
            parentWin.removeEventListener('resize', parentWin.__secResizeHandler);
        }
        parentWin.__secResizeHandler = equalizeSectionPairs;
        parentWin.addEventListener('resize', equalizeSectionPairs);

        equalizeSectionPairs();

        if (parentWin.__secResizeObserver) {
            parentWin.__secResizeObserver.disconnect();
        }
        if (parentWin.__dropdownIconObserver) {
            parentWin.__dropdownIconObserver.disconnect();
        }

        let resizeAnimFrame = null;
        parentWin.__secResizeObserver = new MutationObserver(() => {
            if (resizeAnimFrame) {
                cancelAnimationFrame(resizeAnimFrame);
            }
            resizeAnimFrame = requestAnimationFrame(() => {
                equalizeSectionPairs();
            });
        });

        if (parentDoc.body) {
            parentWin.__secResizeObserver.observe(parentDoc.body, { childList: true, subtree: true });
        }
    })();
    </script>
    """


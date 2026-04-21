/**
 * AIdeator Polish & Animations
 * Signature "Wow" effects for the validation report.
 */

window.AIdeatorPolish = {
    /**
     * Animate a numeric value from start to end.
     * @param {HTMLElement} element - The element to update.
     * @param {number} start - Beginning value.
     * @param {number} end - Target value.
     * @param {number} duration - Animation duration in ms.
     */
    animateValue(element, start, end, duration = 1500) {
        if (!element) return;
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            // Ease out cubic
            const easedProgress = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(easedProgress * (end - start) + start);
            element.innerText = current;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    },

    /**
     * Reveal elements with a delay.
     * @param {string} selector - CSS selector for elements to reveal.
     * @param {number} stagger - Delay between each element in ms.
     */
    revealElements(selector, stagger = 100) {
        const elements = document.querySelectorAll(selector);
        elements.forEach((el, index) => {
            setTimeout(() => {
                el.classList.add('active');
            }, index * stagger);
        });
    },

    /**
     * Initialize result card animations.
     */
    initReportAnimations() {
        // Find all score displays
        const scores = document.querySelectorAll('.animate-score');
        scores.forEach(el => {
            const target = parseInt(el.getAttribute('data-target') || '0', 10);
            this.animateValue(el, 0, target);
        });

        // Reveal cards
        this.revealElements('.reveal');
    }
};

// Auto-init if results are present on load
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.report-container')) {
        window.AIdeatorPolish.initReportAnimations();
    }
});

const AIdeatorPalette = {
    isOpen: false,
    query: '',
    selectedIndex: 0,
    commands: [
        { id: 'lab', title: 'Concept Lab', description: 'Generate and validate new ideas', path: '/', icon: 'biotech' },
        { id: 'reports', title: 'Reports Archive', description: 'Vault of synthesized intelligence', path: '/app/reports', icon: 'vault' },
        { id: 'compare', title: 'Intelligence Comparison', description: 'Side-by-side run analysis', path: '/app/compare', icon: 'compare_arrows' },
        { id: 'settings', title: 'System Settings', description: 'Configure providers and identity', path: '/settings', icon: 'settings' }
    ],

    init() {
        window.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.toggle();
            }
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    },

    toggle() {
        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            setTimeout(() => document.getElementById('palette-input')?.focus(), 50);
        }
    },

    close() {
        this.isOpen = false;
        this.query = '';
        this.selectedIndex = 0;
    },

    get filteredCommands() {
        if (!this.query) return this.commands;
        const q = this.query.toLowerCase();
        return this.commands.filter(c => 
            c.title.toLowerCase().includes(q) || 
            c.description.toLowerCase().includes(q)
        );
    },

    navigate() {
        const selected = this.filteredCommands[this.selectedIndex];
        if (selected) {
            window.location.href = selected.path;
        }
    }
};

window.AIdeatorPalette = AIdeatorPalette;
AIdeatorPalette.init();

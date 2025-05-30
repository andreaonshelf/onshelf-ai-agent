// Debug script for interface switching
// Paste this into the browser console to debug

function debugInterfaces() {
    console.log('=== DEBUGGING INTERFACE STATES ===');
    
    const interfaces = [
        'extractions-interface',
        'pipeline-interface', 
        'prompts-interface',
        'analytics-interface',
        'settings-interface'
    ];
    
    interfaces.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            const styles = window.getComputedStyle(element);
            console.log(`\n${id}:`);
            console.log(`  - Found: ✓`);
            console.log(`  - Display: ${styles.display}`);
            console.log(`  - Classes: ${element.className}`);
            console.log(`  - Has .active: ${element.classList.contains('active')}`);
            console.log(`  - Inline style: ${element.style.display || 'none'}`);
            console.log(`  - Visible: ${styles.display !== 'none'}`);
        } else {
            console.log(`\n${id}: ✗ NOT FOUND`);
        }
    });
    
    console.log('\n=== MODE BUTTONS ===');
    document.querySelectorAll('.mode-btn').forEach(btn => {
        console.log(`${btn.textContent}: ${btn.classList.contains('active') ? 'ACTIVE' : 'inactive'}`);
    });
    
    console.log('\n=== CURRENT MODE ===');
    console.log(`currentMode variable: ${typeof currentMode !== 'undefined' ? currentMode : 'undefined'}`);
}

// Function to test switching
function testSwitch(mode) {
    console.log(`\n🔄 Testing switch to ${mode}...`);
    switchMode(mode);
    setTimeout(() => {
        debugInterfaces();
    }, 500);
}

// Function to verify unique content
function verifyContent() {
    console.log('\n=== VERIFYING UNIQUE CONTENT ===');
    
    const contentChecks = {
        'extractions-interface': ['Extraction Queue', 'queue-panel', 'results-panel'],
        'pipeline-interface': ['Pipeline Studio', 'System Configuration', 'Live Monitoring'],
        'prompts-interface': ['Prompt Lab', 'Structure Agent', 'prompt-editor'],
        'analytics-interface': ['Analytics Dashboard', 'Total Extractions', 'Success Rate'],
        'settings-interface': ['Settings', 'General Settings', 'API Keys']
    };
    
    Object.entries(contentChecks).forEach(([id, keywords]) => {
        const element = document.getElementById(id);
        if (element) {
            console.log(`\n${id}:`);
            keywords.forEach(keyword => {
                const found = element.innerHTML.includes(keyword);
                console.log(`  - "${keyword}": ${found ? '✓' : '✗'}`);
            });
        }
    });
}

// Run initial debug
debugInterfaces();
console.log('\n💡 Use testSwitch("mode") to test switching');
console.log('💡 Use verifyContent() to check unique content');
console.log('💡 Modes: extractions, pipeline, prompts, analytics, settings');
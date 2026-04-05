const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const terminalScenario = [
    { text: "$ dcvpg validate --all", delay: 500, type: "cmd" },
    { text: "[INFO] Loading configuration from dcvpg.config.yaml...", delay: 800, type: "info" },
    { text: "[INFO] Found 14 contracts in ./contracts/", delay: 600, type: "info" },
    { text: "[INFO] Validating postgres_main.orders_raw...", delay: 1000, type: "info" },
    { text: "   ✓ Schema structure match", delay: 300, type: "success" },
    { text: "   ✓ Freshness SLA (last updated 4m ago)", delay: 300, type: "success" },
    { text: "   ✓ Row count (1,402,291 rows)", delay: 400, type: "success" },
    { text: "   ✗ Field 'amount' violates NULLABILITY constraint", delay: 800, type: "error" },
    { text: "      - Found 1,024 nulls (0.07%) but nullable=false", delay: 500, type: "error" },
    { text: "   ✗ Schema Drift Detected on field 'status'", delay: 600, type: "error" },
    { text: "      - Expected: string", delay: 300, type: "error" },
    { text: "      - Found: varchar(50)", delay: 300, type: "error" },
    { text: "[WARN] 1/14 contracts failed validation.", delay: 800, type: "warn" },
    { text: "[ACTION] Quarantining batch req-891f2a...", delay: 1200, type: "action" },
    { text: "[AI] Triggering Auto-Healer agent...", delay: 1500, type: "ai" },
    { text: "[AI] Analyzing schema drift on 'status'...", delay: 1200, type: "ai" },
    { text: "[AI] Action proposed: update contract 'status' type to varchar(50)", delay: 800, type: "ai" },
    { text: "[AI] Opened GitHub PR #42: 'fix: schema drift in orders_raw'", delay: 1000, type: "success" },
    { text: "$ _", delay: 0, type: "prompt" }
];

async function runTerminalAnimation() {
    const termBody = document.getElementById("term-body");
    if (!termBody) return;

    // Reset
    termBody.innerHTML = '';
    
    for (let i = 0; i < terminalScenario.length; i++) {
        const step = terminalScenario[i];
        await sleep(step.delay);
        
        // Remove trailing prompt from previous if exists
        const lastEl = termBody.lastElementChild;
        if (lastEl && lastEl.textContent === "$ _" && step.type !== "prompt") {
            termBody.removeChild(lastEl);
        }

        const div = document.createElement("div");
        div.className = "term-line " + getLineClass(step.type);
        
        // Typing effect for the first command
        if (step.type === "cmd") {
            div.textContent = "$ ";
            termBody.appendChild(div);
            
            const txt = step.text.substring(2);
            for (let j = 0; j < txt.length; j++) {
                div.textContent += txt[j];
                await sleep(50);
            }
        } else {
            div.textContent = step.text;
            termBody.appendChild(div);
        }
        
        // Auto scroll
        termBody.scrollTop = termBody.scrollHeight;
    }

    // Loop animation
    setTimeout(runTerminalAnimation, 8000);
}

function getLineClass(type) {
    switch (type) {
        case "cmd": return "c-blue";
        case "success": return "c-green";
        case "error": return "c-red";
        case "warn": return "c-yellow";
        case "action": return "c-yellow";
        case "ai": return "c-blue";
        case "prompt": return "c-muted";
        default: return "";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    runTerminalAnimation();

    // Smooth scroll
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});

function copyInstall() {
    navigator.clipboard.writeText('pip install "dcvpg[all]"')
        .then(() => {
            const btn = document.querySelector('.btn-primary');
            const originalText = `pip install "dcvpg[all]" <svg class="copy-icon" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" style="margin-left: 6px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
            btn.innerHTML = `Copied! <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" style="margin-left: 6px;"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
            setTimeout(() => {
                btn.innerHTML = originalText;
            }, 2000);
        });
}

// ChatOps Animation Logic
async function runChatOpsAnimation() {
    const aiReply = document.getElementById("ai-chat-reply");
    if (!aiReply) return;

    while (true) {
        // Reset to typing state
        aiReply.innerHTML = `
            <div class="avatar-robot">🤖</div>
            <div class="bubble typing">
                <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            </div>
        `;

        // Wait to simulate typing
        await sleep(2500);

        // Update to response
        aiReply.innerHTML = `
            <div class="avatar-robot">🤖</div>
            <div class="bubble">
                I've triggered a replay for quarantine batch <b>req-891f2a</b>.
                <br><br>
                ✓ Re-validated against updated contract<br>
                ✓ 1,402,291 rows successfully passed<br>
                ✓ Inserted into production warehouse
            </div>
        `;

        // Wait before resetting cycle
        await sleep(6000);
    }
}

// Hook up into DOMContentLoaded
// Hook up into DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
    runChatOpsAnimation();
    initThemeToggle();
    initHeroBlockchain();
});

// Night Mode Toggle Logic
function initThemeToggle() {
    const themeBtn = document.getElementById("theme-btn");
    if (!themeBtn) return;
    
    themeBtn.addEventListener("click", () => {
        const doc = document.documentElement;
        if (doc.getAttribute("data-theme") === "dark") {
            doc.removeAttribute("data-theme");
            themeBtn.textContent = "🌙";
        } else {
            doc.setAttribute("data-theme", "dark");
            themeBtn.textContent = "☀️";
        }
    });
}

// Hero Blockchain Canvas + Contributors Interaction
async function initHeroBlockchain() {
    const canvas = document.getElementById("hero-blockchain-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    
    let width = canvas.width = canvas.parentElement.offsetWidth;
    let height = canvas.height = canvas.parentElement.offsetHeight;

    window.addEventListener('resize', () => {
        width = canvas.width = canvas.parentElement.offsetWidth;
        height = canvas.height = canvas.parentElement.offsetHeight;
    });

    let contributors = [];
    try {
        const res = await fetch("https://api.github.com/repos/pasindudilshan1/dcvpg/contributors");
        if (res.ok) {
            const data = await res.json();
            // Cap at 15 to prevent canvas clutter
            contributors = data.slice(0, 15).map(c => ({
                login: c.login,
                avatar_url: c.avatar_url,
                url: c.html_url
            }));
        }
    } catch (e) {
        console.error("Failed to pull live Github contributors", e);
    }

    // Fallback if fetch fails or repo is empty
    if (contributors.length === 0) {
        contributors = [ { login: 'pasindudilshan1', avatar_url: 'https://github.com/pasindudilshan1.png', url: 'https://github.com/pasindudilshan1' } ];
    }

    const particles = [];
    
    // Spawn simple network dots
    for (let i = 0; i < 40; i++) {
        particles.push({
            x: Math.random() * width, y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.5, vy: (Math.random() - 0.5) * 0.5,
            radius: Math.random() * 2 + 1,
            isProfile: false
        });
    }

    // Spawn Contributor nodes
    contributors.forEach(c => {
        const img = new Image();
        img.src = c.avatar_url;
        particles.push({
            x: Math.random() * width, y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4,
            radius: 20, // size of avatar
            isProfile: true,
            img: img,
            url: c.url
        });
    });

    // Handle Clicks for routing to GitHub
    canvas.addEventListener('click', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        for (let p of particles) {
            if (p.isProfile) {
                const dist = Math.hypot(p.x - mouseX, p.y - mouseY);
                if (dist < p.radius) {
                    window.open(p.url, '_blank');
                    break;
                }
            }
        }
    });

    // Handle Hover for pointer cursor
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        let hoveringOverProfile = false;

        for (let p of particles) {
            if (p.isProfile && Math.hypot(p.x - mouseX, p.y - mouseY) < p.radius) {
                hoveringOverProfile = true;
                break;
            }
        }
        canvas.style.cursor = hoveringOverProfile ? "pointer" : "default";
    });

    function draw() {
        ctx.clearRect(0, 0, width, height);
        
        const isDark = document.documentElement.getAttribute("data-theme") === "dark";
        const lineColor = isDark ? "rgba(255, 255, 255," : "rgba(0, 103, 184,";

        particles.forEach((p, i) => {
            p.x += p.vx;
            p.y += p.vy;

            // Bounce off edges softly
            if (p.x < 0 || p.x > width) p.vx *= -1;
            if (p.y < 0 || p.y > height) p.vy *= -1;

            if (p.isProfile) {
                // Draw circular avatar
                ctx.save();
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2, true);
                ctx.closePath();
                ctx.clip();
                if (p.img.complete) {
                    ctx.drawImage(p.img, p.x - p.radius, p.y - p.radius, p.radius * 2, p.radius * 2);
                } else {
                    ctx.fillStyle = isDark ? "#333" : "#e1dfdd";
                    ctx.fill();
                }
                ctx.restore();
                
                // Add border to avatar
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.strokeStyle = isDark ? "#fff" : "#0067b8";
                ctx.lineWidth = 2;
                ctx.stroke();
            } else {
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = lineColor + " 0.5)";
                ctx.fill();
            }

            // Draw connection lines
            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
                const threshold = (p.isProfile || p2.isProfile) ? 120 : 80;

                if (dist < threshold) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = lineColor + " " + (1 - dist/threshold) + ")";
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        });

        requestAnimationFrame(draw);
    }
    draw();
}

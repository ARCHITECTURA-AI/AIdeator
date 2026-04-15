from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from uuid import UUID

def generate_forge_content(idea_title: str, demand_score: str, demand_summary: str, report_content: str) -> str:
    """Generate a dynamic, high-fidelity Product Ignition Manifest."""
    return f"""# 🚀 PRODUCT_IGNITION_MANIFEST: {idea_title.upper()}
    
## 🛰️ STRATEGIC_OVERVIEW
- **Intelligence_Confidence**: {demand_score}/100
- **Market_Stance**: {demand_summary}
- **Artifact_Type**: Sovereign Micro-SaaS

---

## 🏗️ TECHNICAL_ARCHITECTURE
- **Frontend**: Next.js 14+ (App Router) // Premium Glassmorphism
- **Logic**: TypeScript (Strict Mode)
- **Persistance**: SQLite via Prisma ORM
- **Styling**: Tailwind CSS + Framer Motion
- **Diagnostics**: Custom AIdeator Synthesis Hooks

---

## 🎯 CORE_FUNCTIONALITY_MATRIX (PHASE_0)
1. **Neural Landing Page**: High-conversion landing zone mirroring the AIdeator aesthetic.
2. **Primary_Flow**: {idea_title} core functional workflow.
3. **Data_Vault**: Local-first record management and export capabilities.

---

## 🗓️ 4-WEEK_MISSION_PLAN
### Week 1: Foundation & Identity
- [ ] Initialize Next.js / TypeScript environment
- [ ] Configure Tailwind design tokens and glassmorphism components
- [ ] Deploy basic IDEATION.md and project scaffolding

### Week 2: Logic & Persistence
- [ ] Implement Prisma schema for {idea_title} domain models
- [ ] Build out core API routes and business logic engines
- [ ] Stub authentication or local session management

### Week 3: UX & Immersion
- [ ] Craft the primary dashboard / interaction canvas
- [ ] Implement Framer Motion transitions for a 'Neural OS' feel
- [ ] Integrate local validation feedback loops

### Week 4: Synthesis & Launch
- [ ] Performance audit and CSS optimization
- [ ] Final 'Forge' handoff and deployment readiness check
- [ ] Generate final intelligence report for V1.0

---

## ⚡ NEXUS_FORGE_CONTEXT
{report_content[:2000]}... (Truncated for readability)
"""

def forge_concept_file(idea_title: str, demand_score: str, demand_summary: str, report_content: str, root_dir: Path | str = ".") -> str:
    """Write the dynamic concept.md file to the specified root directory."""
    content = generate_forge_content(idea_title, demand_score, demand_summary, report_content)
    file_path = Path(root_dir) / "concept.md"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return str(file_path.absolute())


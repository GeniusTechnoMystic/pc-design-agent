# PC Design Agent — Project Brief

**Status:** Design
**Created:** 2026-07-21
**Prompt:** `~/workspace/documents/AI/AgentDesign/AgentPrompts/ENG - PC Design Agent.md`
**Private repo:** `GeniusTechnoMystic/pc-design-agent`

---

## 1. Vision

An AI-powered agent that designs x86 PCs and procures parts. It maintains a traversable knowledge graph of hardware components (specs, compatibility, benchmarks, prices, Linux compatibility, ratings) and uses it to design Linux-compatible machines at optimal price/performance points, surfacing price drops and cost-saving opportunities.

## 2. Core Capabilities

### 2.1 Component Knowledge Graph
- **Specs database:** CPU, GPU, motherboard, RAM, PSU, case, cooler, storage — every SKU with full datasheet specs
- **Compatibility graph:** socket/chipset compatibility, RAM generation, PCIe lane budgeting, clearance constraints, PSU connector mapping
- **Linux compatibility layer:** pulled from linux-hardware.org, kernel driver status, firmware requirements
- **Cross-references:** actual user benchmarks, thermal reviews, noise measurements

### 2.2 Market Intelligence
- **Price tracking:** scrape NZ retailers (PBTech, Computer Lounge, Paradigm PCs, Ascent, Mighty Ape, PB Tech) + international (Newegg, Amazon AU)
- **PriceSpy / PCPartPicker integration** for NZ pricing intelligence
- **Price drop alerts:** cron-driven monitoring, surface when components hit threshold discounts
- **Trend data:** price history, availability flags, stock levels

### 2.3 Design Engine
- **Mission profile input:** workload type (gaming, AI/ML training, encode, server, homelab, office), budget, form factor, noise target, OS requirements
- **Constraint solver:** given mission + budget, generate optimal (and budget-variant) builds
- **Compatibility validation:** clearances, PSU wattage headroom, BIOS version requirements, cooler RAM clearance, GPU length vs case
- **Thermal modeling:** TDP budget, airflow path, fan curve recommendations

### 2.4 Procurement Pipeline
- **Build list generation:** parts list with alternates, prices, links, stock status
- **Price comparison across retailers** for the full build
- **Best-buy timing:** flag components that are at historical low prices vs historical averages

## 3. Architecture Sketch

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Data Ingestion  │────▶│  Knowledge Graph  │◀────│  Design Engine   │
│  (cron / MCP)    │     │  (SQLite + RAG)   │     │  (agent prompt)  │
└─────────────────┘     └──────────────────┘     └──────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Scrapers        │     │  Query Interface │     │  Build Output    │
│  - linux-hardware│     │  - parts search  │     │  - parts list    │
│  - PriceSpy      │     │  - compat check  │     │  - comparison    │
│  - PCPartPicker  │     │  - price chart   │     │  - procurement   │
│  - retailers     │     │  - build wizard  │     │  - budget var    │
└─────────────────┘     └──────────────────┘     └──────────────────┘
```

### Key Components
- **MCP Gateway backends** for data retrieval and scraping
- **SQLite-backed knowledge graph** with compatibility relationships
- **Cron jobs** for periodic price/availability updates
- **Agent persona** (`ENG - PC Design Agent.md`) as the reasoning engine
- **PriceSpy/PCPartPicker scraping** for NZ-market pricing

## 4. Data Sources

| Source | Data | Method |
|--------|------|--------|
| linux-hardware.org | Linux compatibility per device | Web scrape / API |
| PriceSpy.co.nz | NZ pricing, price history | Web scrape |
| PCPartPicker (nz) | Build compatibility, prices | Web scrape |
| Retailer sites (PBTech, CL, etc.) | Current pricing, stock | Web scrape |
| UserBenchmark / PassMark | CPU/GPU benchmarks | Web scrape |
| TechPowerUp / TPU | GPU specs, reviews | Web scrape |
| Manufacturer spec sheets | Datasheet PDFs | Direct fetch |

## 5. Implementation Phases

### Phase 1: Foundation (MVP)
- [ ] Scrape component specs into initial knowledge graph (SQLite schema)
- [ ] Define compatibility relationship tables (socket ↔ CPU, chipset ↔ RAM gen, etc.)
- [ ] Wire linux-hardware.org data source
- [ ] Build Parts Search tool — query by type, socket, budget range
- [ ] Stand up the PC Design Agent skill in Hermes (register persona)

### Phase 2: Design Engine
- [ ] Implement constraint-solver for mission-profile-driven builds
- [ ] Compatibility validation checks (clearances, VRM, PSU headroom)
- [ ] Optimal + Budget build variant generation
- [ ] Upgrade-path recommendations

### Phase 3: Market Intelligence
- [ ] NZ retailer price scraping (cron jobs)
- [ ] Price history tracking + trend visualization
- [ ] Price drop alerts
- [ ] Cross-retailer comparison for full builds

### Phase 4: Integration & Polish
- [ ] Build-to-buy pipeline (link → cart → checkout automation)
- [ ] Hermes chat interface (ask "find me a $1500 Linux-compatible gaming PC")
- [ ] Telegram/Matrix notifications for price drops
- [ ] Component review aggregation

## 6. Key Design Decisions

- **SQLite over full graph DB:** simpler to bootstrap, compatible with Hermes toolchain, can upgrade to Neo4j later if needed
- **Hermes skill as the reasoning layer:** the prompt guides component evaluation, layperson explanations, and mission-fit reasoning
- **Cron jobs for price freshness:** prices change daily, not real-time — 24h refresh is sufficient
- **NZ-first, global second:** start with NZ retailers (user is in Christchurch), then add AU/US/global

## 7. Related Projects

| Project | Relationship |
|---------|-------------|
| `PriceScraper` (Projects/PriceScraper/) | Price monitoring overlap — could merge data pipelines |
| `yt-curator` | Reference for Hermes MCP backend + cron pattern |
| `ENG - PC Design Agent.md` | Agent persona prompt — the reasoning engine for this system |

## 8. Files & Locations

| Artifact | Path |
|----------|------|
| Project brief (this file) | `~/workspace/documents/Projects/PC-Design-Agent/PC_Design_Agent_Project_Brief.md` |
| Agent persona prompt | `~/workspace/documents/AI/AgentDesign/AgentPrompts/ENG - PC Design Agent.md` |
| Project notes / scratch | `~/.hermes/projects/pc-design-agent/` |


*Landmark document. Last updated: 2026-07-21.*

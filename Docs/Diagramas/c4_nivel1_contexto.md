flowchart TD
    classDef actor fill:#08427b,stroke:#052e56,stroke-width:2px,color:#fff;
    classDef system fill:#1168bd,stroke:#0b4884,stroke-width:2px,color:#fff;
    classDef external fill:#999999,stroke:#6b6b6b,stroke-width:2px,color:#fff;

    Admin(("👤 Administrador\n(Game Master)")):::actor
    Intern(("👤 Pasante\n(Candidato)")):::actor
    DOMO["⚙️ Sistema DOMO\n(Gateway Hostil & Comando)"]:::system
    NASA[/"🚀 APIs NASA"/]:::external
    CelesTrak[/"📡 CelesTrak"/]:::external

    Admin -->|Configura trampas y lee telemetría| DOMO
    Intern -->|Consume fragmentos bajo desafíos| DOMO
    DOMO -->|Fetch asíncrono| NASA
    DOMO -->|Fetch TLE| CelesTrak
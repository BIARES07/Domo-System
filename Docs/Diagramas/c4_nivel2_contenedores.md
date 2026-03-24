flowchart TB
    classDef actor fill:#08427b,stroke:#052e56,color:#fff;
    classDef container fill:#438dd5,stroke:#2e6295,color:#fff;
    classDef database fill:#2e6295,stroke:#1f4264,color:#fff;
    classDef external fill:#999999,stroke:#6b6b6b,color:#fff;

    Admin(("👤 Admin")):::actor
    Intern(("👤 Pasante")):::actor
    NASA[/"NASA APIs"/]:::external
    CelesTrak[/"CelesTrak"/]:::external

    subgraph DOMO_System ["Límite del Sistema DOMO"]
        direction TB
        AdminUI["💻 Admin UI\n[HTML/CSS/Vanilla JS]"]:::container
        Gateway["⚙️ API Gateway\n[FastAPI - Python]"]:::container
        Redis[("⚡ Caché\n[Redis]")]:::database
        DB[("🗄️ Persistencia\n[SQLite]")]:::database
    end

    Admin --> AdminUI
    Intern --> Gateway
    AdminUI --> Gateway
    Gateway --> Redis
    Gateway --> DB
    Gateway --> NASA
    Gateway --> CelesTrak
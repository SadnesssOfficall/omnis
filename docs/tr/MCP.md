# MCP

`/omnis setup`, kimlik bilgisi istemeyen ve sürümü sabitlenmiş iki sunucuyu kurar:
- **context7** (`@upstash/context7-mcp@4.6.0`): güncel kütüphane belgelerini getirir. `documentation-lookup` skill'i buna dayanır.
- **playwright** (`@playwright/mcp@0.0.84`): tarayıcıda test yapar.

Kimlik bilgisi isteyen sunucular kurulmaz, yalnız önerilir:
- GitHub: `gh` CLI zaten kullanılıyor, ek bir MCP sunucusuna gerek yok.
- Cloudflare, Postgres, Sentry: token gerekir. Token tek bir cümleyle istenir ve `claude mcp add ... -e` ile kullanıcı yapılandırmasına yazılır. Repoya asla yazılmaz.
- planetscale (eklenti): kimlik doğrulaması bekliyor.

OMNIS'in kendi MCP sunucusu (`scripts/mcp_server.py`) başka AI araçları için. Ayrıntılar README'de.

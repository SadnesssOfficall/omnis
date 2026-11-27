# Geri alma

Her `/omnis setup` çalışması `~/.claude/omnis/backups/<ts>/` klasörüne şunları kaydeder:
- settings.json ve CLAUDE.md'nin kopyası
- `manifest.json`: oluşturulan dosyalar, eklenen MCP sunucuları ve otomasyonların listesi

## Komutlar
- `/omnis geri-al`: son kurulumu geri alır.
- `omnis rollback list`: kayıtlı kurulumları listeler.
- `omnis rollback <ts>`: seçtiğin kurulumu geri alır.

## Geri alınca ne olur
- settings.json ve CLAUDE.md yedekten geri yüklenir. Kurulumdan sonra bu iki dosyada yaptığın değişiklikler de geri gider.
- OMNIS işareti taşıyan ajan ve komut dosyaları silinir.
- Kurulumun eklediği MCP sunucuları ve zamanlanmış görevler kaldırılır.
- Senin kendi dosyalarına dokunulmaz.

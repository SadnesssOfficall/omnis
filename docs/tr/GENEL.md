# OMNIS Developer OS: genel bakış ve günlük kullanım

OMNIS, Claude Code'a uzman ajanlar, iş akışı komutları, ucuz güvenlik kancaları, MCP sunucuları ve salt-okur otomasyonlar ekler. Hiçbir dosyayı elle düzenlemen gerekmez.

## Tek komut
- `/omnis setup`: sistemi denetler, plan çıkarır, yedek alır, kurulumu yapar, doğrular ve Türkçe rapor verir. Terminalden aynı iş için `python install.py --os --yes` yazabilirsin. `--yes` olmadan çalıştırırsan yalnız deneme yapar ve hiçbir şeyi değiştirmez.
- `/omnis durum`: sağlık kontrolü yapar.
- `/omnis geri-al`: son kurulumu geri alır. Belirli bir kurulumu geri almak için `omnis rollback <ts>` yaz.

Kurulumdan sonra Claude Code'u yeniden başlat.

## Günlük kullanım
- Küçük işler (tek dosya, yazım hatası) için komut ya da ajan gerekmez. İsteğini doğrudan yaz.
- Yeni bir repoda `/project-onboard` çalıştır. Projenin yığınını tanır ve yalnız uygun skill'leri önerir.
- Özellik eklemek için `/implement <iş>`, hata ayıklamak için `/omnis-debug <hata>`, plan için `/omnis-plan <iş>` kullan.
- İşi bitirirken `/task-report` çalıştır. Görevin durumu bir checkpoint'e yazılır ve bağlam sıkıştırıldıktan sonra geri yüklenir.

## Bilerek kurulmayanlar
- `security-scan` ve `strategic-compact`: kancaları OMNIS'in kancalarıyla çakışıyor.
- `mcp-builder`: aynı skill bir eklentide zaten var.
- `security-review`, `web-perimeter-owasp-2025-audit` ve `search-first`: denetim uyarı verdi (ağ isteği ve paket kurulumu satırları). Kurmak için onay gerekiyor, `/skills-install <ad>` ile kurabilirsin. `security-review` yerleşik `/security-review` komutuyla aynı adı taşıyor, onu gölgeleyebilir.

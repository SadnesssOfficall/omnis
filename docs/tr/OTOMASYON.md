# Otomasyon

`scripts/automation.py`, görevleri Windows Görev Zamanlayıcı'da `OMNIS\<id>` adıyla çalıştırır. Claude Code'un açık olması gerekmez. Her çalışma `~/.omnis/reports/` klasörüne bir rapor yazar ve Windows bildirimi gösterir.

| Görev | Ne yapar |
|---|---|
| skill-update-check | Yönetilen skill'leri yeniden denetler ve güncellemeleri raporlar. Hiçbir şey kurmaz |
| dependency-advisories | Seçilen repolarda npm ya da pnpm audit çalıştırır ve yüksek ya da kritik açıkları sayar |
| repo-health | Değişmiş dosyaları, push edilmemiş commit'leri, son commit'in ne kadar eski olduğunu ve diff'teki gizli bilgileri raporlar |

- Aralık seçenekleri: 1, 2, 3, 5 (varsayılan), 8, 12 ya da 24 saat. Özel bir aralık için `30m` ya da `6h` gibi yazabilirsin.
- Güvenlik: görevler yalnız okur, rapor yazar ve bildirim gösterir. Silmez, dağıtmaz, push etmez, satın almaz, kimseye mesaj atmaz.
- Limit dolunca 5 saat sonra kaldığı yerden devam etme kuralı oturumun içinde zaten çalışıyor. OMNIS bunu ayrıca yapmaz.

# Güvenlik

- `guard.py` felaket komutlarını engeller, riskli komutlarda onay ister. Belirli kalıpları tanır. Emniyet kemeri gibidir, her şeyi yakalayan bir sandbox değildir.
- `.env*`, anahtar ve kilit dosyaları düzenlenmeden önce onay istenir.
- Düzenlenen dosyalarda gizli bilgi aranır. Belleğe, checkpoint'lere ve raporlara yazılan değerler maskelenir.
- Dış skill'ler sabit bir commit'ten indirilir, denetlenir ve onay verilmeden kurulmaz.
- Otomasyonlar yalnız okur. MCP sunucularının sürümleri sabittir. Token isteyen hiçbir sunucu kendiliğinden kurulmaz.

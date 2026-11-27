# Kancalar (hooks)

Bütün kancalar `scripts/os_hooks.py` içinde. Hepsi ucuzdur ve yalnız koşulu tuttuğunda çalışır. Bir kanca hata verirse oturum bozulmaz.

| Olay | Ne yapar | Ne zaman |
|---|---|---|
| PreToolUse Bash/PowerShell | `guard.py` felaket komutlarını engeller, riskli komutlarda onay ister | Her shell komutunda (bu kanca zaten vardı) |
| PreToolUse Edit/Write | `.env*`, anahtar ve kilit dosyalarına yazmadan önce onay ister | Yalnız korunan dosya adlarında |
| PostToolUse Edit/Write | Düzenlenen dosyada gizli bilgi arar. Projede prettier ya da eslint varsa onu çalıştırır | Yalnız düzenlenen dosyada |
| UserPromptSubmit | Turun başladığı zamanı kaydeder | Çıktı üretmez |
| Stop | .ts/.tsx dosyası değiştiyse `tsc --noEmit` çalıştırır. Görev uzun sürdüyse Windows bildirimi gösterir | Turu en fazla bir kez engeller. `stop_hook_active` varsa hiç engellemez |
| SessionStart | Sıkıştırma ya da resume sonrasında son checkpoint'i geri yükler. Yeni oturumda proje yığını için ipucu verir | Sonucu 12 saat önbellekte tutar |
| PreCompact | Otomatik checkpoint alır | Yalnız git deposunda |

## Kapatma
- Tek bir kancayı kapatmak için ortam değişkenine ekle: `OMNIS_HOOKS_OFF=stop,post-edit`.
- Hepsini kaldırmak için `/omnis geri-al` çalıştır ya da ilgili girdiyi settings.json'dan sil.
- Bildirim eşiğini değiştirmek için `OMNIS_TOAST_MIN=5` kullan (varsayılan 3 dakika). Bildirimleri tamamen kapatmak için `OMNIS_NO_TOAST=1` kullan.

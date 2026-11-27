# Komutlar

Komutlar `~/.claude/commands/` altına kurulur ve her dosyada `<!-- omnis-managed -->` işareti bulunur. Yerleşik ya da eklenti komutlarıyla aynı adı taşıyanlar `omnis-` önekiyle kurulur: /plan, /debug, /review ve /docs. Aynı adla senin yazdığın bir dosya varsa ona dokunulmaz.

| Komut | Ne yapar |
|---|---|
| /analyze | Bir alanı değiştirmeden önce anlar: harita, giriş noktaları, riskler |
| /omnis-plan | Her adımı doğrulanabilir bir plan çıkarır (DEEP modu) |
| /implement | İşi uçtan uca yapar: plan, düzenleme, test, doğrulama |
| /omnis-debug | Kök nedeni bulur, düzeltir, regresyon testi yazar ve hatayı belleğe kaydeder |
| /audit | Genel sağlık denetimi yapar, hiçbir şeyi değiştirmez |
| /omnis-security | Diff ya da bir alan için güvenlik incelemesi yapar (yerleşik /security-review'u tamamlar) |
| /omnis-review | Diff'i code-reviewer ajanıyla inceler |
| /test | Yalnız değişikliğin dokunduğu testleri çalıştırır |
| /optimize | Önce ölçer, sonra düzeltir, sonra yeniden ölçer |
| /refactor | Davranışı değiştirmeden kodu yeniden düzenler |
| /omnis-docs | Belgeleri gerçek koda bakarak yazar |
| /release | Sürümü hazırlar, yayınlamadan önce onay ister |
| /deploy | Onay alır, geri alma adımını yazar, sonra dağıtır |
| /cleanup | Ölü kodu ve gereksiz dosyaları listeler, onay verirsen siler |
| /research | Soruyu resmi kaynaklardan, kaynak göstererek yanıtlar |
| /project-onboard | Projenin yığınını tanır, uygun skill ve ajanları önerir |
| /task-report | Görevin durumunu raporlar ve checkpoint kaydeder |
| /skills-discover, /skills-install, /skills-update, /skills-audit, /skills-remove, /skills-list | Skill kataloğu ve kayıt defteri |
| /automation-status, /automation-add, /automation-pause, /automation-resume, /automation-remove, /automation-config, /automation-run | Otomasyon yöneticisi |

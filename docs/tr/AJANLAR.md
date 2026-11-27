# Uzman ajanlar

Ajanlar `~/.claude/agents/` altına kurulur. Bir eklentide ya da senin dosyalarında aynı adlı ajan varsa o ajan atlanır. Şu an eklentilerdeki ajanlar yalnız analyzer, comparator ve grader, yani çakışma yok.

- Salt-okur ajanlar: architect, security-auditor, code-reviewer, debugger, performance, ui-ux, research.
- Dosya düzenleyen ajanlar:
  - developer, frontend, backend, database, docs
  - qa: yalnız test dosyalarını düzenler.
  - devops: yalnız yapılandırma dosyalarını düzenler, dağıtım yapmaz.

## Kurallar
- Küçük işlerde ajan kullanılmaz.
- İki ajan aynı dosyayı düzenlemez. Her ajana ayrı bir dosya grubu verilir.
- Kod yazıldıktan sonra code-reviewer çalışır. Değişiklik kimlik doğrulama, ödeme, dosya ya da shell koduna dokunuyorsa security-auditor da çalışır.

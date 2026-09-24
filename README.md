# SMC Algorithmic Trading

واجهة ويب بـ React وExpress، إلى جانب طرفية Python مستقلة لتجارب SMC/ICT. اقرأ حالة كل مسار قبل التشغيل؛ واجهة الويب الحالية تستخدم بيانات مسح مولّدة وتنفذ الأوامر عبر محوّل ورقي.

## مكونات المشروع

| المسار | الوظيفة |
|---|---|
| `src/` | واجهة React للماسح والإشارات والمخاطر |
| `server.ts` | خادم Express وواجهات `/api/*` |
| `smc_terminal/src/api_bridge.py` | جسر JSON بين خادم الويب ومحركات Python |
| `smc_terminal/` | تطبيق Python، محركات الاستراتيجية، محوّل Binance، واختبارات الوحدة |

## التشغيل المحلي

```bash
npm install
npm run dev
```

يتطلب مسار الويب وجود Python 3.10+ ضمن `PATH` أو ضبط `PYTHON_BIN`، ويستخدم `PYTHONPATH=smc_terminal` عند استدعاء الجسر. لفحص البناء واختبارات Python:

```bash
npm run lint
npm run build
PYTHONPATH=smc_terminal python -m unittest discover -s smc_terminal/tests
```

راجع [دليل طرفية Python](smc_terminal/README.md) لإعدادها المستقل. ملفا `.env.example` يسردان أسماء متغيرات تجريبية؛ لا تضع مفاتيح حقيقية في المستودع.

## الحالة والحدود

- `api_bridge.py` ينشئ شموعًا محددة مسبقًا للماسح؛ الأسعار والإشارات المعروضة عبر هذا المسار ليست تغذية سوق حية.
- `execute_order` في جسر الويب يستخدم `PaperTradingAdapter`، بينما `BinanceSpotAdapter` مكون منفصل يوقّع طلبات منصة Binance عند استدعائه.
- خادم Express يستمع على `0.0.0.0:3000`، ولا توجد طبقة تحقق هوية في المسارات المفحوصة. شغّله داخل بيئة محلية موثوقة فقط حتى تُضاف حماية للخادم.
- ملفات `smc_terminal/terminal.db` و`__pycache__` موجودة بالفعل في تاريخ المستودع. تجاهلها لاحقًا لا يمحو نسخها السابقة؛ ينبغي مراجعة محتوى قاعدة البيانات قبل قرار إزالتها أو تنقية التاريخ.

اقرأ [شرح المصادقة والأسرار](AUTHENTICATION.md)، و[مصادر البيانات](DATA_PROVENANCE.md)، و[تدقيق المشروع](PROJECT_AUDIT.md). هذه الشيفرة مشروع تجريبي وليست ضمانًا للربحية أو تصريحًا بالتداول الحي.

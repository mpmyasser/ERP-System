const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });

    try {
        console.log('\n============= اختبار حفظ واستعادة الإعدادات =============\n');

        // الخطوة 1: الذهاب لصفحة الموظفين
        console.log('📄 الخطوة 1: تحميل صفحة الموظفين');
        await page.goto('http://127.0.0.1:5000/employees/', {
            waitUntil: 'domcontentloaded',
            timeout: 10000
        });
        await page.waitForTimeout(1000);

        // التحقق من localStorage قبل التضيق
        console.log('\n🔍 الخطوة 2: فحص localStorage قبل التضيق');
        let storage = await page.evaluate(() => {
            const keys = Object.keys(localStorage);
            const tableWidths = keys.filter(k => k.includes('table_widths'));
            return {
                totalKeys: keys.length,
                tableWidthKeys: tableWidths,
                contents: Object.fromEntries(tableWidths.map(k => [k, localStorage.getItem(k)]))
            };
        });

        console.log(`   • إجمالي المفاتيح في localStorage: ${storage.totalKeys}`);
        console.log(`   • مفاتيح أعمدة الجداول: ${storage.tableWidthKeys.join(', ') || 'لا توجد'}`);

        // الخطوة 3: البحث عن الجدول
        console.log('\n🔍 الخطوة 3: البحث عن جدول الموظفين');
        const tableExists = await page.locator('#employees-table').isVisible({ timeout: 5000 }).catch(() => false);

        if (!tableExists) {
            console.log('   ✗ الجدول غير موجود - قد تكون هناك صفحة تسجيل دخول');
            // محاولة التقاط شاشة
            await page.screenshot({ path: 'e:/test_employees_table.png' });
            console.log('   تم حفظ لقطة شاشة: e:/test_employees_table.png');
            await browser.close();
            return;
        }

        console.log('   ✓ تم العثور على الجدول\n');

        // الخطوة 4: قياس الأعمدة قبل التضيق
        console.log('📏 الخطوة 4: قياس الأعمدة الأولية');
        const initialMeasurement = await page.evaluate(() => {
            const table = document.getElementById('employees-table');
            const headers = Array.from(table.querySelectorAll('thead th'));
            return headers.map((h, idx) => ({
                index: idx,
                text: h.innerText.trim(),
                width: h.offsetWidth
            }));
        });

        console.log('   الأعمدة الأولية:');
        initialMeasurement.slice(0, 3).forEach(col => {
            console.log(`   • ${col.text}: ${col.width}px`);
        });

        // الخطوة 5: تضيق عمود الكود
        console.log('\n✂️ الخطوة 5: تضيق عمود الكود');
        const codeHeader = page.locator('#employees-table thead th:first-child');
        const resizerBox = await codeHeader.locator('.resizer').boundingBox().catch(() => null);

        if (resizerBox) {
            const startX = resizerBox.x + resizerBox.width / 2;
            const startY = resizerBox.y + resizerBox.height / 2;

            await page.mouse.move(startX, startY);
            await page.mouse.down();
            await page.mouse.move(startX - 25, startY, { steps: 5 });
            await page.mouse.up();
            await page.waitForTimeout(500);

            const afterResize = await codeHeader.evaluate(el => el.offsetWidth);
            console.log(`   ✓ عمود الكود: ${initialMeasurement[0].width}px → ${afterResize}px`);

            // الخطوة 6: فحص localStorage بعد التضيق
            console.log('\n💾 الخطوة 6: فحص localStorage بعد التضيق');
            storage = await page.evaluate(() => {
                const widthsData = localStorage.getItem('table_widths_employees-table');
                return {
                    widthsKey: 'table_widths_employees-table',
                    data: widthsData ? JSON.parse(widthsData) : null
                };
            });

            if (storage.data) {
                console.log('   ✓ تم حفظ الإعدادات في localStorage');
                console.log(`   البيانات المحفوظة: ${JSON.stringify(storage.data).substring(0, 100)}...`);
            } else {
                console.log('   ✗ لم يتم حفظ الإعدادات في localStorage');
            }

            // الخطوة 7: تحديث الصفحة واختبار الاستعادة
            console.log('\n🔄 الخطوة 7: تحديث الصفحة (F5)');
            await page.reload({ waitUntil: 'domcontentloaded' });
            await page.waitForTimeout(1000);

            console.log('\n🔍 الخطوة 8: فحص الأعمدة بعد التحديث');
            const afterReload = await page.evaluate(() => {
                const table = document.getElementById('employees-table');
                const headers = Array.from(table.querySelectorAll('thead th'));
                return headers.slice(0, 3).map((h, idx) => ({
                    index: idx,
                    text: h.innerText.trim(),
                    width: h.offsetWidth,
                    style: h.style.width
                }));
            });

            console.log('   الأعمدة بعد التحديث:');
            afterReload.forEach(col => {
                console.log(`   • ${col.text}: ${col.width}px (style: ${col.style || 'بدون'})`);
            });

            // المقارنة
            console.log('\n📊 الخطوة 9: المقارنة والنتيجة');
            const codeBeforeResize = initialMeasurement[0].width;
            const codeAfterResize = afterReload[0].width;

            if (Math.abs(codeAfterResize - codeBeforeResize) < 10) {
                // حُفظ العرض المضيق
                console.log(`   ✅ تم استعادة الإعدادات بنجاح!`);
                console.log(`   • عمود الكود: ${codeAfterResize}px (تم تضييقه بـ ${codeBeforeResize - codeAfterResize}px)`);
            } else if (codeAfterResize === initialMeasurement[0].width) {
                // عاد للحجم الأصلي
                console.log(`   ❌ الإعدادات لم تُحفظ - عاد العمود للحجم الأصلي`);
            } else {
                console.log(`   ⚠ الإعدادات غير متسقة`);
            }
        }

        // التقطة شاشة نهائية
        await page.screenshot({ path: 'e:/test_persist_final.png' });
        console.log('\n✓ تم حفظ لقطة الشاشة النهائية: e:/test_persist_final.png');

        console.log('\n===============================================\n');

    } catch (error) {
        console.error('❌ خطأ:', error.message);
    } finally {
        await browser.close();
    }
})();

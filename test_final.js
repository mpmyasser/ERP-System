const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });

    try {
        console.log('\n=== اختبار تضيق الأعمدة ===\n');

        // الانتظار قليلاً
        await page.waitForTimeout(500);

        // فتح المتصفح على صفحة الموظفين (قد نحصل على redirect للتسجيل)
        console.log('1️⃣ محاولة فتح صفحة الموظفين...');
        await page.goto('http://127.0.0.1:5000/employees/', {
            waitUntil: 'domcontentloaded',
            timeout: 15000
        });

        // التحقق من URL
        const url = page.url();
        console.log(`   الصفحة الحالية: ${url}`);

        // إذا كانت صفحة تسجيل دخول
        if (url.includes('login')) {
            console.log('   ✓ يتطلب تسجيل دخول، جاري ملء النموذج...\n');

            // محاولة ملء النموذج بطريقة آمنة
            const emailInput = await page.locator('input[type="email"]').first();
            const passwordInput = await page.locator('input[type="password"]').first();
            const submitBtn = await page.locator('button[type="submit"]').first();

            if (await emailInput.isVisible({ timeout: 5000 }).catch(() => false)) {
                await emailInput.fill('admin@test.com', { timeout: 5000 });
                await passwordInput.fill('admin', { timeout: 5000 });
                await submitBtn.click({ timeout: 5000 });

                // انتظر الانتقال
                await page.waitForNavigation({
                    waitUntil: 'domcontentloaded',
                    timeout: 10000
                }).catch(() => {});

                await page.waitForTimeout(2000);
                console.log('   ✓ تم التسجيل\n');
            }
        }

        // التحقق من وجود جدول الموظفين
        console.log('2️⃣ البحث عن جدول الموظفين...');
        const table = page.locator('#employees-table');

        if (!(await table.isVisible({ timeout: 5000 }).catch(() => false))) {
            console.log('   ✗ الجدول غير موجود\n');
            console.log('   محاولة التقاط شاشة للتشخيص...');
            await page.screenshot({ path: 'e:/test_debug.png' });
            await browser.close();
            return;
        }

        console.log('   ✓ تم العثور على الجدول\n');

        // قياس الأعمدة قبل التضيق
        console.log('3️⃣ قياس الأعمدة الأولية...');
        const headers = await page.locator('#employees-table thead th').all();

        const codeCol = headers[0];
        const nameCol = headers[1];

        const codeWidthBefore = await codeCol.evaluate(el => el.offsetWidth);
        const nameWidthBefore = await nameCol.evaluate(el => el.offsetWidth);

        console.log(`   • عمود الكود: ${codeWidthBefore}px`);
        console.log(`   • عمود الاسم: ${nameWidthBefore}px\n`);

        // تضيق عمود الكود
        console.log('4️⃣ تضيق عمود الكود...');
        const codeResizerBox = await codeCol.locator('.resizer').boundingBox();

        if (codeResizerBox) {
            const x = codeResizerBox.x + codeResizerBox.width / 2;
            const y = codeResizerBox.y + codeResizerBox.height / 2;

            // سحب لليسار 20px
            await page.mouse.move(x, y);
            await page.mouse.down();
            await page.mouse.move(x - 20, y, { steps: 5 });
            await page.mouse.up();

            await page.waitForTimeout(300);

            const codeWidthAfterCodeResize = await codeCol.evaluate(el => el.offsetWidth);
            console.log(`   ✓ عرض الكود بعد التضيق: ${codeWidthAfterCodeResize}px`);
            console.log(`   • تقليل بـ: ${codeWidthBefore - codeWidthAfterCodeResize}px\n`);

            // تضيق عمود الاسم
            console.log('5️⃣ تضيق عمود الاسم...');
            const nameResizerBox = await nameCol.locator('.resizer').boundingBox();

            if (nameResizerBox) {
                const nameX = nameResizerBox.x + nameResizerBox.width / 2;
                const nameY = nameResizerBox.y + nameResizerBox.height / 2;

                await page.mouse.move(nameX, nameY);
                await page.mouse.down();
                await page.mouse.move(nameX - 30, nameY, { steps: 5 });
                await page.mouse.up();

                await page.waitForTimeout(300);

                const nameWidthAfterResize = await nameCol.evaluate(el => el.offsetWidth);
                console.log(`   ✓ عرض الاسم بعد التضيق: ${nameWidthAfterResize}px`);
                console.log(`   • تقليل بـ: ${nameWidthBefore - nameWidthAfterResize}px\n`);
            }

            // التحقق من استقرار عمود الكود
            console.log('6️⃣ التحقق من استقرار عمود الكود...');
            const codeWidthAfter = await codeCol.evaluate(el => el.offsetWidth);

            console.log(`   العرض النهائي: ${codeWidthAfter}px`);
            console.log(`   العرض المتوقع: ${codeWidthAfterCodeResize}px`);
            console.log(`   الفرق: ${Math.abs(codeWidthAfter - codeWidthAfterCodeResize)}px\n`);

            console.log('📊 النتيجة:');
            if (Math.abs(codeWidthAfter - codeWidthAfterCodeResize) < 5) {
                console.log('   ✅ عمود الكود بقي مستقراً');
                console.log('   ✅ المشكلة تم حلها بنجاح!\n');
            } else {
                console.log('   ❌ عمود الكود تغيّر بشكل غير متوقع');
                console.log('   ❌ المشكلة لم تحل\n');
            }
        }

        await page.screenshot({ path: 'e:/test_resize_final.png' });
        console.log('✓ تم حفظ النتيجة في: e:/test_resize_final.png\n');

    } catch (error) {
        console.error('❌ خطأ:', error.message);
    } finally {
        await browser.close();
    }
})();

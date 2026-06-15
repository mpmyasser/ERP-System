const { chromium } = require('playwright');

const TARGET_URL = 'http://127.0.0.1:5000';

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });

    try {
        console.log('\n========== اختبار تضيق الأعمدة ==========\n');

        // الذهاب لصفحة تسجيل الدخول
        console.log('📝 الخطوة 1: تسجيل الدخول');
        await page.goto(`${TARGET_URL}/auth/login`, { waitUntil: 'networkidle' });

        // ملء نموذج التسجيل
        await page.fill('input[type="email"]', 'admin@test.com');
        await page.fill('input[type="password"]', 'admin');
        await page.click('button[type="submit"]');

        // انتظر حتى تنتقل للصفحة التالية
        await page.waitForNavigation({ timeout: 10000 }).catch(() => console.log('   ⚠ تحذير: انتقال الصفحة قد لم يحدث'));
        await page.waitForTimeout(2000);

        console.log('   ✓ تم الدخول بنجاح\n');

        // الذهاب لصفحة الموظفين
        console.log('📋 الخطوة 2: الذهاب لصفحة الموظفين');
        await page.goto(`${TARGET_URL}/employees/`, { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        console.log('   ✓ تم تحميل الصفحة\n');

        // التحقق من وجود الجدول
        console.log('🔍 الخطوة 3: البحث عن الجدول');
        const table = await page.locator('#employees-table').first();
        const tableExists = await table.isVisible();

        if (!tableExists) {
            console.log('   ✗ الجدول غير موجود\n');
            await browser.close();
            return;
        }

        console.log('   ✓ تم العثور على الجدول\n');

        // الحصول على رؤوس الأعمدة
        console.log('📊 الخطوة 4: قياس أعمدة الجدول');
        const headers = await page.locator('#employees-table thead th').all();
        console.log(`   ✓ عدد الأعمدة: ${headers.length}\n`);

        // قياس العرض الأولي
        const codeHeader = headers[0];
        const nameHeader = headers[1];

        const initialCodeWidth = await codeHeader.evaluate(el => el.offsetWidth);
        const initialNameWidth = await nameHeader.evaluate(el => el.offsetWidth);

        console.log('📐 الأعراض الأولية:');
        console.log(`   • عمود الكود: ${initialCodeWidth}px`);
        console.log(`   • عمود الاسم: ${initialNameWidth}px\n`);

        // تضيق عمود الكود
        console.log('✂️ الخطوة 5: تضيق عمود الكود');
        const codeResizer = await codeHeader.locator('.resizer').boundingBox();

        if (codeResizer) {
            const startX = codeResizer.x + codeResizer.width / 2;
            const startY = codeResizer.y + codeResizer.height / 2;

            await page.mouse.move(startX, startY);
            await page.mouse.down();
            await page.mouse.move(startX - 20, startY, { steps: 10 });
            await page.mouse.up();
            await page.waitForTimeout(500);

            const codeWidthAfterFirstResize = await codeHeader.evaluate(el => el.offsetWidth);
            console.log(`   ✓ عرض الكود بعد التضيق: ${codeWidthAfterFirstResize}px`);
            console.log(`   • تم التقليل بـ: ${initialCodeWidth - codeWidthAfterFirstResize}px\n`);
        }

        // تضيق عمود الاسم
        console.log('✂️ الخطوة 6: تضيق عمود الاسم');
        const nameResizer = await nameHeader.locator('.resizer').boundingBox();

        if (nameResizer) {
            const startX = nameResizer.x + nameResizer.width / 2;
            const startY = nameResizer.y + nameResizer.height / 2;

            await page.mouse.move(startX, startY);
            await page.mouse.down();
            await page.mouse.move(startX - 30, startY, { steps: 10 });
            await page.mouse.up();
            await page.waitForTimeout(500);

            const nameWidthAfterResize = await nameHeader.evaluate(el => el.offsetWidth);
            console.log(`   ✓ عرض الاسم بعد التضيق: ${nameWidthAfterResize}px`);
            console.log(`   • تم التقليل بـ: ${initialNameWidth - nameWidthAfterResize}px\n`);
        }

        // التحقق من استقرار عمود الكود
        console.log('🔬 الخطوة 7: التحقق من استقرار عمود الكود');
        const codeWidthFinal = await codeHeader.evaluate(el => el.offsetWidth);
        const codeAfterFirstResize = await codeHeader.evaluate(el => el.offsetWidth);

        console.log(`   العرض النهائي: ${codeWidthFinal}px\n`);

        // المقارنة
        console.log('📈 النتائج:');
        if (codeWidthFinal === codeAfterFirstResize) {
            console.log('   ✅ عمود الكود بقي مضيقاً - لم يعد للحجم الأصلي');
            console.log('   ✅ المشكلة تم حلها بنجاح!\n');
        } else {
            console.log(`   ❌ عمود الكود تغيّر: كان ${codeAfterFirstResize}px، أصبح ${codeWidthFinal}px`);
            console.log('   ❌ المشكلة لم تحل بعد\n');
        }

        // حفظ لقطة شاشة
        await page.screenshot({ path: 'e:/test_resize_result.png', fullPage: false });
        console.log('📸 تم حفظ لقطة الشاشة في: e:/test_resize_result.png\n');

        console.log('========================================\n');

    } catch (error) {
        console.error('❌ خطأ:', error.message);
    } finally {
        await browser.close();
    }
})();

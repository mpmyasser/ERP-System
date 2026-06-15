const { chromium } = require('playwright');

const TARGET_URL = 'http://127.0.0.1:5000';

(async () => {
    const browser = await chromium.launch({ headless: false, slowMo: 50 });
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });

    try {
        console.log('=== بدء الاختبار ===\n');

        // الخطوة 1: الذهاب للصفحة الرئيسية
        console.log('1️⃣ التنقل للصفحة الرئيسية...');
        await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1000);

        const url = page.url();
        console.log(`   الصفحة الحالية: ${url}`);

        // الخطوة 2: التحقق من تسجيل الدخول
        const loginForm = await page.locator('form').first().isVisible().catch(() => false);

        if (loginForm || url.includes('login')) {
            console.log('   ✓ يتطلب تسجيل دخول');
            console.log('   جاري تسجيل الدخول...');

            // محاولة ملء بيانات تسجيل الدخول
            try {
                await page.fill('input[type="email"], input[name="email"], input[name="username"]', 'admin@test.com', { timeout: 5000 });
                await page.fill('input[type="password"], input[name="password"]', 'admin', { timeout: 5000 });
                await page.click('button[type="submit"]', { timeout: 5000 });
                await page.waitForNavigation({ timeout: 5000 }).catch(() => {});
                await page.waitForTimeout(2000);
                console.log('   ✓ تم تسجيل الدخول');
            } catch (e) {
                console.log(`   ⚠ خطأ في تسجيل الدخول: ${e.message}`);
            }
        }

        // الخطوة 3: الذهاب لصفحة الموظفين مباشرة
        console.log('\n2️⃣ الذهاب لصفحة الموظفين...');
        await page.goto(`${TARGET_URL}/employees/`, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        // الخطوة 4: التحقق من وجود الجدول
        console.log('\n3️⃣ البحث عن الجدول...');
        const tableExists = await page.locator('table#employees-table, table.datatable, table.dataTable').first().isVisible().catch(() => false);

        if (!tableExists) {
            console.log('   ✗ لم يتم العثور على جدول الموظفين');
            console.log('\n   محتوى الصفحة:');
            const pageContent = await page.content();
            if (pageContent.includes('موظفين') || pageContent.includes('employees')) {
                console.log('   ✓ كلمة موظفين موجودة في الصفحة');
            }
            await page.screenshot({ path: 'e:/test_error.png', fullPage: true });
            await browser.close();
            return;
        }

        console.log('   ✓ تم العثور على جدول الموظفين');

        // الخطوة 5: الحصول على رؤوس الأعمدة
        console.log('\n4️⃣ تحديد الأعمدة...');
        const headers = await page.locator('table#employees-table thead th').all();
        console.log(`   ✓ عدد الأعمدة: ${headers.length}`);

        if (headers.length < 2) {
            console.log('   ✗ عدد الأعمدة أقل من 2');
            await browser.close();
            return;
        }

        // الخطوة 6: تضيق عمود الكود
        console.log('\n5️⃣ تضيق عمود الكود (الأول)...');
        const codeColHeader = headers[0];
        const initialCodeWidth = await codeColHeader.evaluate(el => el.offsetWidth);
        console.log(`   العرض الأولي: ${initialCodeWidth}px`);

        // البحث عن resizer
        const resizerVisible = await codeColHeader.locator('.resizer').isVisible().catch(() => false);
        if (resizerVisible) {
            const resizerBox = await codeColHeader.locator('.resizer').boundingBox();
            console.log(`   ✓ وجدت resizer - موقع: (${resizerBox.x}, ${resizerBox.y})`);

            // سحب الـ resizer لليسار
            const startX = resizerBox.x + resizerBox.width / 2;
            const startY = resizerBox.y + resizerBox.height / 2;
            const endX = startX - 25;

            await page.mouse.move(startX, startY);
            await page.mouse.down();
            await page.mouse.move(endX, startY, { steps: 10 });
            await page.mouse.up();

            await page.waitForTimeout(500);

            const codeWidthAfterResize = await codeColHeader.evaluate(el => el.offsetWidth);
            const reduction = initialCodeWidth - codeWidthAfterResize;

            console.log(`   العرض بعد التضيق: ${codeWidthAfterResize}px`);
            console.log(`   تقليل بمقدار: ${reduction}px`);

            if (reduction > 5) {
                console.log('   ✓ تم تضيق عمود الكود بنجاح');
            } else {
                console.log(`   ⚠ التضيق قليل جداً: ${reduction}px`);
            }
        } else {
            console.log('   ✗ لم يتم العثور على resizer');
        }

        // الخطوة 7: تضيق عمود آخر
        console.log('\n6️⃣ تضيق عمود الاسم (الثاني)...');
        const nameColHeader = headers[1];
        const initialNameWidth = await nameColHeader.evaluate(el => el.offsetWidth);
        console.log(`   العرض الأولي: ${initialNameWidth}px`);

        const nameResizerVisible = await nameColHeader.locator('.resizer').isVisible().catch(() => false);
        if (nameResizerVisible) {
            const nameResizerBox = await nameColHeader.locator('.resizer').boundingBox();
            console.log(`   ✓ وجدت resizer`);

            const startX = nameResizerBox.x + nameResizerBox.width / 2;
            const startY = nameResizerBox.y + nameResizerBox.height / 2;
            const endX = startX - 30;

            await page.mouse.move(startX, startY);
            await page.mouse.down();
            await page.mouse.move(endX, startY, { steps: 10 });
            await page.mouse.up();

            await page.waitForTimeout(500);

            const nameWidthAfterResize = await nameColHeader.evaluate(el => el.offsetWidth);
            console.log(`   العرض بعد التضيق: ${nameWidthAfterResize}px`);
            console.log(`   تقليل بمقدار: ${initialNameWidth - nameWidthAfterResize}px`);
        }

        // الخطوة 8: التحقق من استقرار عمود الكود
        console.log('\n7️⃣ التحقق من استقرار عمود الكود...');
        const codeWidthFinal = await codeColHeader.evaluate(el => el.offsetWidth);
        const codeWidthAfterResize = await codeColHeader.evaluate(el => {
            const width = el.style.width;
            return width ? parseFloat(width) : el.offsetWidth;
        });

        console.log(`   العرض النهائي: ${codeWidthFinal}px`);
        console.log(`   Width Style: ${codeWidthAfterResize}px`);

        const difference = Math.abs(codeWidthFinal - (initialCodeWidth - 25));
        console.log(`   الفرق عن الحجم المتوقع: ${difference}px`);

        if (difference < 10) {
            console.log('   ✅ النتيجة: عمود الكود بقي مضيقاً - المشكلة حُلّت!');
        } else {
            console.log(`   ❌ النتيجة: عمود الكود تغيّر بشكل غير متوقع`);
        }

        // التقطة الشاشة
        await page.screenshot({ path: 'e:/test_column_resize_success.png', fullPage: true });
        console.log('\n✓ تم حفظ لقطة الشاشة: e:/test_column_resize_success.png');

        console.log('\n=== انتهى الاختبار ===\n');

    } catch (error) {
        console.error('\n✗ خطأ غير متوقع:', error.message);
        console.error(error.stack);
    } finally {
        await browser.close();
    }
})();

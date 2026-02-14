class EgyptianNationalIDParser {
    static govMap = {
        '01': 'القاهرة', '02': 'الإسكندرية', '03': 'بورسعيد', '04': 'السويس',
        '11': 'دمياط', '12': 'الدقهلية', '13': 'الشرقية', '14': 'القليوبية',
        '15': 'كفر الشيخ', '16': 'الغربية', '17': 'المنوفية', '18': 'البحيرة',
        '19': 'الإسماعيلية', '21': 'الجيزة', '22': 'بني سويف', '23': 'الفيوم',
        '24': 'المنيا', '25': 'أسيوط', '26': 'سوهاج', '27': 'قنا',
        '28': 'أسوان', '29': 'الأقصر', '31': 'البحر الأحمر', '32': 'الوادي الجديد',
        '33': 'مطروح', '34': 'شمال سيناء', '35': 'جنوب سيناء', '88': 'خارج الجمهورية'
    };

    /**
     * استخراج تاريخ الميلاد والمحافظة من الرقم القومي
     * @param {string} nationalId - الرقم القومي (14 رقم)
     * @returns {Object|null} - {birthDate, governorate} أو null إذا كان غير صحيح
     */
    static parse(nationalId) {
        const cleaned = String(nationalId).trim().replace(/[\s\-]/g, '');
        if (!/^\d{14}$/.test(cleaned)) return null;

        const centuryDigit = parseInt(cleaned.charAt(0), 10);
        const year_2digit = parseInt(cleaned.substring(1, 3), 10);
        const month = parseInt(cleaned.substring(3, 5), 10);
        const day = parseInt(cleaned.substring(5, 7), 10);
        const govCode = cleaned.substring(7, 9);

        if (!(month >= 1 && month <= 12 && day >= 1 && day <= 31)) return null;

        let fullYear;
        if (centuryDigit === 2) fullYear = 1900 + year_2digit;
        else if (centuryDigit === 3) fullYear = 2000 + year_2digit;
        else return null;

        const birthDate = new Date(fullYear, month - 1, day);
        if (!(birthDate.getDate() === day && birthDate.getMonth() === month - 1 && birthDate.getFullYear() === fullYear)) {
            return null;
        }

        return {
            birthDate: birthDate,
            governorate: this.govMap[govCode] || ''
        };
    }

    /**
     * حساب العمر (سنين وأشهر وأيام)
     */
    static calculateAge(birthDate) {
        const today = new Date();
        let years = today.getFullYear() - birthDate.getFullYear();
        let months = today.getMonth() - birthDate.getMonth();
        let days = today.getDate() - birthDate.getDate();

        if (days < 0) {
            months--;
            const lastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
            days += lastMonth.getDate();
        }
        if (months < 0) {
            years--;
            months += 12;
        }

        return { years, months, days };
    }

    static formatAgeArabic(ageObj) {
        const parts = [];
        if (ageObj.years > 0) parts.push(ageObj.years === 1 ? 'سنة واحدة' : (ageObj.years === 2 ? 'سنتان' : (ageObj.years < 11 ? `${ageObj.years} سنوات` : `${ageObj.years} سنة`)));
        if (ageObj.months > 0) parts.push(ageObj.months === 1 ? 'شهر واحد' : (ageObj.months === 2 ? 'شهران' : (ageObj.months < 11 ? `${ageObj.months} أشهر` : `${ageObj.months} شهر`)));
        if (ageObj.days > 0 && ageObj.years === 0) parts.push(ageObj.days === 1 ? 'يوم واحد' : (ageObj.days === 2 ? 'يومان' : (ageObj.days < 11 ? `${ageObj.days} أيام` : `${ageObj.days} يوم`)));
        return parts.length > 0 ? parts.join(' و ') : 'حديث الولادة';
    }
}

window.formState = {
    nidValid: true,
    mobileValid: true,
    codeValid: true,
    updateButton: function () {
        const submitBtn = document.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = !(this.nidValid && this.mobileValid && this.codeValid);
        }
    }
};

document.addEventListener('DOMContentLoaded', function () {
    const nationalIdInput = document.getElementById('national_id');
    const dateOfBirthInput = document.getElementById('date_of_birth');
    const governorateInput = document.getElementById('governorate');
    const mobileInput = document.getElementById('mobile_number');
    const ageDisplay = document.getElementById('age-display');

    function validateLengths() {
        let nidOk = true;
        let mobileOk = true;

        // National ID Validation
        if (nationalIdInput && nationalIdInput.value.trim()) {
            const nid = nationalIdInput.value.trim();
            if (nid.length !== 14) {
                nationalIdInput.classList.add('is-invalid');
                nidOk = false;
            } else {
                nationalIdInput.classList.remove('is-invalid');
            }
        }

        // Mobile Number Validation
        if (mobileInput && mobileInput.value.trim()) {
            const mobile = mobileInput.value.trim();
            if (mobile.length !== 11) {
                mobileInput.classList.add('is-invalid');
                mobileOk = false;
            } else {
                mobileInput.classList.remove('is-invalid');
            }
        }

        window.formState.nidValid = nidOk;
        window.formState.mobileValid = mobileOk;
        window.formState.updateButton();
    }

    function updateFieldsFromNid() {
        const nationalId = nationalIdInput.value.trim();
        if (!nationalId) {
            if (ageDisplay) ageDisplay.innerHTML = '';
            validateLengths();
            return;
        }

        const data = EgyptianNationalIDParser.parse(nationalId);

        if (data) {
            const { birthDate, governorate } = data;

            // DOB
            if (dateOfBirthInput) {
                const day = String(birthDate.getDate()).padStart(2, '0');
                const month = String(birthDate.getMonth() + 1).padStart(2, '0');
                const formattedDate = `${day}/${month}/${birthDate.getFullYear()}`;
                dateOfBirthInput.value = formattedDate;
                if (dateOfBirthInput._flatpickr) dateOfBirthInput._flatpickr.setDate(formattedDate, false, 'd/m/Y');
                dateOfBirthInput.classList.add('is-valid');
                dateOfBirthInput.classList.remove('is-invalid');
            }

            // Governorate
            if (governorateInput && !governorateInput.value) {
                governorateInput.value = governorate;
            }

            // Age Display
            if (ageDisplay) {
                const age = EgyptianNationalIDParser.calculateAge(birthDate);
                const ageText = EgyptianNationalIDParser.formatAgeArabic(age);
                ageDisplay.innerHTML = `
                    <div class="alert alert-info py-2 mb-2" role="alert">
                        <i class="fas fa-info-circle me-1"></i>
                        <strong>تاريخ الميلاد:</strong> ${String(birthDate.getDate()).padStart(2, '0')}/${String(birthDate.getMonth() + 1).padStart(2, '0')}/${birthDate.getFullYear()} 
                        | <strong>المحافظة:</strong> ${governorate}
                        | <strong>العمر:</strong> ${ageText}
                    </div>
                `;
            }
            nationalIdInput.classList.add('is-valid');
            nationalIdInput.classList.remove('is-invalid');
        } else {
            if (nationalId.length === 14) {
                nationalIdInput.classList.add('is-invalid');
                if (ageDisplay) ageDisplay.innerHTML = '<div class="alert alert-danger py-2">رقم قومي غير صحيح</div>';
            }
        }
        validateLengths();
    }

    if (nationalIdInput) {
        nationalIdInput.addEventListener('input', updateFieldsFromNid);
        if (nationalIdInput.value.trim()) updateFieldsFromNid();
    }

    if (mobileInput) {
        mobileInput.addEventListener('input', validateLengths);
        if (mobileInput.value.trim()) validateLengths();
    }
});

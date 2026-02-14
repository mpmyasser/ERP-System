// Global date formatting helper
// Replaces <input type="date"> with a visible dd/mm/yyyy input while keeping
// the original input as a hidden ISO (yyyy-mm-dd) field so existing JS and
// form submissions keep working.

(function($){
    function arabicToWesternDigits(s){
        if(!s) return s;
        const ar = '٠١٢٣٤٥٦٧٨٩';
        for(let i=0;i<10;i++) s = s.replace(new RegExp(ar[i], 'g'), String(i));
        return s;
    }

    function formatDateToDDMM(iso){
        if(!iso) return '';
        // expected iso: yyyy-mm-dd
        const parts = iso.split('-');
        if(parts.length !== 3) return iso;
        return parts[2] + '/' + parts[1] + '/' + parts[0];
    }

    function parseDDMMToISO(text){
        if(!text) return '';
        text = arabicToWesternDigits(text.trim());
        const sep = text.indexOf('/') !== -1 ? '/' : (text.indexOf('-') !== -1 ? '-' : null);
        let d,m,y;
        if(sep){
            const parts = text.split(sep).map(p=>p.trim());
            if(parts.length !== 3) return null;
            d = parts[0]; m = parts[1]; y = parts[2];
        } else {
            // try DDMMYYYY
            const digits = text.replace(/[^0-9]/g,'');
            if(digits.length !== 8) return null;
            d = digits.substring(0,2); m = digits.substring(2,4); y = digits.substring(4,8);
        }
        if(d.length===1) d = '0'+d; if(m.length===1) m = '0'+m;
        // Basic validation
        const di = parseInt(d,10), mi = parseInt(m,10), yi = parseInt(y,10);
        if(isNaN(di)||isNaN(mi)||isNaN(yi)) return null;
        if(di<1||di>31||mi<1||mi>12||yi<1900||yi>2100) return null;
        return yi + '-' + (m.length===2?m:('0'+m)) + '-' + (d.length===2?d:('0'+d));
    }

    $(function(){
        $('input[type="date"]').each(function(){
            const $orig = $(this);
            if($orig.data('date-format-processed')) return;
            $orig.data('date-format-processed', true);

            // Preserve current value (ISO) and id/name
            const isoVal = $orig.val(); // yyyy-mm-dd
            const id = $orig.attr('id');
            const name = $orig.attr('name');

            // Make original a hidden field so existing JS selectors like $('#effective-date') still work
            $orig.attr('type','hidden');

            // Create visible text input
            const $wrap = $('<div class="input-group date-ui-group"></div>');
            const $icon = $('<span class="input-group-text"><i class="fas fa-calendar-alt"></i></span>');
            const $display = $('<input type="text" class="form-control date-ui" placeholder="dd/mm/yyyy">');

            // Insert after original
            $orig.after($wrap);
            $wrap.append($icon).append($display);

            // Set initial display value
            $display.val(formatDateToDDMM(isoVal));

            // On user edit, update hidden original with ISO value
            $display.on('change input blur', function(){
                const v = $(this).val();
                const iso = parseDDMMToISO(v);
                if(iso){
                    $orig.val(iso);
                    $(this).removeClass('is-invalid');
                } else if(!v){
                    $orig.val('');
                    $(this).removeClass('is-invalid');
                } else {
                    $(this).addClass('is-invalid');
                }
                // Trigger change on original for other scripts
                $orig.trigger('change');
            });

            // If other code updates the original (e.g., server-side rendering), reflect it
            $orig.on('change', function(){
                const newIso = $(this).val();
                $display.val(formatDateToDDMM(newIso));
            });
        });
    });
})(jQuery);

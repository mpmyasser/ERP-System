# Script: Replace the 7 inline bonus methods in db_manager.py with
# a lazy property + one-line compatibility wrappers (BonusService delegation).
# Uses precise string markers (verified above) to avoid encoding issues.

$path = 'core/db_manager.py'
$content = [System.IO.File]::ReadAllText($path)

# The block to replace starts at '    def add_bonus(' and ends right
# before '    def add_salary_history' (verified indices above).
$startMarker = '    def add_bonus(self, employee_id, amount, reason, date_awarded, paid_with_salary=True):'
$endMarker = '    def add_salary_history(self, employee_id, old_salary, new_salary, reason=None, notes=None, modified_by=None):'

$startIdx = $content.IndexOf($startMarker)
$endIdx = $content.IndexOf($endMarker, $startIdx)

if ($startIdx -lt 0 -or $endIdx -lt 0 -or $endIdx -le $startIdx) {
    throw "Markers not found or misordered: start=$startIdx end=$endIdx"
}

# Build the new section: property + 7 wrappers, inserted right before
# the preserved '    def add_salary_history' line (kept verbatim).
$replacement = @"
    # ===== Bonus Functions (المكافآت) =====

    @property
    def _bonus_service(self):
        """Lazy-initialized ``BonusService`` bound to this manager's session
        factory. The service is instantiated on first access and cached on the
        instance via a private attribute so subsequent calls reuse it.

        NOTE (P1-C02 slice, 2026-08-10): follows the same lazy-property +
        one-line-wrapper delegation pattern established by
        ``_audit_log_service`` and ``_penalty_service``. All public method
        signatures on ``DBManager`` remain unchanged for
        ``app/routes/bonuses.py`` / ``app/routes/interactive_api.py`` and
        other callers.
        """
        svc = getattr(self, '_bonus_service_instance', None)
        if svc is None:
            from core.services.bonus_service import BonusService
            svc = BonusService(self.Session)
            self._bonus_service_instance = svc
        return svc

    def add_bonus(self, employee_id, amount, reason, date_awarded, paid_with_salary=True):
        """Compatibility wrapper delegating to ``BonusService.add_bonus``."""
        return self._bonus_service.add_bonus(employee_id, amount, reason, date_awarded, paid_with_salary=paid_with_salary)

    def get_all_bonuses(self):
        """Compatibility wrapper delegating to ``BonusService.get_all_bonuses``."""
        return self._bonus_service.get_all_bonuses()

    def get_bonus_by_id(self, bonus_id):
        """Compatibility wrapper delegating to ``BonusService.get_bonus_by_id``."""
        return self._bonus_service.get_bonus_by_id(bonus_id)

    def get_employee_bonuses(self, employee_id):
        """Compatibility wrapper delegating to ``BonusService.get_employee_bonuses``."""
        return self._bonus_service.get_employee_bonuses(employee_id)

    def update_bonus(self, bonus_id, **kwargs):
        """Compatibility wrapper delegating to ``BonusService.update_bonus``."""
        return self._bonus_service.update_bonus(bonus_id, **kwargs)

    def delete_bonus(self, bonus_id):
        """Compatibility wrapper delegating to ``BonusService.delete_bonus``."""
        return self._bonus_service.delete_bonus(bonus_id)

    def get_bonuses_by_month(self, employee_id, month, year):
        """Compatibility wrapper delegating to ``BonusService.get_bonuses_by_month``."""
        return self._bonus_service.get_bonuses_by_month(employee_id, month, year)

    # ===== Salary History Functions (سجل تاريخ الرواتب) =====

"@ 

# Reassemble: keep everything before add_bonus, insert replacement
# (which already ends with the section-header + blank line), then
# restore add_salary_history and everything after it verbatim.
$newContent = $content.Substring(0, $startIdx) + $replacement + $content.Substring($endIdx)

# Write back as UTF-8 (no BOM) to match the file's existing encoding.
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Resolve-Path $path).Path, $newContent, $utf8NoBom)

Write-Output ("OLD_LEN=" + $content.Length + " NEW_LEN=" + $newContent.Length + " DELTA=" + ($newContent.Length - $content.Length))

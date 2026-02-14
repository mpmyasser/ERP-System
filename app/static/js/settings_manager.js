/*
 * Centralized User Settings Manager
 * =================================
 * Single key-value persistence layer for UI settings across all modules.
 * Storage order:
 * 1) in-memory cache (fast)
 * 2) localStorage mirror (instant restore on refresh)
 * 3) backend DB sync (/settings/user/preferences) for restart/update durability
 */

(function () {
    'use strict';

    const LOCAL_PREFIX = 'hr_pref:';
    const DELETE_MARKER = '__HR_DELETE__';
    const FLUSH_DELAY_MS = 600;
    const API_URL = '/settings/user/preferences';

    function readCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta && meta.content) return meta.content;
        const input = document.querySelector('input[name="csrf_token"]');
        return input ? input.value : '';
    }

    function safeParse(raw, fallback) {
        try {
            return JSON.parse(raw);
        } catch (e) {
            return fallback;
        }
    }

    class SettingsManager {
        constructor() {
            this.cache = new Map();
            this.pending = new Map();
            this.flushTimer = null;
            this.syncPromise = null;

            this._loadMirror();
            this._migrateLegacyLocalStorage();
            this.syncFromServer();

            window.addEventListener('pagehide', () => {
                this.flush(true);
            });
        }

        _normalizeKey(key) {
            return String(key || '').trim();
        }

        _localKey(key) {
            return LOCAL_PREFIX + key;
        }

        _loadMirror() {
            try {
                Object.keys(localStorage).forEach((storageKey) => {
                    if (!storageKey.startsWith(LOCAL_PREFIX)) return;
                    const key = storageKey.slice(LOCAL_PREFIX.length);
                    const value = safeParse(localStorage.getItem(storageKey), null);
                    if (value !== null) this.cache.set(key, value);
                });
            } catch (e) {
                // No-op: localStorage might be unavailable.
            }
        }

        _writeMirror(key, value) {
            try {
                localStorage.setItem(this._localKey(key), JSON.stringify(value));
            } catch (e) {
                // No-op
            }
        }

        _removeMirror(key) {
            try {
                localStorage.removeItem(this._localKey(key));
            } catch (e) {
                // No-op
            }
        }

        _emitSyncedEvent() {
            try {
                window.dispatchEvent(new CustomEvent('hr-settings-synced'));
            } catch (e) {
                // No-op
            }
        }

        _migrateLegacyLocalStorage() {
            const exactKeys = new Set([
                'employees_filters',
                'employees_bulk_settings',
                'attendance_filters',
                'attendance_bulk_settings',
                'loans_filters',
                'bonuses_filters',
                'penalties_filters',
                'permissions_filters',
                'leaves_bulk_settings',
                'bonuses_bulk_settings',
                'penalties_bulk_settings',
                'permissions_bulk_settings',
                'bulk_salaries_effective_date',
                'employees_bulk_edit_filters',
                'employees_bulk_edit_columns'
            ]);

            const prefixKeys = [
                'table_widths_',
                'dt_vis_',
                'DataTables_'
            ];

            let migrated = false;
            try {
                Object.keys(localStorage).forEach((key) => {
                    if (key.startsWith(LOCAL_PREFIX)) return;
                    const shouldMigrate = exactKeys.has(key) || prefixKeys.some(prefix => key.startsWith(prefix));
                    if (!shouldMigrate) return;

                    const raw = localStorage.getItem(key);
                    if (raw === null || raw === undefined) return;

                    let value = safeParse(raw, raw);
                    if (typeof value === 'string' && value.trim() === '') return;

                    if (!this.cache.has(key)) {
                        this.cache.set(key, value);
                        this._writeMirror(key, value);
                        this.pending.set(key, value);
                        migrated = true;
                    }
                });
            } catch (e) {
                // No-op
            }

            if (migrated) this._scheduleFlush();
        }

        getSetting(key, defaultValue = null) {
            const k = this._normalizeKey(key);
            if (!k) return defaultValue;
            return this.cache.has(k) ? this.cache.get(k) : defaultValue;
        }

        getObject(key, defaultValue = {}) {
            const value = this.getSetting(key, defaultValue);
            if (value && typeof value === 'object') return value;
            return defaultValue;
        }

        setSetting(key, value, options = {}) {
            const k = this._normalizeKey(key);
            if (!k) return Promise.resolve(false);

            this.cache.set(k, value);
            this._writeMirror(k, value);
            this.pending.set(k, value);

            if (options.immediate) {
                return this.flush();
            }
            this._scheduleFlush();
            return Promise.resolve(true);
        }

        setObject(key, value, options = {}) {
            return this.setSetting(key, value, options);
        }

        removeSetting(key, options = {}) {
            const k = this._normalizeKey(key);
            if (!k) return Promise.resolve(false);

            this.cache.delete(k);
            this._removeMirror(k);
            this.pending.set(k, DELETE_MARKER);

            if (options.immediate) {
                return this.flush();
            }
            this._scheduleFlush();
            return Promise.resolve(true);
        }

        listKeys(prefix = '') {
            const normalizedPrefix = this._normalizeKey(prefix);
            const keys = [];
            this.cache.forEach((_, key) => {
                if (!normalizedPrefix || key.startsWith(normalizedPrefix)) {
                    keys.push(key);
                }
            });
            return keys;
        }

        getByPrefix(prefix) {
            const normalizedPrefix = this._normalizeKey(prefix);
            const out = {};
            this.cache.forEach((value, key) => {
                if (!normalizedPrefix || key.startsWith(normalizedPrefix)) {
                    out[key] = value;
                }
            });
            return out;
        }

        clearByPrefix(prefix, options = {}) {
            const keys = this.listKeys(prefix);
            keys.forEach((key) => {
                this.cache.delete(key);
                this._removeMirror(key);
                this.pending.set(key, DELETE_MARKER);
            });
            if (options.immediate) {
                return this.flush();
            }
            this._scheduleFlush();
            return Promise.resolve(true);
        }

        _scheduleFlush() {
            if (this.flushTimer) clearTimeout(this.flushTimer);
            this.flushTimer = setTimeout(() => this.flush(), FLUSH_DELAY_MS);
        }

        async flush(forceKeepAlive = false) {
            if (this.pending.size === 0) return true;
            if (this.syncPromise) return this.syncPromise;

            const settings = {};
            const removeKeys = [];

            this.pending.forEach((value, key) => {
                if (value === DELETE_MARKER) removeKeys.push(key);
                else settings[key] = value;
            });

            this.pending.clear();
            if (this.flushTimer) {
                clearTimeout(this.flushTimer);
                this.flushTimer = null;
            }

            const payload = { settings: settings, remove_keys: removeKeys };
            const csrf = readCsrfToken();

            this.syncPromise = fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf
                },
                credentials: 'same-origin',
                keepalive: !!forceKeepAlive,
                body: JSON.stringify(payload)
            }).then((res) => {
                if (!res.ok) throw new Error('Failed to persist settings');
                return res.json();
            }).then(() => {
                this.syncPromise = null;
                return true;
            }).catch(() => {
                // Re-queue on failure to avoid data loss
                Object.keys(settings).forEach((key) => this.pending.set(key, settings[key]));
                removeKeys.forEach((key) => this.pending.set(key, DELETE_MARKER));
                this.syncPromise = null;
                return false;
            });

            return this.syncPromise;
        }

        async syncFromServer(prefix = '') {
            const query = prefix ? ('?prefix=' + encodeURIComponent(prefix)) : '';
            try {
                const res = await fetch(API_URL + query, { credentials: 'same-origin' });
                if (!res.ok) return;
                const data = await res.json();
                if (!data || !data.success || !data.settings) return;

                Object.keys(data.settings).forEach((key) => {
                    if (this.pending.has(key)) return;
                    const value = data.settings[key];
                    this.cache.set(key, value);
                    this._writeMirror(key, value);
                });
                this._emitSyncedEvent();
            } catch (e) {
                // No-op
            }
        }
    }

    const manager = new SettingsManager();

    window.HRSettingsManager = manager;
    window.HRSettingsUtil = {
        get: function (key, defaultValue = null) {
            return manager.getSetting(key, defaultValue);
        },
        getObject: function (key, defaultValue = {}) {
            return manager.getObject(key, defaultValue);
        },
        set: function (key, value, options = {}) {
            return manager.setSetting(key, value, options);
        },
        setObject: function (key, value, options = {}) {
            return manager.setObject(key, value, options);
        },
        remove: function (key, options = {}) {
            return manager.removeSetting(key, options);
        },
        listKeys: function (prefix = '') {
            return manager.listKeys(prefix);
        },
        getByPrefix: function (prefix = '') {
            return manager.getByPrefix(prefix);
        },
        clearByPrefix: function (prefix = '', options = {}) {
            return manager.clearByPrefix(prefix, options);
        },
        flush: function () {
            return manager.flush();
        },
        syncFromServer: function (prefix = '') {
            return manager.syncFromServer(prefix);
        }
    };
})();

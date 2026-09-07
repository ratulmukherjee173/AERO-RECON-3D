export function safeGetStorage(key: string, isSession: boolean = false): string | null {
  try {
    const storage = isSession ? window.sessionStorage : window.localStorage;
    return storage.getItem(key);
  } catch (e) {
    console.warn(`[Storage] Failed to get ${key}:`, e);
    return null;
  }
}

export function safeSetStorage(key: string, value: string, isSession: boolean = false): void {
  try {
    const storage = isSession ? window.sessionStorage : window.localStorage;
    storage.setItem(key, value);
  } catch (e) {
    console.warn(`[Storage] Failed to set ${key}:`, e);
  }
}

export function safeRemoveStorage(key: string, isSession: boolean = false): void {
  try {
    const storage = isSession ? window.sessionStorage : window.localStorage;
    storage.removeItem(key);
  } catch (e) {
    console.warn(`[Storage] Failed to remove ${key}:`, e);
  }
}

/**
 * Key Management Service
 * Handles RSA key generation, storage, and retrieval using Session Storage
 */

const PRIVATE_KEY_SESSION_KEY = 'trace_private_key';
const PUBLIC_KEY_SESSION_KEY = 'trace_public_key';

export interface KeyPair {
  privateKey: string | null;
  publicKey: string | null;
}

/**
 * Store private key in session storage
 */
export const setPrivateKey = (keyContent: string): void => {
  try {
    sessionStorage.setItem(PRIVATE_KEY_SESSION_KEY, keyContent);
  } catch (error) {
    console.error('Failed to store private key:', error);
    throw new Error('Failed to store private key in session storage');
  }
};

/**
 * Store public key in session storage
 */
export const setPublicKey = (keyContent: string): void => {
  try {
    sessionStorage.setItem(PUBLIC_KEY_SESSION_KEY, keyContent);
  } catch (error) {
    console.error('Failed to store public key:', error);
    throw new Error('Failed to store public key in session storage');
  }
};

/**
 * Get private key from session storage
 */
export const getPrivateKey = (): string | null => {
  try {
    return sessionStorage.getItem(PRIVATE_KEY_SESSION_KEY);
  } catch (error) {
    console.error('Failed to retrieve private key:', error);
    return null;
  }
};

/**
 * Get public key from session storage
 */
export const getPublicKey = (): string | null => {
  try {
    return sessionStorage.getItem(PUBLIC_KEY_SESSION_KEY);
  } catch (error) {
    console.error('Failed to retrieve public key:', error);
    return null;
  }
};

/**
 * Get both keys from session storage
 */
export const getKeyPair = (): KeyPair => {
  return {
    privateKey: getPrivateKey(),
    publicKey: getPublicKey(),
  };
};

/**
 * Check if private key exists in session storage
 */
export const hasPrivateKey = (): boolean => {
  return getPrivateKey() !== null;
};

/**
 * Check if public key exists in session storage
 */
export const hasPublicKey = (): boolean => {
  return getPublicKey() !== null;
};

/**
 * Check if both keys exist in session storage
 */
export const hasKeyPair = (): boolean => {
  return hasPrivateKey() && hasPublicKey();
};

/**
 * Clear private key from session storage
 */
export const clearPrivateKey = (): void => {
  try {
    sessionStorage.removeItem(PRIVATE_KEY_SESSION_KEY);
  } catch (error) {
    console.error('Failed to clear private key:', error);
  }
};

/**
 * Clear public key from session storage
 */
export const clearPublicKey = (): void => {
  try {
    sessionStorage.removeItem(PUBLIC_KEY_SESSION_KEY);
  } catch (error) {
    console.error('Failed to clear public key:', error);
  }
};

/**
 * Clear both keys from session storage
 */
export const clearKeys = (): void => {
  clearPrivateKey();
  clearPublicKey();
};

/**
 * Validate PEM format (basic check)
 */
export const validatePEMFormat = (content: string, keyType: 'private' | 'public'): boolean => {
  const trimmed = content.trim();

  if (keyType === 'private') {
    return (
      trimmed.includes('BEGIN RSA PRIVATE KEY') ||
      trimmed.includes('BEGIN PRIVATE KEY')
    ) && (
      trimmed.includes('END RSA PRIVATE KEY') ||
      trimmed.includes('END PRIVATE KEY')
    );
  } else {
    return (
      trimmed.includes('BEGIN PUBLIC KEY') ||
      trimmed.includes('BEGIN RSA PUBLIC KEY')
    ) && (
      trimmed.includes('END PUBLIC KEY') ||
      trimmed.includes('END RSA PUBLIC KEY')
    );
  }
};

/**
 * Calculate SHA256 fingerprint of key (first 16 chars for display)
 */
export const getKeyFingerprint = async (keyContent: string): Promise<string> => {
  try {
    const encoder = new TextEncoder();
    const data = encoder.encode(keyContent);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex.substring(0, 16).toUpperCase();
  } catch (error) {
    console.error('Failed to calculate fingerprint:', error);
    return 'UNKNOWN';
  }
};

/**
 * Read file as text
 */
export const readFileAsText = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      if (e.target?.result) {
        resolve(e.target.result as string);
      } else {
        reject(new Error('Failed to read file'));
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
};

/**
 * Download key as file
 */
export const downloadKey = (keyContent: string, filename: string): void => {
  const blob = new Blob([keyContent], { type: 'text/plain' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};


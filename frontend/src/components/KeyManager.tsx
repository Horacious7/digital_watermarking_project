import React, { useState, useEffect, useRef } from 'react';
import './KeyManager.css';
import toast from 'react-hot-toast';
import {
  getPrivateKey,
  getPublicKey,
  setPrivateKey,
  setPublicKey,
  clearKeys,
  clearPrivateKey,
  clearPublicKey,
  hasPrivateKey,
  hasPublicKey,
  validatePEMFormat,
  readFileAsText,
  getKeyFingerprint,
  downloadKey,
} from '../services/keyManager';
import { KeyIcon, KeyAltIcon, UnlockIcon, UnlockAltIcon, LockAltIcon, CheckIcon, XMarkIcon, AttentionIcon, FingerprintIcon, TrashIcon } from './Icons';

const API_BASE_URL = 'http://localhost:5000/api';

interface KeyManagerProps {
  requirePrivateKey?: boolean;
  requirePublicKey?: boolean;
  onKeysChanged?: () => void;
}

const KeyManager: React.FC<KeyManagerProps> = ({
  requirePrivateKey = false,
  requirePublicKey = false,
  onKeysChanged,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [privateKeyLoaded, setPrivateKeyLoaded] = useState<boolean>(false);
  const [publicKeyLoaded, setPublicKeyLoaded] = useState<boolean>(false);
  const [privateKeyFingerprint, setPrivateKeyFingerprint] = useState<string>('');
  const [publicKeyFingerprint, setPublicKeyFingerprint] = useState<string>('');
  const [generating, setGenerating] = useState<boolean>(false);

  const privateKeyInputRef = useRef<HTMLInputElement>(null);
  const publicKeyInputRef = useRef<HTMLInputElement>(null);

  // Check for existing keys on mount
  useEffect(() => {
    checkKeys();
  }, []);

  const checkKeys = async () => {
    const hasPriv = hasPrivateKey();
    const hasPub = hasPublicKey();

    setPrivateKeyLoaded(hasPriv);
    setPublicKeyLoaded(hasPub);

    // Calculate fingerprints
    if (hasPriv) {
      const privKey = getPrivateKey();
      if (privKey) {
        const fingerprint = await getKeyFingerprint(privKey);
        setPrivateKeyFingerprint(fingerprint);
      }
    }

    if (hasPub) {
      const pubKey = getPublicKey();
      if (pubKey) {
        const fingerprint = await getKeyFingerprint(pubKey);
        setPublicKeyFingerprint(fingerprint);
      }
    }
  };

  const handleGenerateKeys = async () => {
    setGenerating(true);
    const loadingToast = toast.loading('Generating RSA key pair...');

    try {
      const response = await fetch(`${API_BASE_URL}/keys/generate`, {
        method: 'POST',
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'trace_rsa_keys.zip';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        toast.success('RSA key pair generated! ZIP file downloaded. Please upload the keys below.', {
          id: loadingToast,
          duration: 5000,
        });
      } else {
        const errorData = await response.json();
        toast.error(errorData.error || 'Failed to generate keys', {
          id: loadingToast,
        });
      }
    } catch (error) {
      console.error('Key generation error:', error);
      toast.error('Network error: Could not connect to server', {
        id: loadingToast,
      });
    } finally {
      setGenerating(false);
    }
  };

  const handlePrivateKeyUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const content = await readFileAsText(file);

      // Validate format
      if (!validatePEMFormat(content, 'private')) {
        toast.error('Invalid private key format. Expected PEM format.');
        return;
      }

      // Store in session storage
      setPrivateKey(content);

      // Update UI
      setPrivateKeyLoaded(true);
      const fingerprint = await getKeyFingerprint(content);
      setPrivateKeyFingerprint(fingerprint);

      toast.success('Private key loaded successfully!');
      onKeysChanged?.();
    } catch (error) {
      console.error('Error loading private key:', error);
      toast.error('Failed to load private key');
    }

    // Reset input
    if (privateKeyInputRef.current) {
      privateKeyInputRef.current.value = '';
    }
  };

  const handlePublicKeyUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const content = await readFileAsText(file);

      // Validate format
      if (!validatePEMFormat(content, 'public')) {
        toast.error('Invalid public key format. Expected PEM format.');
        return;
      }

      // Store in session storage
      setPublicKey(content);

      // Update UI
      setPublicKeyLoaded(true);
      const fingerprint = await getKeyFingerprint(content);
      setPublicKeyFingerprint(fingerprint);

      toast.success('Public key loaded successfully!');
      onKeysChanged?.();
    } catch (error) {
      console.error('Error loading public key:', error);
      toast.error('Failed to load public key');
    }

    // Reset input
    if (publicKeyInputRef.current) {
      publicKeyInputRef.current.value = '';
    }
  };

  const handleClearKeys = () => {
    clearKeys();
    setPrivateKeyLoaded(false);
    setPublicKeyLoaded(false);
    setPrivateKeyFingerprint('');
    setPublicKeyFingerprint('');
    toast.success('Keys cleared from session');
    onKeysChanged?.();
  };

  const handleDeletePrivateKey = () => {
    clearPrivateKey();
    setPrivateKeyLoaded(false);
    setPrivateKeyFingerprint('');
    toast.success('Private key removed');
    onKeysChanged?.();
  };

  const handleDeletePublicKey = () => {
    clearPublicKey();
    setPublicKeyLoaded(false);
    setPublicKeyFingerprint('');
    toast.success('Public key removed');
    onKeysChanged?.();
  };

  const handleDownloadPrivateKey = () => {
    const key = getPrivateKey();
    if (key) {
      downloadKey(key, 'private.pem');
      toast.success('Private key downloaded');
    }
  };

  const handleDownloadPublicKey = () => {
    const key = getPublicKey();
    if (key) {
      downloadKey(key, 'public.pem');
      toast.success('Public key downloaded');
    }
  };

  const showWarning = requirePrivateKey && !privateKeyLoaded;
  const showPublicWarning = requirePublicKey && !publicKeyLoaded;

  return (
    <div className="key-manager">
      <div className="key-manager-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="key-manager-title">
          <KeyAltIcon size={20} />
          <span>Cryptographic Key Management</span>
          {(privateKeyLoaded && publicKeyLoaded) ? (
            <span className="key-status-badge complete">
              <CheckIcon size={14} /> Keys Loaded
            </span>
          ) : (privateKeyLoaded || publicKeyLoaded) ? (
            <span className="key-status-badge partial">
              <AttentionIcon size={14} /> 1/2 Keys Loaded
            </span>
          ) : (
            <span className="key-status-badge empty">
              <XMarkIcon size={14} /> No Keys Loaded
            </span>
          )}
        </div>
        <button className="expand-toggle" type="button">
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>

      {isExpanded && (
        <div className="key-manager-content">
          <div className="key-manager-info">
            <div className="info-alert">
              <AttentionIcon size={18} />
              <div>
                <strong>Session Storage:</strong> Keys are stored in your browser session only.
                They will be cleared when you close this tab.
              </div>
            </div>
          </div>

          {(showWarning || showPublicWarning) && (
            <div className="key-warning">
              <XMarkIcon size={18} />
              <span>
                {showWarning && 'Private key required for signing. '}
                {showPublicWarning && 'Public key required for verification. '}
                Please upload or generate keys below.
              </span>
            </div>
          )}

          <div className="key-actions">
            <button
              className="btn-generate-keys"
              onClick={handleGenerateKeys}
              disabled={generating}
            >
              <FingerprintIcon size={18} />
              {generating ? 'Generating...' : 'Generate New Key Pair'}
            </button>

            {(privateKeyLoaded || publicKeyLoaded) && (
              <button
                className="btn-clear-keys"
                onClick={handleClearKeys}
              >
                <XMarkIcon size={18} />
                Clear All Keys
              </button>
            )}
          </div>

          <div className="key-upload-section">
            <div className="key-upload-item">
              <div className="key-upload-header">
                <LockAltIcon size={18} />
                <span>Private Key</span>
                {privateKeyLoaded && (
                  <span className="key-loaded-indicator">
                    <CheckIcon size={14} /> Loaded
                  </span>
                )}
              </div>

              {privateKeyLoaded ? (
                <div className="key-info">
                  <div className="key-fingerprint">
                    <strong>Fingerprint:</strong> {privateKeyFingerprint}
                  </div>
                  <div className="key-actions-inline">
                    <button
                      className="btn-download-key"
                      onClick={handleDownloadPrivateKey}
                    >
                      Download Private Key
                    </button>
                    <button
                      className="btn-delete-key"
                      onClick={handleDeletePrivateKey}
                      title="Remove private key"
                    >
                      <TrashIcon size={16} />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="key-upload-control">
                  <input
                    type="file"
                    ref={privateKeyInputRef}
                    onChange={handlePrivateKeyUpload}
                    accept=".pem"
                    style={{ display: 'none' }}
                  />
                  <button
                    className="btn-upload-key"
                    onClick={() => privateKeyInputRef.current?.click()}
                  >
                    Upload Private Key (.pem)
                  </button>
                </div>
              )}
            </div>

            <div className="key-upload-item">
              <div className="key-upload-header">
                <UnlockAltIcon size={18} />
                <span>Public Key</span>
                {publicKeyLoaded && (
                  <span className="key-loaded-indicator">
                    <CheckIcon size={14} /> Loaded
                  </span>
                )}
              </div>

              {publicKeyLoaded ? (
                <div className="key-info">
                  <div className="key-fingerprint">
                    <strong>Fingerprint:</strong> {publicKeyFingerprint}
                  </div>
                  <div className="key-actions-inline">
                    <button
                      className="btn-download-key"
                      onClick={handleDownloadPublicKey}
                    >
                      Download Public Key
                    </button>
                    <button
                      className="btn-delete-key"
                      onClick={handleDeletePublicKey}
                      title="Remove public key"
                    >
                      <TrashIcon size={16} />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="key-upload-control">
                  <input
                    type="file"
                    ref={publicKeyInputRef}
                    onChange={handlePublicKeyUpload}
                    accept=".pem"
                    style={{ display: 'none' }}
                  />
                  <button
                    className="btn-upload-key"
                    onClick={() => publicKeyInputRef.current?.click()}
                  >
                    Upload Public Key (.pem)
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="key-help-text">
            <p>
              <strong>First time?</strong> Click "Generate New Key Pair" to create and download
              new RSA keys, then upload them above.
            </p>
            <p>
              <strong>Note:</strong> Keep your private key secure. Anyone with access to it can
              sign watermarks as you.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default KeyManager;


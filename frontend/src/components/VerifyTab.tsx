import React, { useState, useRef } from 'react';
import './VerifyTab.css';

const API_BASE_URL = 'http://localhost:5000/api';

interface VerifyResult {
  message: string;
  valid: boolean;
  signature_length: number;
  error?: string;
}

const VerifyTab: React.FC = () => {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [blockSize, setBlockSize] = useState<number>(8);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedImage(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError('');
    setResult(null);
  };

  const handleVerify = async () => {
    if (!selectedImage) {
      setError('Please select an image');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image', selectedImage);
      formData.append('block_size', blockSize.toString());

      const response = await fetch(`${API_BASE_URL}/verify`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
      } else {
        setError(data.error || 'Failed to verify watermark');
      }
    } catch (err) {
      setError('Network error: Could not connect to server. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="verify-tab">
      <div className="upload-section">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleImageSelect}
          accept="image/png,image/jpeg,image/jpg,image/bmp"
          style={{ display: 'none' }}
        />
        <button
          className="btn-primary"
          onClick={() => fileInputRef.current?.click()}
        >
          📁 Select Watermarked Image
        </button>
        {selectedImage && <span className="filename">{selectedImage.name}</span>}
      </div>

      {previewUrl && (
        <div className="preview-section">
          <img src={previewUrl} alt="Preview" className="image-preview" />
        </div>
      )}

      <div className="input-section">
        <label>
          <strong>Block Size:</strong>
          <div className="block-size-control">
            <input
              type="range"
              min="2"
              max="64"
              value={blockSize}
              onChange={(e) => setBlockSize(parseInt(e.target.value))}
              className="slider"
            />
            <span className="block-size-value">{blockSize}</span>
          </div>
          <small>Use the same block size that was used for embedding</small>
        </label>
      </div>

      <button
        className="btn-verify"
        onClick={handleVerify}
        disabled={loading || !selectedImage}
      >
        {loading ? '⏳ Verifying...' : '🔍 Extract & Verify Watermark'}
      </button>

      {error && <div className="status-error">❌ {error}</div>}

      {result && (
        <div className={`result-section ${result.valid ? 'valid' : 'invalid'}`}>
          <div className="result-header">
            <h2>{result.valid ? '✅ Signature Valid' : '❌ Signature Invalid'}</h2>
          </div>

          <div className="result-content">
            <div className="result-field">
              <label>Extracted Message:</label>
              <div className="message-display">{result.message || '(empty)'}</div>
            </div>

            <div className="result-field">
              <label>Signature Status:</label>
              <div className={`signature-status ${result.valid ? 'valid' : 'invalid'}`}>
                {result.valid ? (
                  <>
                    <span className="icon">🔒</span>
                    <span>Cryptographically verified - message is authentic</span>
                  </>
                ) : (
                  <>
                    <span className="icon">⚠️</span>
                    <span>Verification failed - message may be tampered</span>
                  </>
                )}
              </div>
            </div>

            <div className="result-field">
              <label>Signature Length:</label>
              <div>{result.signature_length} bytes</div>
            </div>
          </div>

          {result.valid && (
            <div className="info-box">
              <p><strong>ℹ️ What does this mean?</strong></p>
              <p>The digital signature has been successfully verified using the public key.
                 This proves that the watermark was created by someone with access to the private key
                 and the message has not been altered since embedding.</p>
            </div>
          )}

          {!result.valid && (
            <div className="warning-box">
              <p><strong>⚠️ Warning</strong></p>
              <p>The signature verification failed. This could mean:</p>
              <ul>
                <li>The image has been modified after watermarking</li>
                <li>The image was compressed (JPEG, WhatsApp, Facebook, etc.)</li>
                <li>The wrong block size was used for extraction</li>
                <li>This image was not watermarked with this system</li>
              </ul>
              <p className="info-note">
                <strong>ℹ️ Note:</strong> This watermarking system is designed for lossless formats (PNG).
                Compression algorithms (JPEG, WebP) or social media platforms (WhatsApp, Facebook, Instagram)
                will modify the DCT coefficients, making the signature verification fail even though
                the message can still be extracted.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VerifyTab;


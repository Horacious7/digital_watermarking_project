import React, { useState, useRef, useEffect } from 'react';
import './VerifyTab.css';
import toast from 'react-hot-toast';

const API_BASE_URL = 'http://localhost:5000/api';

interface VerifyResult {
  filename?: string;
  message: string;
  valid: boolean;
  signature_length: number;
  block_size: number;
  error?: string;
  success?: boolean;
}

interface BatchResult {
  results: VerifyResult[];
  summary: {
    total: number;
    successful: number;
    valid_signatures: number;
  };
}

const VerifyTab: React.FC = () => {
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [currentImageIndex, setCurrentImageIndex] = useState<number>(0);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [batchResults, setBatchResults] = useState<BatchResult | null>(null);
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    setSelectedImages(files);
    setCurrentImageIndex(0);

    // Create preview URLs for all images
    const urls = files.map(file => URL.createObjectURL(file));
    setPreviewUrls(urls);

    setError('');
    setResult(null);
    setBatchResults(null);
  };

  // Navigate to previous image
  const handlePrevImage = () => {
    if (currentImageIndex > 0) {
      setCurrentImageIndex(currentImageIndex - 1);
    }
  };

  // Navigate to next image
  const handleNextImage = () => {
    if (currentImageIndex < selectedImages.length - 1) {
      setCurrentImageIndex(currentImageIndex + 1);
    }
  };

  // Navigate to specific image by index
  const handleSelectImage = (index: number) => {
    setCurrentImageIndex(index);
  };

  // Cleanup preview URLs on unmount
  useEffect(() => {
    return () => {
      previewUrls.forEach(url => URL.revokeObjectURL(url));
    };
  }, [previewUrls]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (selectedImages.length <= 1) return;

      if (e.key === 'ArrowLeft') {
        handlePrevImage();
      } else if (e.key === 'ArrowRight') {
        handleNextImage();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentImageIndex, selectedImages.length]);

  const handleVerify = async () => {
    if (selectedImages.length === 0) {
      toast.error('Please select image(s) to verify');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    setBatchResults(null);

    const isBatch = selectedImages.length > 1;
    const loadingToast = toast.loading(
      isBatch
        ? `Verifying ${selectedImages.length} images...`
        : 'Verifying watermark...'
    );

    try {
      const formData = new FormData();

      if (isBatch) {
        // Batch verification
        selectedImages.forEach(img => {
          formData.append('images', img);
        });

        const response = await fetch(`${API_BASE_URL}/verify/batch`, {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();

        if (response.ok) {
          setBatchResults(data);
          const validCount = data.results.filter((r: any) => r.valid).length;
          toast.success(
            `✅ Verified ${selectedImages.length} images: ${validCount} valid, ${selectedImages.length - validCount} invalid`,
            { id: loadingToast, duration: 5000 }
          );
        } else {
          const errorMsg = data.error || 'Failed to verify watermarks';
          toast.error(errorMsg, { id: loadingToast });
          setError(errorMsg);
        }
      } else {
        // Single image verification
        formData.append('image', selectedImages[0]);

        const response = await fetch(`${API_BASE_URL}/verify`, {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();

        if (response.ok) {
          setResult(data);
          if (data.valid) {
            toast.success('✅ Signature verified! Watermark is authentic.', {
              id: loadingToast,
              duration: 5000
            });
          } else {
            toast.error('❌ Signature verification failed! Watermark may be tampered.', {
              id: loadingToast,
              duration: 5000
            });
          }
        } else {
          const errorMsg = data.error || 'Failed to verify watermark';
          toast.error(errorMsg, { id: loadingToast });
          setError(errorMsg);
        }
      }
    } catch (err) {
      const errorMsg = 'Network error: Could not connect to server. Make sure the backend is running.';
      toast.error(errorMsg, { id: loadingToast });
      setError(errorMsg);
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
          multiple
          style={{ display: 'none' }}
        />
        <button
          className="btn-primary"
          onClick={() => fileInputRef.current?.click()}
        >
          📁 Select Watermarked Image(s)
        </button>
        {selectedImages.length > 0 && (
          <span className="filename">
            {selectedImages.length === 1
              ? selectedImages[0].name
              : `${selectedImages.length} images selected`}
          </span>
        )}
      </div>

      {previewUrls.length > 0 && !batchResults && (
        <div className="carousel-container">
          {/* Main Image Display */}
          <div className="carousel-main">
            {selectedImages.length > 1 && (
              <button
                className="carousel-arrow carousel-arrow-left"
                onClick={handlePrevImage}
                disabled={currentImageIndex === 0}
              >
                ‹
              </button>
            )}

            <div className="carousel-image-wrapper">
              <img
                src={previewUrls[currentImageIndex]}
                alt={`Preview ${currentImageIndex + 1}`}
                className="image-preview"
              />
              {selectedImages.length > 1 && (
                <div className="carousel-counter">
                  {currentImageIndex + 1} / {selectedImages.length}
                </div>
              )}
            </div>

            {selectedImages.length > 1 && (
              <button
                className="carousel-arrow carousel-arrow-right"
                onClick={handleNextImage}
                disabled={currentImageIndex === selectedImages.length - 1}
              >
                ›
              </button>
            )}
          </div>

          {/* Thumbnail Gallery */}
          {selectedImages.length > 1 && (
            <div className="carousel-thumbnails">
              {selectedImages.map((img, idx) => (
                <div
                  key={idx}
                  className={`thumbnail ${idx === currentImageIndex ? 'active' : ''}`}
                  onClick={() => handleSelectImage(idx)}
                >
                  <img src={previewUrls[idx]} alt={`Thumb ${idx + 1}`} />
                  <span className="thumbnail-name">{img.name}</span>
                </div>
              ))}
            </div>
          )}

          {selectedImages.length > 1 && (
            <div className="keyboard-hint">
              💡 <strong>Tip:</strong> Use ← → arrow keys to navigate between images
            </div>
          )}

          <div className="preview-info">
            <p><strong>Current:</strong> {selectedImages[currentImageIndex].name}</p>
            {selectedImages.length > 1 && (
              <p><strong>Ready to verify:</strong> {selectedImages.length} images</p>
            )}
          </div>
        </div>
      )}

      <button
        className="btn-verify"
        onClick={handleVerify}
        disabled={loading || selectedImages.length === 0}
      >
        {loading ? '⏳ Verifying...' : selectedImages.length > 1 ? `🔍 Verify ${selectedImages.length} Images` : '🔍 Extract & Verify Watermark'}
      </button>

      {error && <div className="status-error">❌ {error}</div>}

      {batchResults && (
        <div className="batch-results">
          <div className="batch-summary">
            <h2>📊 Batch Verification Results</h2>
            <p><strong>Total Images:</strong> {batchResults.summary.total}</p>
            <p><strong>Successfully Processed:</strong> {batchResults.summary.successful}</p>
            <p><strong>Valid Signatures:</strong> {batchResults.summary.valid_signatures}</p>
            <p><strong>Success Rate:</strong> {((batchResults.summary.valid_signatures / batchResults.summary.total) * 100).toFixed(1)}%</p>
          </div>

          <div className="batch-results-list">
            {batchResults.results.map((res, idx) => (
              <div key={idx} className={`batch-result-item ${res.valid ? 'valid' : 'invalid'}`}>
                <div className="result-header">
                  <strong>{res.filename}</strong>
                  <span className={`status-badge ${res.valid ? 'valid' : 'invalid'}`}>
                    {res.valid ? '✅ Valid' : res.success ? '⚠️ Invalid' : '❌ Error'}
                  </span>
                </div>
                {res.success && (
                  <div className="result-details">
                    <p><strong>Message:</strong> {res.message || '(empty)'}</p>
                    <p><strong>Block Size:</strong> {res.block_size}x{res.block_size}</p>
                    {res.signature_length && <p><strong>Signature:</strong> {res.signature_length} bytes</p>}
                  </div>
                )}
                {res.error && <p className="error-text">Error: {res.error}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

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

            <div className="result-field">
              <label>Detected Block Size:</label>
              <div>{result.block_size}x{result.block_size} pixels</div>
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


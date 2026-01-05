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
  const [dragActive, setDragActive] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Process files (used by both file input and drag & drop)
  const processFiles = (files: File[]) => {
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

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    processFiles(files);
  };

  // Drag & Drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragIn = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setDragActive(true);
    }
  };

  const handleDragOut = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files).filter(file =>
      file.type.startsWith('image/')
    );

    if (files.length === 0) {
      toast.error('Please drop valid image files (PNG, JPEG, BMP)');
      return;
    }

    processFiles(files);
    toast.success(`${files.length} image${files.length > 1 ? 's' : ''} loaded successfully!`);
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

  // Remove image from selection
  const handleRemoveImage = (indexToRemove: number) => {
    // Revoke the URL of the image being removed
    URL.revokeObjectURL(previewUrls[indexToRemove]);

    // Filter out the removed image
    const newImages = selectedImages.filter((_, idx) => idx !== indexToRemove);

    if (newImages.length === 0) {
      // No images left - cleanup all URLs
      previewUrls.forEach(url => URL.revokeObjectURL(url));
      setSelectedImages([]);
      setPreviewUrls([]);
      setCurrentImageIndex(0);
      setResult(null);
      setBatchResults(null);
      toast.success('All images removed');
    } else {
      // Recreate preview URLs for remaining images
      const newUrls = newImages.map(file => URL.createObjectURL(file));

      // Cleanup old URLs (except the one we already revoked)
      previewUrls.forEach((url, idx) => {
        if (idx !== indexToRemove) {
          URL.revokeObjectURL(url);
        }
      });

      // Adjust current index
      let newIndex = currentImageIndex;

      if (indexToRemove === currentImageIndex) {
        // Removed the current image - go to previous or stay at same position
        newIndex = Math.max(0, currentImageIndex - 1);
      } else if (indexToRemove < currentImageIndex) {
        // Removed image before current - adjust index down
        newIndex = currentImageIndex - 1;
      }
      // else: removed image after current - index stays the same

      // Update state
      setSelectedImages(newImages);
      setPreviewUrls(newUrls);
      setCurrentImageIndex(newIndex);

      toast.success(`Image removed (${newImages.length} remaining)`);
    }
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
            `Verified ${selectedImages.length} images: ${validCount} valid, ${selectedImages.length - validCount} invalid`,
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
            toast.success('Signature verified! Watermark is authentic.', {
              id: loadingToast,
              duration: 5000
            });
          } else {
            toast.error('Signature verification failed! Watermark may be tampered.', {
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
      <div
        className={`upload-section ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleImageSelect}
          accept="image/png,image/jpeg,image/jpg,image/bmp"
          multiple
          style={{ display: 'none' }}
        />

        {dragActive ? (
          <div className="drop-zone-active">
            <div className="drop-icon">📥</div>
            <p className="drop-text">Drop images here...</p>
          </div>
        ) : (
          <>
            <button
              className="btn-primary"
              onClick={() => fileInputRef.current?.click()}
            >
              📁 Select Watermarked Image(s)
            </button>
            <span className="drag-hint">or drag & drop images here</span>
          </>
        )}

        {selectedImages.length > 0 && !dragActive && (
          <span className="filename">
            {selectedImages.length === 1
              ? selectedImages[0].name
              : `${selectedImages.length} images selected`}
          </span>
        )}
      </div>

      {previewUrls.length > 0 && (
        <div className="carousel-container" key={`carousel-${previewUrls.length}`}>
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
                src={previewUrls[Math.min(currentImageIndex, previewUrls.length - 1)]}
                alt={`Preview ${currentImageIndex + 1}`}
                className="image-preview"
                key={`preview-${currentImageIndex}-${previewUrls.length}`}
              />
              {selectedImages.length > 1 && (
                <div className="carousel-counter">
                  {Math.min(currentImageIndex + 1, selectedImages.length)} / {selectedImages.length}
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
                  key={`thumb-${idx}-${img.name}-${selectedImages.length}`}
                  className={`thumbnail ${idx === currentImageIndex ? 'active' : ''}`}
                >
                  <img
                    src={previewUrls[idx] || ''}
                    alt={`Thumb ${idx + 1}`}
                    onClick={() => handleSelectImage(idx)}
                  />
                  <button
                    className="thumbnail-remove"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveImage(idx);
                    }}
                    title="Remove image"
                  >
                    ✕
                  </button>
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


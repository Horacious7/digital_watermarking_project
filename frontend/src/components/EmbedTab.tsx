import React, { useState, useRef, useEffect } from 'react';
import './EmbedTab.css';
import toast from 'react-hot-toast';
import { ImagePlusIcon, BulbIcon, ArrowDownIcon, FileLockIcon, AttentionIcon, HourglassIcon, CheckIcon, XMarkIcon } from './Icons';
import KeyManager from './KeyManager';
import { getPrivateKey, getPublicKey, hasPrivateKey } from '../services/keyManager';

const API_BASE_URL = 'http://localhost:5000/api';

// Block size reliability categories based on extensive testing on 15 synthetic stress-test images
const SAFE_BLOCK_SIZES = [3, 5, 6]; // 100% reliable
const WARNING_BLOCK_SIZES = [2, 4, 8, 9, 10]; // 80-90% reliable
const DANGER_BLOCK_SIZES = [7, 11, 12, 13, 14, 15, 16, 17, 18]; // <80% reliable

const getBlockSizeStatus = (bs: number): { color: string; label: string; cssClass: string } => {
  if (SAFE_BLOCK_SIZES.includes(bs)) {
    return { color: '#4ade80', label: 'Highly Reliable', cssClass: 'block-size-safe' };
  }
  if (WARNING_BLOCK_SIZES.includes(bs)) {
    return { color: '#fbbf24', label: 'Moderately Reliable', cssClass: 'block-size-warning' };
  }
  if (DANGER_BLOCK_SIZES.includes(bs)) {
    return { color: '#f87171', label: 'May Be Unreliable', cssClass: 'block-size-danger' };
  }
  return { color: '#94a3b8', label: 'Unknown Reliability', cssClass: 'block-size-unknown' };
};

interface CapacityInfo {
  capacity_bits: number;
  capacity_bytes: number;
  image_size: { width: number; height: number };
  block_size: number;
  signature_overhead_bytes?: number;  // Optional for backward compatibility
}

const EmbedTab: React.FC = () => {
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [currentImageIndex, setCurrentImageIndex] = useState<number>(0);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [message, setMessage] = useState<string>('');
  const [blockSize, setBlockSize] = useState<number>(8);
  const [useOptimization, setUseOptimization] = useState<boolean>(true); // New optimization toggle
  const [capacity, setCapacity] = useState<CapacityInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [status, setStatus] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [dragActive, setDragActive] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [privateKeyAvailable, setPrivateKeyAvailable] = useState<boolean>(false);

  // Check for private key on mount and when keys change
  useEffect(() => {
    setPrivateKeyAvailable(hasPrivateKey());
  }, []);

  const handleKeysChanged = () => {
    setPrivateKeyAvailable(hasPrivateKey());
  };

  // Process files (used by both file input and drag & drop)
  const processFiles = async (files: File[]) => {
    if (files.length === 0) return;

    setSelectedImages(files);
    setCurrentImageIndex(0);

    // Create preview URLs for all images
    const urls = files.map(file => URL.createObjectURL(file));
    setPreviewUrls(urls);

    setError('');
    setStatus('');

    // Calculate capacity for first image
    await calculateCapacity(files[0], blockSize);
  };

  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    // Reset the input value to allow selecting the same file again if needed
    e.target.value = '';
    await processFiles(files);
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

  const handleDrop = async (e: React.DragEvent) => {
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

    await processFiles(files);
    toast.success(`${files.length} image${files.length > 1 ? 's' : ''} loaded successfully!`);
  };

  // Navigate to previous image
  const handlePrevImage = async () => {
    if (currentImageIndex > 0) {
      const newIndex = currentImageIndex - 1;
      setCurrentImageIndex(newIndex);
      await calculateCapacity(selectedImages[newIndex], blockSize);
    }
  };

  // Navigate to next image
  const handleNextImage = async () => {
    if (currentImageIndex < selectedImages.length - 1) {
      const newIndex = currentImageIndex + 1;
      setCurrentImageIndex(newIndex);
      await calculateCapacity(selectedImages[newIndex], blockSize);
    }
  };

  // Navigate to specific image by index
  const handleSelectImage = async (index: number) => {
    setCurrentImageIndex(index);
    await calculateCapacity(selectedImages[index], blockSize);
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
      setCapacity(null);
      setCurrentImageIndex(0);
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

      // Recalculate capacity for the new current image
      setTimeout(() => {
        calculateCapacity(newImages[newIndex], blockSize);
      }, 0);

      toast.success(`Image removed (${newImages.length} remaining)`);
    }
  };

  const calculateCapacity = async (file: File, bs: number) => {
    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('block_size', bs.toString());
      // use_optimization doesn't affect capacity calculation logic on backend currently, 
      // but good to keep in mind if that changes. For now we just send block_size.
      formData.append('use_optimization', useOptimization.toString()); // Just in case backend uses it later for capacity

      const response = await fetch(`${API_BASE_URL}/capacity`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setCapacity(data);
        setError('');
      } else {
        const errorData = await response.json();
        const errorMsg = errorData.error || 'Failed to calculate image capacity';
        toast.error(errorMsg);
        setError(errorMsg);
        setCapacity(null);
      }
    } catch (err) {
      console.error('Error calculating capacity:', err);
      const errorMsg = 'Network error: Could not connect to server. Make sure the backend is running.';
      toast.error(errorMsg);
      setError(errorMsg);
      setCapacity(null);
    }
  };

  const handleBlockSizeChange = (newSize: number) => {
    setBlockSize(newSize);

    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new timer - only call API after 300ms of no changes
    if (selectedImages.length > 0) {
      debounceTimerRef.current = setTimeout(() => {
        calculateCapacity(selectedImages[currentImageIndex], newSize);
      }, 300);
    }
  };

  // Cleanup timer and preview URLs on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      // Cleanup preview URLs
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

  const handleEmbed = async () => {
    if (selectedImages.length === 0 || !message) {
      toast.error('Please select images and enter a message');
      return;
    }
    
    // Check if private key is available
    if (!hasPrivateKey()) {
      toast.error('Private key is required for signing. Please generate or import keys in the Key Management section.');
      return;
    }

    setLoading(true);
    setStatus('Processing...');
    setError('');
    
    const loadingToast = toast.loading('Processing watermarks...');

    try {
      const formData = new FormData();
      
      // Append all selected images
      selectedImages.forEach((file) => {
        formData.append('images', file);
      });
      
      formData.append('message', message);
      formData.append('block_size', blockSize.toString());
      formData.append('use_optimization', useOptimization.toString()); // Pass the toggle
      
      // Append private key
      const privateKey = getPrivateKey();
      if (privateKey) {
        formData.append('private_key', privateKey);
      } else {
        throw new Error('Private key not found');
      }
      
      // Append public key (needed for immediate verification in batch mode)
      const publicKey = getPublicKey();
      if (publicKey) {
        formData.append('public_key', publicKey);
      }
      
      const response = await fetch(`${API_BASE_URL}/embed/batch`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const blob = await response.blob();

        // Parse batch statistics from headers
        const totalHeader = response.headers.get('X-Batch-Total');
        const successfulHeader = response.headers.get('X-Batch-Successful');
        const failedHeader = response.headers.get('X-Batch-Failed');
        const failedImagesJson = response.headers.get('X-Batch-Failed-Images');

        // Debug: log headers
        console.log('Batch headers:', {
          total: totalHeader,
          successful: successfulHeader,
          failed: failedHeader,
          failedImagesJson: failedImagesJson
        });

        const total = parseInt(totalHeader || String(selectedImages.length));
        const successful = parseInt(successfulHeader || '0');
        const failed = parseInt(failedHeader || '0');
        const failedImages = failedImagesJson ? JSON.parse(failedImagesJson) : [];

        console.log('Parsed batch stats:', { total, successful, failed, failedImages });

        // TRY to get filename from Content-Disposition header
        let downloadFilename = 'watermarked_images.zip';
        const contentDisposition = response.headers.get('Content-Disposition');
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
            if (filenameMatch && filenameMatch[1]) {
                downloadFilename = filenameMatch[1];
            }
        } else {
            // Fallback: If only 1 successful image and it's not a ZIP, guess extension
            if (successful === 1 && failed === 0 && blob.type !== 'application/zip') {
                 // Try to use original filename with prefix
                 if (selectedImages.length === 1) {
                     const originalName = selectedImages[0].name;
                     const nameParts = originalName.split('.');
                     const ext = nameParts.pop();
                     const base = nameParts.join('.');
                     downloadFilename = `watermarked_${base}.png`; // Backend outputs png
                 } else {
                     downloadFilename = 'watermarked_image.png';
                 }
            }
        }

        // Download file (ZIP or single image)
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = downloadFilename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        // AUTO-REMOVE: Remove successful images from list
        if (failed > 0 && failedImages.length > 0) {
          // Keep only failed images
          const failedFilenames = new Set(failedImages.map((f: any) => f.filename));
          const remainingImages = selectedImages.filter(img => failedFilenames.has(img.name));

          // Revoke old preview URLs
          previewUrls.forEach(url => URL.revokeObjectURL(url));

          // Create new preview URLs for remaining images
          const remainingUrls = remainingImages.map(file => URL.createObjectURL(file));

          setSelectedImages(remainingImages);
          setPreviewUrls(remainingUrls);
          setCurrentImageIndex(0);

          // Recalculate capacity for first remaining image
          if (remainingImages.length > 0) {
            setTimeout(() => {
              calculateCapacity(remainingImages[0], blockSize);
            }, 0);
          }

          // Show detailed toast with failures
          const failureDetails = failedImages.map((f: any) => `• ${f.filename}: ${f.error}`).join('\n');
          toast.error(
            `${successful}/${total} images watermarked successfully!\n\n` +
            `${failed} images failed:\n${failureDetails}\n\n` +
            `Failed images remain in the list. Try a different block size.`,
            { id: loadingToast, duration: 10000 }
          );
          setError(`${failed} images failed verification. Check toast notification for details.`);
        } else {
          // All succeeded - clear all images
          setSelectedImages([]);
          setPreviewUrls([]);
          setCurrentImageIndex(0);
          setCapacity(null);

          toast.success(`All ${successful} images watermarked & verified successfully! Download started.`, {
            id: loadingToast,
            duration: 5000,
          });
          setStatus('');
          setError('');
        }
      } else {
        const errorData = await response.json();

        // Handle case where ALL images failed
        if (errorData.failed_images && errorData.failed_images.length > 0) {
          const failureDetails = errorData.failed_images.map((f: any) => `• ${f.filename}: ${f.error}`).join('\n');
          
          if (errorData.total === 1) {
             toast.error(
              `Embedding failed!\n\n${failureDetails}\n\n` +
              `Try using a different block size or smaller message.`,
              { id: loadingToast, duration: 10000 }
            );
            setError(`Image failed: ${errorData.failed_images[0].error}`);
          } else {
            toast.error(
              `All ${errorData.total} images failed!\n\n${failureDetails}\n\n` +
              `Try using a different block size or smaller message.`,
              { id: loadingToast, duration: 10000 }
            );
            setError(`All images failed: ${errorData.error}`);
          }
        } else {
          toast.error(errorData.error || 'Failed to embed watermarks', { id: loadingToast });
          setError(errorData.error || 'Failed to embed watermarks');
        }
        setStatus('');
      }
    } catch (err) {
      setError('Network error: Could not connect to server');
      setStatus('');
    } finally {
      setLoading(false);
    }
  };

  const messageBytes = new TextEncoder().encode(message).length;
  // Calculate signature overhead dynamically based on whether private key is loaded
  // If no private key: overhead is 0 (no signature will be added)
  // If private key exists: 265 bytes (4 bytes sig_len + 256 bytes RSA-2048 + 4 bytes terminator + 1 byte safety margin)
  const signatureOverhead = privateKeyAvailable ? (capacity?.signature_overhead_bytes || 265) : 0;
  const totalPayloadBytes = messageBytes + signatureOverhead;
  const totalPayloadBits = totalPayloadBytes * 8;
  const capacityOk = capacity && totalPayloadBits <= capacity.capacity_bits;

  return (
    <div className="embed-tab">
      <KeyManager requirePrivateKey={true} onKeysChanged={handleKeysChanged} />

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
            <div className="drop-icon">
              <ArrowDownIcon size={48} />
            </div>
            <p className="drop-text">Drop images here...</p>
          </div>
        ) : (
          <>
            <button
              className="btn-primary upload-btn"
              onClick={() => fileInputRef.current?.click()}
            >
              <ImagePlusIcon size={18} /> Select Image(s)
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
              <BulbIcon size={16} /> <strong>Tip:</strong> Use ← → arrow keys to navigate between images
            </div>
          )}

          {/* Image Info */}
          <div className="preview-section">
            {capacity && (
              <div className="capacity-info">
                <h3>Image Information - {selectedImages[currentImageIndex].name}</h3>
                <p><strong>Size:</strong> {capacity.image_size.width} × {capacity.image_size.height} px</p>
                <p><strong>Capacity:</strong> {capacity.capacity_bits} bits ({capacity.capacity_bytes} bytes)</p>
                <p><strong>Block Size:</strong> {capacity.block_size}</p>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="input-section">
        <label>
          <strong>Message to Embed:</strong>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter the message you want to embed in the image..."
            rows={4}
            className="message-input"
          />
        </label>

        <div className="payload-info">
          <p><strong>Payload Breakdown:</strong></p>
          <p>• Message: {messageBytes} bytes</p>
          {signatureOverhead > 0 && (
            <p>• Digital Signature + Overhead: {signatureOverhead} bytes (includes 1-byte safety margin)</p>
          )}
          <p>• <strong>Total Required:</strong> {totalPayloadBytes} bytes ({totalPayloadBits} bits)</p>
          {capacity && (
            <>
              <p>• <strong>Available Capacity:</strong> {capacity.capacity_bytes} bytes ({capacity.capacity_bits} bits)</p>
              <p className={capacityOk ? 'text-success' : 'text-error'}>
                {capacityOk
                  ? <><CheckIcon size={16} /> Message {signatureOverhead > 0 ? '+ signature' : ''} fits safely in image!</>
                  : <><XMarkIcon size={16} /> Need {totalPayloadBytes - capacity.capacity_bytes} more bytes (reduce message or decrease block size)</>}
              </p>

              {/* Block Size Reliability Indicator */}
              {(() => {
                let status = getBlockSizeStatus(blockSize);
                
                // If Resonance Optimization is enabled, we guarantee reliability
                // because we crop to exact multiples of 2*BlockSize, avoiding padding artifacts
                if (useOptimization) {
                  status = {
                    color: '#4ade80', 
                    label: 'Highly Reliable', 
                    cssClass: 'block-size-safe'
                  };
                }

                return (
                  <div className={`block-size-indicator ${status.cssClass}`}>
                    <span className="indicator-dot" style={{backgroundColor: status.color}}></span>
                    <span className="indicator-text">
                      Block Size {blockSize}×{blockSize}: <strong>{status.label}</strong>
                    </span>
                  </div>
                );
              })()}
            </>
          )}
        </div>

        <label>
          <strong>Block Size:</strong>
          <div className="block-size-control">
            <input
              type="range"
              min="2"
              max="64"
              value={blockSize}
              onChange={(e) => handleBlockSizeChange(parseInt(e.target.value))}
              className="slider"
            />
            <span className="block-size-value">{blockSize}</span>
          </div>
          <small>Smaller blocks = more capacity, but less robust to attacks</small>
        </label>

        <div className="optimization-container">
          <div className="optimization-header">
            <div className="optimization-title">
              <strong>Resonance Optimization</strong>
              {useOptimization && <span className="badge-recommended">Recommended</span>}
            </div>
            <div className="optimization-switch" onClick={() => setUseOptimization(!useOptimization)}>
              <div className={`switch-slider ${useOptimization ? 'on' : 'off'}`}>
                <div className="switch-knob"></div>
              </div>
            </div>
          </div>
          
          <p className="optimization-description">
            {useOptimization 
              ? "Automatically adjusts image dimensions (via slight cropping) to eliminate edge padding and entropy artifacts, ensuring perfect alignment with the watermarking grid. Guarantees 100% cryptographic stability."
              : "Uses original image dimensions. NOTICE: If dimensions are not divisible by (2 × BlockSize), asymmetric padding or edge entropy may cause signature verification failures."}
          </p>
        </div>
      </div>

      <button
        className="btn-embed"
        onClick={handleEmbed}
        disabled={loading || selectedImages.length === 0 || !message || !capacityOk || !privateKeyAvailable}
      >
        {loading ? (
          <><HourglassIcon size={18} /> Embedding...</>
        ) : selectedImages.length > 1 ? (
          <><FileLockIcon size={18} /> Embed & Sign {selectedImages.length} Images</>
        ) : (
          <><FileLockIcon size={18} /> Embed & Sign Watermark</>
        )}
      </button>

      {status && <div className="status-success">{status}</div>}
      {error && <div className="status-error">❌ {error}</div>}

      <div className="info-box">
        <p><strong><AttentionIcon size={18} /> Important Information</strong></p>
        <p>
          This watermarking system works best with <strong>lossless image formats (PNG)</strong>.
          The watermark will be embedded in the DCT coefficients of the image.
        </p>
        <p>
          <strong>Note:</strong> Compression (JPEG, WebP) or sharing via social media
          (WhatsApp, Facebook, Instagram) will alter the embedded data. While the message
          may still be extractable, the cryptographic signature verification will likely fail.
        </p>
      </div>
    </div>
  );
};

export default EmbedTab;


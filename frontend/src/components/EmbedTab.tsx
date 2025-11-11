import React, { useState, useRef, useCallback, useEffect } from 'react';
import './EmbedTab.css';

const API_BASE_URL = 'http://localhost:5000/api';

interface CapacityInfo {
  capacity_bits: number;
  capacity_bytes: number;
  image_size: { width: number; height: number };
  block_size: number;
}

const EmbedTab: React.FC = () => {
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [currentImageIndex, setCurrentImageIndex] = useState<number>(0);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [message, setMessage] = useState<string>('');
  const [blockSize, setBlockSize] = useState<number>(8);
  const [capacity, setCapacity] = useState<CapacityInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [status, setStatus] = useState<string>('');
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
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

  const calculateCapacity = async (file: File, bs: number) => {
    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('block_size', bs.toString());

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
        setError(errorData.error || 'Failed to calculate image capacity');
        setCapacity(null);
      }
    } catch (err) {
      console.error('Error calculating capacity:', err);
      setError('Network error: Could not connect to server. Make sure the backend is running.');
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
      setError('Please select image(s) and enter a message');
      return;
    }

    setLoading(true);
    setError('');

    const isBatch = selectedImages.length > 1;
    setStatus(isBatch ? `Embedding watermark into ${selectedImages.length} images...` : 'Embedding watermark...');

    try {
      const formData = new FormData();

      if (isBatch) {
        // Batch processing
        selectedImages.forEach(img => {
          formData.append('images', img);
        });
        formData.append('message', message);
        formData.append('block_size', blockSize.toString());

        const response = await fetch(`${API_BASE_URL}/embed/batch`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'watermarked_images.zip';
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);

          setStatus(`✅ Watermarked ${selectedImages.length} images successfully! ZIP file downloaded.`);
          setError('');
        } else {
          const errorData = await response.json();
          setError(errorData.error || 'Failed to embed watermarks');
          setStatus('');
        }
      } else {
        // Single image processing
        formData.append('image', selectedImages[0]);
        formData.append('message', message);
        formData.append('block_size', blockSize.toString());

        const response = await fetch(`${API_BASE_URL}/embed`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `watermarked_${selectedImages[0].name}`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);

          setStatus('✅ Watermark embedded successfully! File downloaded.');
          setError('');
        } else {
          const errorData = await response.json();
          setError(errorData.error || 'Failed to embed watermark');
          setStatus('');
        }
      }
    } catch (err) {
      setError('Network error: Could not connect to server');
      setStatus('');
    } finally {
      setLoading(false);
    }
  };

  const messageBytes = new TextEncoder().encode(message).length;
  const signatureOverhead = 260; // Approximate RSA signature size + length field
  const totalPayloadBytes = messageBytes + signatureOverhead;
  const totalPayloadBits = totalPayloadBytes * 8;
  const capacityOk = capacity && totalPayloadBits <= capacity.capacity_bits;

  return (
    <div className="embed-tab">
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
          📁 Select Image(s)
        </button>
        {selectedImages.length > 0 && (
          <span className="filename">
            {selectedImages.length === 1
              ? selectedImages[0].name
              : `${selectedImages.length} images selected`}
          </span>
        )}
      </div>

      {previewUrls.length > 0 && (
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
          <p>Message: {messageBytes} bytes | Signature: ~{signatureOverhead} bytes | <strong>Total: {totalPayloadBits} bits</strong></p>
          {capacity && (
            <p className={capacityOk ? 'text-success' : 'text-error'}>
              {capacityOk ? '✅ Message fits in image' : '❌ Message too large for image capacity'}
            </p>
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
      </div>

      <button
        className="btn-embed"
        onClick={handleEmbed}
        disabled={loading || selectedImages.length === 0 || !message || !capacityOk}
      >
        {loading ? '⏳ Embedding...' : selectedImages.length > 1 ? `🔐 Embed & Sign ${selectedImages.length} Images` : '🔐 Embed & Sign Watermark'}
      </button>

      {status && <div className="status-success">{status}</div>}
      {error && <div className="status-error">❌ {error}</div>}

      <div className="info-box" style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f0f8ff', borderLeft: '4px solid #2196F3', borderRadius: '4px' }}>
        <p><strong>ℹ️ Important Information</strong></p>
        <p style={{ margin: '5px 0', fontSize: '14px' }}>
          This watermarking system works best with <strong>lossless image formats (PNG)</strong>.
          The watermark will be embedded in the DCT coefficients of the image.
        </p>
        <p style={{ margin: '5px 0', fontSize: '14px' }}>
          <strong>⚠️ Note:</strong> Compression (JPEG, WebP) or sharing via social media
          (WhatsApp, Facebook, Instagram) will alter the embedded data. While the message
          may still be extractable, the cryptographic signature verification will likely fail.
        </p>
      </div>
    </div>
  );
};

export default EmbedTab;


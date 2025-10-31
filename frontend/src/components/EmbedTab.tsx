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
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const [blockSize, setBlockSize] = useState<number>(8);
  const [capacity, setCapacity] = useState<CapacityInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [status, setStatus] = useState<string>('');
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedImage(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError('');
    setStatus('');

    // Calculate capacity
    await calculateCapacity(file, blockSize);
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
    if (selectedImage) {
      debounceTimerRef.current = setTimeout(() => {
        calculateCapacity(selectedImage, newSize);
      }, 300);
    }
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const handleEmbed = async () => {
    if (!selectedImage || !message) {
      setError('Please select an image and enter a message');
      return;
    }

    setLoading(true);
    setError('');
    setStatus('Embedding watermark...');

    try {
      const formData = new FormData();
      formData.append('image', selectedImage);
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
        a.download = `watermarked_${selectedImage.name}`;
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
          style={{ display: 'none' }}
        />
        <button
          className="btn-primary"
          onClick={() => fileInputRef.current?.click()}
        >
          📁 Select Image
        </button>
        {selectedImage && <span className="filename">{selectedImage.name}</span>}
      </div>

      {previewUrl && (
        <div className="preview-section">
          <img src={previewUrl} alt="Preview" className="image-preview" />
          {capacity && (
            <div className="capacity-info">
              <h3>Image Information</h3>
              <p><strong>Size:</strong> {capacity.image_size.width} × {capacity.image_size.height} px</p>
              <p><strong>Capacity:</strong> {capacity.capacity_bits} bits ({capacity.capacity_bytes} bytes)</p>
              <p><strong>Block Size:</strong> {capacity.block_size}</p>
            </div>
          )}
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
        disabled={loading || !selectedImage || !message || !capacityOk}
      >
        {loading ? '⏳ Embedding...' : '🔐 Embed & Sign Watermark'}
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


import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders digital watermarking header', () => {
  render(<App />);
  const headerElement = screen.getByText(/Digital Watermarking for Historical Photos/i);
  expect(headerElement).toBeInTheDocument();
});

test('renders embed tab button', () => {
  render(<App />);
  const embedButton = screen.getByText(/Embed Watermark/i);
  expect(embedButton).toBeInTheDocument();
});

test('renders verify tab button', () => {
  render(<App />);
  const verifyButton = screen.getByText(/Verify Watermark/i);
  expect(verifyButton).toBeInTheDocument();
});

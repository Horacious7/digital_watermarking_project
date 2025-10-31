"""
Test script pentru Digital Watermarking API
Rulează toate endpoint-urile pentru a verifica funcționalitatea
"""
import requests
import os
from pathlib import Path

API_BASE_URL = "http://localhost:5000/api"
TEST_IMAGE = "data/test.png"

def test_health():
    """Test health check endpoint"""
    print("\n" + "="*50)
    print("Testing: Health Check")
    print("="*50)

    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            print("✅ Health check PASSED")
            return True
        else:
            print("❌ Health check FAILED")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_capacity():
    """Test capacity calculation endpoint"""
    print("\n" + "="*50)
    print("Testing: Capacity Calculation")
    print("="*50)

    if not os.path.exists(TEST_IMAGE):
        print(f"❌ Test image not found: {TEST_IMAGE}")
        return False

    try:
        with open(TEST_IMAGE, 'rb') as f:
            files = {'image': f}
            data = {'block_size': 8}
            response = requests.post(f"{API_BASE_URL}/capacity", files=files, data=data)

        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Capacity: {result.get('capacity_bits')} bits ({result.get('capacity_bytes')} bytes)")
        print(f"Image Size: {result.get('image_size')}")
        print(f"Block Size: {result.get('block_size')}")

        if response.status_code == 200:
            print("✅ Capacity calculation PASSED")
            return True
        else:
            print(f"❌ Capacity calculation FAILED: {result}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_embed():
    """Test watermark embedding endpoint"""
    print("\n" + "="*50)
    print("Testing: Embed Watermark")
    print("="*50)

    if not os.path.exists(TEST_IMAGE):
        print(f"❌ Test image not found: {TEST_IMAGE}")
        return False

    try:
        message = "Test watermark - Digital Watermarking System"
        output_path = "data/watermarked/test_api_output.png"

        with open(TEST_IMAGE, 'rb') as f:
            files = {'image': f}
            data = {
                'message': message,
                'block_size': 8
            }
            response = requests.post(f"{API_BASE_URL}/embed", files=files, data=data)

        print(f"Status Code: {response.status_code}")
        print(f"Message: {message}")

        if response.status_code == 200:
            # Save the watermarked image
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Watermarked image saved to: {output_path}")
            print("✅ Embed watermark PASSED")
            return output_path
        else:
            error = response.json()
            print(f"❌ Embed watermark FAILED: {error}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_verify(watermarked_image):
    """Test watermark verification endpoint"""
    print("\n" + "="*50)
    print("Testing: Verify Watermark")
    print("="*50)

    if not watermarked_image or not os.path.exists(watermarked_image):
        print(f"❌ Watermarked image not found: {watermarked_image}")
        return False

    try:
        with open(watermarked_image, 'rb') as f:
            files = {'image': f}
            data = {'block_size': 8}
            response = requests.post(f"{API_BASE_URL}/verify", files=files, data=data)

        print(f"Status Code: {response.status_code}")
        result = response.json()

        if 'error' in result:
            print(f"❌ Verify watermark FAILED: {result['error']}")
            return False

        print(f"Extracted Message: {result.get('message')}")
        print(f"Signature Valid: {result.get('valid')}")
        print(f"Signature Length: {result.get('signature_length')} bytes")

        if response.status_code == 200 and result.get('valid'):
            print("✅ Verify watermark PASSED")
            return True
        else:
            print("❌ Signature verification FAILED")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*70)
    print("DIGITAL WATERMARKING API - TEST SUITE")
    print("="*70)

    results = {
        'health': False,
        'capacity': False,
        'embed': False,
        'verify': False
    }

    # Test 1: Health Check
    results['health'] = test_health()

    if not results['health']:
        print("\n❌ API is not running! Please start the backend first.")
        print("Run: python api.py")
        return

    # Test 2: Capacity
    results['capacity'] = test_capacity()

    # Test 3: Embed
    watermarked_image = test_embed()
    results['embed'] = watermarked_image is not None

    # Test 4: Verify (only if embed succeeded)
    if results['embed']:
        results['verify'] = test_verify(watermarked_image)

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    total_tests = len(results)
    passed_tests = sum(results.values())

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper()}: {status}")

    print("-" * 70)
    print(f"Total: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! API is working correctly.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please check the errors above.")

    print("="*70)

if __name__ == "__main__":
    run_all_tests()


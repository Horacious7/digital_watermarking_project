from __future__ import annotations

import hashlib
import tempfile
import time
import csv
import concurrent.futures
from dataclasses import dataclass
from pathlib import Path

import cv2
import pywt

from backend.crypto.keys import generate_rsa_keys
from backend.crypto.sign import sign_hash
from backend.crypto.verify import verify_signature
from backend.utils.conversions import bits_to_bytes, bytes_to_bits
from backend.watermarking.embed import embed_watermark
from backend.watermarking.extract import extract_watermark

BLOCK_SIZES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
ITERATIONS = 3
FIXED_MESSAGE = "TRACE_BENCHMARK_PAYLOAD"
MARGIN_FALLBACK_BITS = [0, 32, 64, 96]


def _dataset_dir() -> Path:
    return Path(__file__).resolve().parent / "dataset"


def _list_dataset_images(dataset_dir: Path) -> list[Path]:
    images = sorted(dataset_dir.glob("*.png"))
    if not images:
        raise FileNotFoundError("No PNG files found. Run generate_data.py first.")
    return images


def _build_payload(message: str, private_key_path: Path) -> str:
    message_bytes = message.encode("utf-8")
    message_hash = hashlib.sha256(message_bytes).digest()
    signature = sign_hash(str(private_key_path), message_hash)
    sig_len_bytes = len(signature).to_bytes(4, byteorder="big")
    payload = sig_len_bytes + signature + message_bytes
    return bytes_to_bits(payload)


def _verify_from_extracted_bits(extracted_bits: str, public_key_path: Path) -> bool:
    try:
        payload_bytes = bits_to_bytes(extracted_bits)
        if len(payload_bytes) < 4:
            return False
        sig_len = int.from_bytes(payload_bytes[:4], byteorder="big")
        sig_start = 4
        sig_end = sig_start + sig_len
        if len(payload_bytes) < sig_end:
            return False
        signature = payload_bytes[sig_start:sig_end]
        message_bytes = payload_bytes[sig_end:]
        msg_hash = hashlib.sha256(message_bytes).digest()
        return verify_signature(str(public_key_path), msg_hash, signature)
    except Exception:
        return False


def _available_blocks(image_path: Path, block_size: int) -> int:
    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    blue = img[:, :, 0].astype("float32")
    cA, _ = pywt.dwt2(blue, "haar")
    cA_h, cA_w = cA.shape
    return (cA_h // block_size) * (cA_w // block_size)


@dataclass
class CaseResult:
    block_size: int
    image_name: str
    iteration: int
    success: bool
    duration_s: float
    psnr: float = 0.0  # Added metric
    error: str = ""
    skipped_capacity: bool = False
    margin_used: int = -1


def process_one_case(
    block_size: int,
    image_path: Path,
    iteration: int,
    out_dir: Path,
    private_key_path: Path,
    public_key_path: Path,
    base_payload_bits: str,
    margin_fallback_bits: list[int]
) -> CaseResult:
    """Worker function for multiprocessing."""
    t0 = time.perf_counter()
    image_name = image_path.name

    try:
        available_capacity = _available_blocks(image_path, block_size)
        base_required = 8 + len(base_payload_bits)

        if base_required > available_capacity:
            return CaseResult(
                block_size=block_size, image_name=image_name,
                iteration=iteration, success=False,
                duration_s=time.perf_counter() - t0,
                error="Insufficient Physical Capacity", skipped_capacity=True
            )

        test_passed = False
        final_margin = -1
        last_error = ""
        final_psnr = 0.0

        for margin in margin_fallback_bits:
            total_required = base_required + margin

            if total_required > available_capacity:
                last_error = f"Capacity exceeded at margin {margin}"
                break

            try:
                padded_payload_bits = base_payload_bits + ("0" * margin)
                out_path = out_dir / f"wm_{image_path.stem}_b{block_size}_i{iteration}_m{margin}.png"

                embed_watermark(
                    image_path=str(image_path),
                    watermark_bits=padded_payload_bits,
                    output_path=str(out_path),
                    block_size=block_size,
                )

                # Calculate PSNR
                original_img = cv2.imread(str(image_path))
                watermarked_img = cv2.imread(str(out_path))
                final_psnr = cv2.PSNR(original_img, watermarked_img)

                extracted_bits = extract_watermark(
                    image_path=str(out_path),
                    n_bits=total_required,
                    block_size=block_size,
                )

                if len(extracted_bits) < base_required:
                    raise ValueError("Extracted fewer bits than base required.")

                payload_only = extracted_bits[8: 8 + len(base_payload_bits)]
                is_valid = _verify_from_extracted_bits(payload_only, public_key_path)

                if is_valid:
                    test_passed = True
                    final_margin = margin
                    break
                else:
                    last_error = f"Invalid Signature at margin {margin}"

            except Exception as e:
                last_error = str(e)

        if test_passed:
            return CaseResult(
                block_size=block_size, image_name=image_name,
                iteration=iteration, success=True,
                duration_s=time.perf_counter() - t0, error="",
                margin_used=final_margin, psnr=final_psnr
            )
        else:
            return CaseResult(
                block_size=block_size, image_name=image_name,
                iteration=iteration, success=False,
                duration_s=time.perf_counter() - t0, error=last_error,
                margin_used=final_margin, psnr=final_psnr  # Keep last PSNR (usually 0 unless extract failed)
            )
            
    except Exception as e:
        return CaseResult(
            block_size=block_size, image_name=image_name,
            iteration=iteration, success=False,
            duration_s=time.perf_counter() - t0, error=f"Process Crash: {str(e)}"
        )


def run_benchmark() -> None:
    dataset_dir = _dataset_dir()
    images = _list_dataset_images(dataset_dir)

    # Use a persistent temp dir for parallel workers to access keys
    temp_dir_obj = tempfile.TemporaryDirectory(prefix="trace_bench_")
    tmp_path = Path(temp_dir_obj.name)
    
    try:
        private_key_path = tmp_path / "bench_private.pem"
        public_key_path = tmp_path / "bench_public.pem"
        out_dir = tmp_path / "out"
        out_dir.mkdir(parents=True, exist_ok=True)

        generate_rsa_keys(str(private_key_path), str(public_key_path), key_size=2048)
        base_payload_bits = _build_payload(FIXED_MESSAGE, private_key_path)

        print(f"Dataset: {dataset_dir}")
        print(f"Images: {len(images)}")
        print(f"Block sizes: {BLOCK_SIZES}")
        print(f"Parallel Workers: {min(32, len(BLOCK_SIZES) * len(images))}") # Simple heuristic
        print("-" * 90)

        tasks = []
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for block_size in BLOCK_SIZES:
                for image_path in images:
                    for iteration in range(1, ITERATIONS + 1):
                        tasks.append(
                            executor.submit(
                                process_one_case,
                                block_size,
                                image_path,
                                iteration,
                                out_dir,
                                private_key_path,
                                public_key_path,
                                base_payload_bits,
                                MARGIN_FALLBACK_BITS
                            )
                        )
            
            results = []
            completed = 0
            total = len(tasks)
            print(f"Processing {total} tasks...")
            
            for future in concurrent.futures.as_completed(tasks):
                res = future.result()
                results.append(res)
                completed += 1
                if completed % 10 == 0 or completed == total:
                    print(f"Progress: {completed}/{total} ({res.block_size}px finished)", end="\r")
            
            print(f"\nCompleted all {total} tasks.")

        # Prepare CSV output
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        csv_path = Path(f"benchmark_results_{timestamp}.csv")

        # Sort results for consistent table output
        results.sort(key=lambda x: (x.block_size, x.image_name, x.iteration))

        # --- SUMMARY TABLE ---
        print("\n" + "=" * 105)
        print("BLOCK SIZE RELIABILITY SUMMARY (WITH QUALITY METRICS)")
        print("=" * 105)
        print(
            f"{'Block':>6} | {'Tested':>6} | {'Passed':>6} | {'Skipped':>7} | {'Success %':>9} | {'Avg PSNR':>9} | {'Avg Time':>10}")
        print("-" * 105)

        overall_tested, overall_passed, overall_skipped = 0, 0, 0

        for size in BLOCK_SIZES:
            sub = [r for r in results if r.block_size == size]
            skipped = sum(1 for r in sub if r.skipped_capacity)
            tested = len(sub) - skipped
            passed = sum(1 for r in sub if r.success)
            
            # Avg PSNR only for successful cases
            successful_cases = [r for r in sub if r.success]
            avg_psnr = sum(r.psnr for r in successful_cases) / len(successful_cases) if successful_cases else 0.0

            overall_skipped += skipped
            overall_tested += tested
            overall_passed += passed

            success_rate = (passed / tested * 100.0) if tested > 0 else 0.0
            avg_time = sum(r.duration_s for r in sub if not r.skipped_capacity) / tested if tested > 0 else 0.0

            print(f"{size:>6} | {tested:>6} | {passed:>6} | {skipped:>7} | {success_rate:>8.2f}% | {avg_psnr:>9.2f} | {avg_time:>10.3f}s")

        overall_rate = (overall_passed / overall_tested * 100.0) if overall_tested > 0 else 0.0
        print("-" * 105)
        print(f"Overall Tested: {overall_passed}/{overall_tested} ({overall_rate:.2f}%)")
        print(f"Skipped due to Capacity: {overall_skipped}")
        
        # Save to CSV
        try:
            with open(csv_path, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["BlockSize", "Image", "Iteration", "Success", "Margin", "PSNR", "Duration", "Error"])
                for r in results:
                    writer.writerow([r.block_size, r.image_name, r.iteration, r.success, r.margin_used, f"{r.psnr:.2f}", f"{r.duration_s:.4f}", r.error])
            print(f"\n[INFO] Detailed results saved to: {csv_path.absolute()}")
        except Exception as e:
            print(f"\n[ERROR] Could not save CSV: {e}")
    finally:
        temp_dir_obj.cleanup()  # Ensure temp dir is cleaned up

if __name__ == "__main__":
    run_benchmark()
from __future__ import annotations

import hashlib
import tempfile
import time
import csv
import sys
import concurrent.futures
from dataclasses import dataclass
from pathlib import Path

import cv2
import pywt

from backend.crypto.keys import generate_rsa_keys
from backend.crypto.sign import sign_hash
from backend.crypto.verify import verify_signature
from backend.utils.conversions import bits_to_bytes, bytes_to_bits
from backend.utils.image_utils import get_resonant_crop
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
    optimization: bool
    success: bool
    duration_s: float
    psnr: float = 0.0
    error: str = ""
    skipped_capacity: bool = False
    margin_used: int = -1


def process_one_case(
        block_size: int, image_path: Path, iteration: int, out_dir: Path,
        private_key_path: Path, public_key_path: Path, base_payload_bits: str, margin_fallback_bits: list[int],
        use_optimization: bool  # Added parameter
) -> CaseResult:
    t0 = time.perf_counter()
    image_name = image_path.name
    try:
        available_capacity = _available_blocks(image_path, block_size)
        base_required = 8 + len(base_payload_bits)

        if base_required > available_capacity:
            return CaseResult(block_size=block_size, image_name=image_name, iteration=iteration, optimization=use_optimization, success=False,
                              duration_s=time.perf_counter() - t0, error="CapacityExceeded", skipped_capacity=True)

        test_passed = False
        final_margin = -1
        last_error = ""
        final_psnr = 0.0

        for margin in margin_fallback_bits:
            total_required = base_required + margin
            if total_required > available_capacity:
                last_error = f"CapacityExceeded_Margin_{margin}"
                break

            try:
                padded_payload_bits = base_payload_bits + ("0" * margin)
                out_path = out_dir / f"wm_{image_path.stem}_b{block_size}_i{iteration}_m{margin}_opt{use_optimization}.png"
                embed_watermark(image_path=str(image_path), watermark_bits=padded_payload_bits,
                                output_path=str(out_path), block_size=block_size, use_optimization=use_optimization)

                original_img = cv2.imread(str(image_path))
                watermarked_img = cv2.imread(str(out_path))
                
                # Determine reference image for PSNR calculation based on optimization mode
                if use_optimization:
                    # When optimization is enabled, the embedded image is cropped.
                    original_img_for_psnr = get_resonant_crop(original_img, block_size)
                else:
                    # When optimization is disabled, use original, but ensure dimensions match
                    original_img_for_psnr = original_img

                # Ensure dimensions match exactly for PSNR (handle edge cases)
                h_ref, w_ref = original_img_for_psnr.shape[:2]
                h_wm, w_wm = watermarked_img.shape[:2]
                
                h_common = min(h_ref, h_wm)
                w_common = min(w_ref, w_wm)
                
                original_img_for_psnr = original_img_for_psnr[:h_common, :w_common]
                watermarked_img = watermarked_img[:h_common, :w_common]
                
                final_psnr = cv2.PSNR(original_img_for_psnr, watermarked_img)

                extracted_bits = extract_watermark(image_path=str(out_path), n_bits=total_required,
                                                   block_size=block_size)
                if len(extracted_bits) < base_required:
                    raise ValueError("ExtractionTruncated")

                payload_only = extracted_bits[8: 8 + len(base_payload_bits)]
                if _verify_from_extracted_bits(payload_only, public_key_path):
                    test_passed = True
                    final_margin = margin
                    break
                else:
                    last_error = f"SignatureInvalid_Margin_{margin}"
            except Exception as e:
                last_error = f"Exception_{type(e).__name__}"

        return CaseResult(block_size=block_size, image_name=image_name, iteration=iteration, optimization=use_optimization, success=test_passed,
                          duration_s=time.perf_counter() - t0, error="" if test_passed else last_error,
                          margin_used=final_margin, psnr=final_psnr)
    except Exception as e:
        return CaseResult(block_size=block_size, image_name=image_name, iteration=iteration, optimization=use_optimization, success=False,
                          duration_s=time.perf_counter() - t0, error="ProcessCrash")


def print_progress_bar(iteration, total, prefix='', suffix='', length=40, fill='█', printEnd="\r"):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total:
        print()


def run_benchmark() -> None:
    dataset_dir = _dataset_dir()
    images = _list_dataset_images(dataset_dir)

    temp_dir_obj = tempfile.TemporaryDirectory(prefix="trace_bench_")
    tmp_path = Path(temp_dir_obj.name)

    try:
        private_key_path = tmp_path / "bench_private.pem"
        public_key_path = tmp_path / "bench_public.pem"
        out_dir = tmp_path / "out"
        out_dir.mkdir(parents=True, exist_ok=True)

        generate_rsa_keys(str(private_key_path), str(public_key_path), key_size=2048)
        base_payload_bits = _build_payload(FIXED_MESSAGE, private_key_path)

        print("\n" + "=" * 80)
        print(" TRACE EMPIRICAL RESILIENCE & CAPACITY BENCHMARK")
        print("=" * 80)
        print(f" Target Dataset : {dataset_dir.name} ({len(images)} images)")
        print(f" Block Sizes    : {len(BLOCK_SIZES)} configurations (2x2 to 18x18)")
        print(f" Iterations     : {ITERATIONS} per configuration")
        print(f" Margin Policy  : Dynamic Fallback {MARGIN_FALLBACK_BITS}")
        print("-" * 80)

        tasks = []
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for use_optimization in [True, False]:
                for block_size in BLOCK_SIZES:
                    for image_path in images:
                        for iteration in range(1, ITERATIONS + 1):
                            tasks.append(executor.submit(process_one_case, block_size, image_path, iteration,
                                                         out_dir, private_key_path, public_key_path, base_payload_bits,
                                                         MARGIN_FALLBACK_BITS, use_optimization))

            results = []
            total = len(tasks)
            print_progress_bar(0, total, prefix=' Progress:', suffix='Complete', length=50)

            for i, future in enumerate(concurrent.futures.as_completed(tasks), 1):
                results.append(future.result())
                print_progress_bar(i, total, prefix=' Progress:', suffix=f'({i}/{total}) Processed', length=50)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_path = Path(f"empirical_benchmark_{timestamp}.csv")
        results.sort(key=lambda x: (x.optimization, x.block_size, x.image_name, x.iteration))

        print("\n" + "=" * 95)
        print(" FINAL RESULTS MATRIX")
        print("=" * 95)
        print(
            f"{'Opt':>5} | {'Block':>6} | {'Tested':>8} | {'Passed':>8} | {'Skipped':>8} | {'Success %':>10} | {'Avg PSNR':>9} | {'Avg Time':>10}")
        print("-" * 95)

        overall_tested, overall_passed, overall_skipped = 0, 0, 0

        for opt in [True, False]:
            for size in BLOCK_SIZES:
                sub = [r for r in results if r.optimization == opt and r.block_size == size]
                skipped = sum(1 for r in sub if r.skipped_capacity)
                tested = len(sub) - skipped
                passed = sum(1 for r in sub if r.success)

                successful_cases = [r for r in sub if r.success]
                avg_psnr = sum(r.psnr for r in successful_cases) / len(successful_cases) if successful_cases else 0.0

                overall_skipped += skipped
                overall_tested += tested
                overall_passed += passed

                success_rate = (passed / tested * 100.0) if tested > 0 else 0.0
                avg_time = sum(r.duration_s for r in sub if not r.skipped_capacity) / tested if tested > 0 else 0.0
                
                opt_str = "ON" if opt else "OFF"
                print(
                    f"{opt_str:>5} | {size:>6} | {tested:>8} | {passed:>8} | {skipped:>8} | {success_rate:>9.2f}% | {avg_psnr:>6.2f} dB | {avg_time:>9.3f}s")

        overall_rate = (overall_passed / overall_tested * 100.0) if overall_tested > 0 else 0.0
        print("-" * 95)
        print(
            f" OVERALL: {overall_passed}/{overall_tested} Passed ({overall_rate:.2f}%) | {overall_skipped} Skipped (Capacity Limits)")
        print("=" * 95)

        try:
            with open(csv_path, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["BlockSize", "Image", "Iteration", "Optimization", "Success", "MarginUsed", "PSNR_dB", "Duration_s", "ErrorCode"])
                for r in results:
                    writer.writerow([r.block_size, r.image_name, r.iteration, r.optimization, r.success, r.margin_used, f"{r.psnr:.2f}",
                                     f"{r.duration_s:.4f}", r.error])
            print(f"\n [✓] CSV Report exported to: {csv_path.name}")
        except Exception as e:
            print(f"\n [!] Error saving CSV: {e}")

    finally:
        temp_dir_obj.cleanup()


if __name__ == "__main__":
    run_benchmark()
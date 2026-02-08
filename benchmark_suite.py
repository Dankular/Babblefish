"""
BabbleFish Comprehensive Benchmark Suite

Tests all components of the stack:
1. NLLB Translation (CTranslate2)
2. Whisper Transcription
3. End-to-end Pipeline
4. Real-time System
5. Memory & Resource Usage
"""

import time
import psutil
import os
import tempfile
import wave
import numpy as np
from pathlib import Path
import json

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

class BenchmarkSuite:
    def __init__(self):
        self.results = {}
        self.process = psutil.Process(os.getpid())

    def get_memory_usage(self):
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024

    def benchmark_nllb_translation(self):
        """Benchmark NLLB translation speed"""
        print("\n" + "="*60)
        print("BENCHMARK 1: NLLB Translation (CTranslate2)")
        print("="*60)

        from nllb_ct2_fixed import NLLBTranslatorCT2

        # Test sentences of varying lengths
        test_cases = [
            ("Short", "Hello"),
            ("Medium", "Hello, how are you today?"),
            ("Long", "The quick brown fox jumps over the lazy dog while the sun shines brightly in the clear blue sky."),
            ("Very Long", "Artificial intelligence and machine learning are transforming the way we live and work, enabling unprecedented advances in healthcare, transportation, education, and countless other fields that touch our daily lives.")
        ]

        print("\nLoading NLLB model...")
        mem_before = self.get_memory_usage()
        translator = NLLBTranslatorCT2(device="cpu", compute_type="int8")
        translator.load_model()
        mem_after = self.get_memory_usage()

        print(f"Memory used by model: {mem_after - mem_before:.1f} MB")

        results = []
        for name, text in test_cases:
            # Warm up
            translator.translate(text, "eng_Latn", "spa_Latn")

            # Benchmark
            times = []
            for _ in range(5):
                start = time.time()
                result = translator.translate(text, "eng_Latn", "spa_Latn")
                elapsed = time.time() - start
                times.append(elapsed)

            avg_time = np.mean(times)
            std_time = np.std(times)
            words = len(text.split())
            wps = words / avg_time

            results.append({
                "name": name,
                "words": words,
                "avg_time": avg_time,
                "std_time": std_time,
                "wps": wps
            })

            print(f"\n{name:12} ({words:3} words)")
            print(f"  Time:  {avg_time:.3f}s ± {std_time:.3f}s")
            print(f"  Speed: {wps:.1f} words/sec")

        self.results['nllb'] = results
        return results

    def benchmark_whisper_transcription(self):
        """Benchmark Whisper transcription speed"""
        print("\n" + "="*60)
        print("BENCHMARK 2: Whisper Transcription")
        print("="*60)

        from faster_whisper import WhisperModel

        print("\nLoading Whisper model...")
        mem_before = self.get_memory_usage()
        whisper = WhisperModel("medium", device="cpu", compute_type="int8")
        mem_after = self.get_memory_usage()

        print(f"Memory used by model: {mem_after - mem_before:.1f} MB")

        # Create test audio files of varying lengths
        sample_rate = 16000
        test_durations = [1, 3, 5, 10]  # seconds

        results = []
        for duration in test_durations:
            # Generate dummy audio (silence with some noise)
            samples = int(sample_rate * duration)
            audio = np.random.randn(samples) * 0.01
            audio = audio.astype(np.float32)

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            audio_int16 = (audio * 32768).astype(np.int16)

            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int16.tobytes())

            # Warm up
            segments, info = whisper.transcribe(temp_file.name)
            list(segments)  # Consume generator

            # Benchmark
            times = []
            for _ in range(3):
                start = time.time()
                segments, info = whisper.transcribe(temp_file.name)
                list(segments)  # Consume generator
                elapsed = time.time() - start
                times.append(elapsed)

            os.unlink(temp_file.name)

            avg_time = np.mean(times)
            std_time = np.std(times)
            rtf = avg_time / duration  # Real-time factor

            results.append({
                "duration": duration,
                "avg_time": avg_time,
                "std_time": std_time,
                "rtf": rtf
            })

            print(f"\n{duration}s audio:")
            print(f"  Time: {avg_time:.3f}s ± {std_time:.3f}s")
            print(f"  RTF:  {rtf:.2f}x {'(faster than realtime)' if rtf < 1 else '(slower than realtime)'}")

        self.results['whisper'] = results
        return results

    def benchmark_end_to_end_pipeline(self):
        """Benchmark complete audio → transcription → translation pipeline"""
        print("\n" + "="*60)
        print("BENCHMARK 3: End-to-End Pipeline")
        print("="*60)

        from faster_whisper import WhisperModel
        from nllb_ct2_fixed import NLLBTranslatorCT2

        print("\nLoading models...")
        whisper = WhisperModel("medium", device="cpu", compute_type="int8")
        translator = NLLBTranslatorCT2(device="cpu", compute_type="int8")
        translator.load_model()

        # Create test audio (3 seconds)
        sample_rate = 16000
        duration = 3
        samples = int(sample_rate * duration)
        audio = np.random.randn(samples) * 0.01
        audio = audio.astype(np.float32)

        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        audio_int16 = (audio * 32768).astype(np.int16)

        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())

        print("\nRunning end-to-end pipeline (audio → text → translation)...")

        times = []
        breakdown = []

        for i in range(5):
            timings = {}

            # Transcription
            start = time.time()
            segments, info = whisper.transcribe(temp_file.name)
            transcription = " ".join([seg.text for seg in segments])
            timings['transcription'] = time.time() - start

            # Language detection (already done)
            timings['detection'] = 0  # Included in transcription

            # Translation
            if transcription.strip():
                start = time.time()
                translation = translator.translate(
                    transcription,
                    source_lang="eng_Latn",
                    target_lang="spa_Latn"
                )
                timings['translation'] = time.time() - start
            else:
                timings['translation'] = 0

            total = sum(timings.values())
            times.append(total)
            breakdown.append(timings)

        os.unlink(temp_file.name)

        avg_total = np.mean(times)
        avg_transcription = np.mean([b['transcription'] for b in breakdown])
        avg_translation = np.mean([b['translation'] for b in breakdown])

        print(f"\nResults (averaged over 5 runs):")
        print(f"  Transcription: {avg_transcription:.3f}s ({avg_transcription/avg_total*100:.1f}%)")
        print(f"  Translation:   {avg_translation:.3f}s ({avg_translation/avg_total*100:.1f}%)")
        print(f"  Total:         {avg_total:.3f}s")
        print(f"\nLatency breakdown:")
        print(f"  Audio capture:      0.300s (simulated)")
        print(f"  VAD processing:     0.010s (simulated)")
        print(f"  Network transport:  0.050s (simulated)")
        print(f"  Transcription:      {avg_transcription:.3f}s")
        print(f"  Translation:        {avg_translation:.3f}s")
        print(f"  Network return:     0.050s (simulated)")
        print(f"  ─────────────────────────────")
        print(f"  Total end-to-end:   {avg_total + 0.410:.3f}s")

        self.results['pipeline'] = {
            "total": avg_total,
            "transcription": avg_transcription,
            "translation": avg_translation,
            "with_overhead": avg_total + 0.410
        }

        return self.results['pipeline']

    def benchmark_throughput(self):
        """Benchmark maximum throughput"""
        print("\n" + "="*60)
        print("BENCHMARK 4: Maximum Throughput")
        print("="*60)

        from nllb_ct2_fixed import NLLBTranslatorCT2

        translator = NLLBTranslatorCT2(device="cpu", compute_type="int8")
        translator.load_model()

        # Test sentences
        sentences = [
            "Hello, how are you?",
            "The weather is beautiful today.",
            "I love programming in Python.",
            "Artificial intelligence is amazing.",
            "Let's go to the park this afternoon."
        ] * 10  # 50 sentences total

        print(f"\nTranslating {len(sentences)} sentences...")

        start = time.time()
        for sentence in sentences:
            translator.translate(sentence, "eng_Latn", "spa_Latn")
        elapsed = time.time() - start

        throughput = len(sentences) / elapsed * 60  # sentences per minute

        print(f"\nResults:")
        print(f"  Time:       {elapsed:.1f}s")
        print(f"  Throughput: {throughput:.1f} sentences/minute")
        print(f"  Per sentence: {elapsed/len(sentences):.3f}s")

        self.results['throughput'] = {
            "sentences": len(sentences),
            "time": elapsed,
            "spm": throughput
        }

        return self.results['throughput']

    def benchmark_memory_usage(self):
        """Benchmark memory usage"""
        print("\n" + "="*60)
        print("BENCHMARK 5: Memory Usage")
        print("="*60)

        mem_baseline = self.get_memory_usage()
        print(f"\nBaseline memory: {mem_baseline:.1f} MB")

        from faster_whisper import WhisperModel
        from nllb_ct2_fixed import NLLBTranslatorCT2

        # Load Whisper
        print("\nLoading Whisper...")
        mem_before = self.get_memory_usage()
        whisper = WhisperModel("medium", device="cpu", compute_type="int8")
        mem_after = self.get_memory_usage()
        mem_whisper = mem_after - mem_before
        print(f"  Whisper memory: {mem_whisper:.1f} MB")

        # Load NLLB
        print("\nLoading NLLB...")
        mem_before = self.get_memory_usage()
        translator = NLLBTranslatorCT2(device="cpu", compute_type="int8")
        translator.load_model()
        mem_after = self.get_memory_usage()
        mem_nllb = mem_after - mem_before
        print(f"  NLLB memory:    {mem_nllb:.1f} MB")

        mem_total = self.get_memory_usage()
        print(f"\nTotal memory usage: {mem_total:.1f} MB")
        print(f"  Python baseline:  {mem_baseline:.1f} MB")
        print(f"  Whisper:          {mem_whisper:.1f} MB")
        print(f"  NLLB:             {mem_nllb:.1f} MB")
        print(f"  Other:            {mem_total - mem_baseline - mem_whisper - mem_nllb:.1f} MB")

        self.results['memory'] = {
            "baseline": mem_baseline,
            "whisper": mem_whisper,
            "nllb": mem_nllb,
            "total": mem_total
        }

        return self.results['memory']

    def benchmark_cpu_usage(self):
        """Benchmark CPU usage during inference"""
        print("\n" + "="*60)
        print("BENCHMARK 6: CPU Usage")
        print("="*60)

        from nllb_ct2_fixed import NLLBTranslatorCT2
        import threading

        translator = NLLBTranslatorCT2(device="cpu", compute_type="int8")
        translator.load_model()

        cpu_samples = []
        stop_monitoring = False

        def monitor_cpu():
            while not stop_monitoring:
                cpu_samples.append(psutil.cpu_percent(interval=0.1))

        # Start monitoring
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()

        # Run translations
        print("\nRunning translations while monitoring CPU...")
        text = "The quick brown fox jumps over the lazy dog."
        for _ in range(20):
            translator.translate(text, "eng_Latn", "spa_Latn")

        # Stop monitoring
        stop_monitoring = True
        monitor_thread.join()

        avg_cpu = np.mean(cpu_samples)
        max_cpu = np.max(cpu_samples)

        print(f"\nCPU Usage:")
        print(f"  Average: {avg_cpu:.1f}%")
        print(f"  Peak:    {max_cpu:.1f}%")
        print(f"  Cores:   {psutil.cpu_count()}")
        print(f"  Per-core: {avg_cpu/psutil.cpu_count():.1f}%")

        self.results['cpu'] = {
            "average": avg_cpu,
            "peak": max_cpu,
            "cores": psutil.cpu_count()
        }

        return self.results['cpu']

    def generate_report(self):
        """Generate comprehensive benchmark report"""
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY REPORT")
        print("="*60)

        print("\n📊 NLLB Translation Performance")
        print("─" * 40)
        if 'nllb' in self.results:
            for item in self.results['nllb']:
                print(f"{item['name']:12} {item['avg_time']:.3f}s  ({item['wps']:.1f} words/sec)")

        print("\n🎤 Whisper Transcription Performance")
        print("─" * 40)
        if 'whisper' in self.results:
            for item in self.results['whisper']:
                rtf_label = "faster" if item['rtf'] < 1 else "slower"
                print(f"{item['duration']}s audio: {item['avg_time']:.3f}s  (RTF: {item['rtf']:.2f}x {rtf_label})")

        print("\n🔄 End-to-End Pipeline")
        print("─" * 40)
        if 'pipeline' in self.results:
            p = self.results['pipeline']
            print(f"Transcription:  {p['transcription']:.3f}s")
            print(f"Translation:    {p['translation']:.3f}s")
            print(f"Total latency:  {p['with_overhead']:.3f}s")

        print("\n⚡ Throughput")
        print("─" * 40)
        if 'throughput' in self.results:
            t = self.results['throughput']
            print(f"Sentences/min:  {t['spm']:.1f}")
            print(f"Per sentence:   {t['time']/t['sentences']:.3f}s")

        print("\n💾 Memory Usage")
        print("─" * 40)
        if 'memory' in self.results:
            m = self.results['memory']
            print(f"Whisper:        {m['whisper']:.1f} MB")
            print(f"NLLB:           {m['nllb']:.1f} MB")
            print(f"Total:          {m['total']:.1f} MB")

        print("\n🖥️  CPU Usage")
        print("─" * 40)
        if 'cpu' in self.results:
            c = self.results['cpu']
            print(f"Average:        {c['average']:.1f}%")
            print(f"Peak:           {c['peak']:.1f}%")
            print(f"Cores:          {c['cores']}")

        print("\n" + "="*60)
        print("PERFORMANCE GRADE")
        print("="*60)

        # Calculate grade
        if 'pipeline' in self.results and 'throughput' in self.results:
            latency = self.results['pipeline']['with_overhead']
            throughput = self.results['throughput']['spm']

            grade = "A+"
            if latency > 3.0: grade = "A"
            if latency > 4.0: grade = "B+"
            if latency > 5.0: grade = "B"
            if throughput < 15: grade = "B"
            if throughput < 10: grade = "C"

            print(f"\nOverall Grade: {grade}")
            print(f"  Latency:    {latency:.2f}s  {'✅' if latency < 3 else '⚠️'}")
            print(f"  Throughput: {throughput:.1f}/min  {'✅' if throughput > 15 else '⚠️'}")

        # Save results to JSON
        with open('benchmark_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📁 Results saved to: benchmark_results.json")
        print("="*60)


def main():
    """Run complete benchmark suite"""
    print("="*60)
    print("BabbleFish Stack Benchmark Suite")
    print("="*60)
    print("\nThis will test:")
    print("  1. NLLB Translation speed")
    print("  2. Whisper Transcription speed")
    print("  3. End-to-end pipeline latency")
    print("  4. Maximum throughput")
    print("  5. Memory usage")
    print("  6. CPU utilization")
    print("\nEstimated time: 3-5 minutes")
    print("="*60)

    import sys
    if sys.stdin.isatty():
        input("\nPress Enter to start benchmarking...")
    else:
        print("\nStarting benchmark...")

    suite = BenchmarkSuite()

    try:
        suite.benchmark_nllb_translation()
        suite.benchmark_whisper_transcription()
        suite.benchmark_end_to_end_pipeline()
        suite.benchmark_throughput()
        suite.benchmark_memory_usage()
        suite.benchmark_cpu_usage()
        suite.generate_report()

    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
        suite.generate_report()
    except Exception as e:
        print(f"\n\nError during benchmark: {e}")
        import traceback
        traceback.print_exc()
        suite.generate_report()


if __name__ == "__main__":
    main()

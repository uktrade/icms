set -e

case "$1" in
  "gmp")
    echo "Generating GMP benchmark PDFs."
    ./run-tests.sh web/tests/utils/pdf/test_visual_regression/generate_benchmark_pdfs/export.py::TestGenerateGmpLicenceBenchmarkPDF
    ;;
  "com")
    echo "Generating COM benchmark PDFs."
    ./run-tests.sh web/tests/utils/pdf/test_visual_regression/generate_benchmark_pdfs/export.py::TestGenerateComLicenceBenchmarkPDF
    ;;
  "cfs")
    echo "Generating CFS benchmark PDFs."
    ./run-tests.sh web/tests/utils/pdf/test_visual_regression/generate_benchmark_pdfs/export.py::TestGenerateCfsLicenceBenchmarkPDF
    ;;
  "oil")
    echo "Generating OIL benchmark PDFs."
    ./run-tests.sh web/tests/utils/pdf/test_visual_regression/generate_benchmark_pdfs/import.py::TestGenerateOilLicenceBenchmarkPDF
    ;;
  "sil")
    echo "Generating SIL benchmark PDFs."
    ./run-tests.sh web/tests/utils/pdf/test_visual_regression/generate_benchmark_pdfs/import.py::TestGenerateSilLicenceBenchmarkPDF
    ;;
  "dfl")
    echo "Generating DFL benchmark PDFs."
    ./run-tests.sh web/tests/utils/pdf/test_visual_regression/generate_benchmark_pdfs/import.py::TestGenerateDflLicenceBenchmarkPDF
    ;;
  "sanctions")
    echo "Generating Sanctions benchmark PDFs."
    ./run-tests.sh web/tests/utils/pdf/test_visual_regression/generate_benchmark_pdfs/import.py::TestGenerateSanctionsLicenceBenchmarkPDF
    ;;
  "cfs-cover-letter")
    echo "Generating CFS Cover letter benchmark PDFs."
    ./run-tests.sh web/tests/utils/pdf/test_visual_regression/generate_benchmark_pdfs/import.py::TestGenerateCoverLetterBenchmarkPDF
    ;;
  *)
    echo "Generating all benchmark PDFs."
    ./run-tests.sh  \
		web/tests/utils/pdf/test_visual_regression/generate_benchmark_pdfs/export.py \
		web/tests/utils/pdf/test_visual_regression/generate_benchmark_pdfs/import.py
    ;;
esac

#!/bin/sh
cd $(dirname $0)/..

sh scripts/copy_test_data.sh
sh pytest --cov --cov-report=html:coverage_report

#!/bin/bash

MIN_PYLINT_RATING=${1:-7}

DIR=$(dirname "${BASH_SOURCE[0]}")

echo 'Assessing code quality with pylint ...'
pylint --rcfile="$DIR/pylintrc" "$DIR/$PROJECT" >pylint_results || true

# Check if pylint rating is good enough.
ACTUAL_PYLINT_RATING=$(grep -Po '(?<=Your code has been rated at )[^/]+(?=/10)' pylint_results)
echo "Minimal acceptable pylint rating is ${MIN_PYLINT_RATING}."
echo "Actual pylint rating is ${ACTUAL_PYLINT_RATING}."

if [ -z "$ACTUAL_PYLINT_RATING" ]; then
    echo "Pylint error: $(cat pylint_results)"
else
    python -c "import sys; sys.exit(0) if $ACTUAL_PYLINT_RATING >= $MIN_PYLINT_RATING else sys.exit(1)"
fi

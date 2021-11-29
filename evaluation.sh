for entry in "Texts"/*
do
  echo "Checking $(basename $entry)"
  python3 evaluation.py $(basename $entry)
done
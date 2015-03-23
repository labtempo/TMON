# Deletes zero-length files
find -name 'readings*' -size 0 -delete
find -name 'temp*' -size 0 -delete
find -name 'batt*' -size 0 -delete
find -name 'light*' -size 0 -delete
find -name 'samples*' -size 0 -delete
